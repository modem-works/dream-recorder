import io
import os
import tempfile
import pytest
from unittest import mock
from functions import audio

@pytest.fixture
def mock_config(monkeypatch):
    monkeypatch.setattr(audio, 'get_config', lambda: {
        'AUDIO_CHANNELS': 1,
        'AUDIO_SAMPLE_WIDTH': 2,
        'AUDIO_FRAME_RATE': 44100,
        'RECORDINGS_DIR': tempfile.gettempdir(),
        'OPENAI_API_KEY': 'sk-test',
        'GPT_SYSTEM_PROMPT': 'Prompt',
        'GPT_SYSTEM_PROMPT_EXTEND': 'PromptExt',
        'GPT_MODEL': 'gpt-3.5-turbo',
        'GPT_TEMPERATURE': 0.5,
        'GPT_MAX_TOKENS': 100,
        'WHISPER_MODEL': 'whisper-1',
        'LUMA_EXTEND': '0',
    })

@pytest.fixture
def mock_logger():
    return mock.Mock()

def test_create_wav_file(mock_config):
    buf = io.BytesIO()
    wav = audio.create_wav_file(buf)
    assert wav.getnchannels() == 1
    assert wav.getsampwidth() == 2
    assert wav.getframerate() == 44100
    wav.close()

def test_save_wav_file_creates_file(monkeypatch, mock_config, mock_logger):
    # Patch ffmpeg to avoid real conversion
    monkeypatch.setattr(audio.ffmpeg, 'input', lambda x: x)
    monkeypatch.setattr(audio.ffmpeg, 'output', lambda x, y, **kwargs: (x, y))
    monkeypatch.setattr(audio.ffmpeg, 'run', lambda *a, **k: None)
    audio_data = b'RIFF....'  # fake webm data
    filename = audio.save_wav_file(audio_data, filename='test.wav', logger=mock_logger)
    assert filename.endswith('.wav')
    mock_logger.info.assert_called()

def test_save_wav_file_handles_tempfile_cleanup(monkeypatch, mock_config, mock_logger):
    # Patch ffmpeg to raise error
    monkeypatch.setattr(audio.ffmpeg, 'input', lambda x: x)
    monkeypatch.setattr(audio.ffmpeg, 'output', lambda x, y, **kwargs: (x, y))
    def raise_exc(*a, **k): raise Exception('ffmpeg fail')
    monkeypatch.setattr(audio.ffmpeg, 'run', raise_exc)
    audio_data = b'RIFF....'
    # Should raise, since save_wav_file does not suppress ffmpeg.run errors
    with pytest.raises(Exception, match='ffmpeg fail'):
        audio.save_wav_file(audio_data, filename='fail.wav', logger=mock_logger)

def test_save_wav_file_handles_os_unlink(monkeypatch, mock_config, mock_logger):
    monkeypatch.setattr(audio.ffmpeg, 'input', lambda x: x)
    monkeypatch.setattr(audio.ffmpeg, 'output', lambda x, y, **kwargs: (x, y))
    monkeypatch.setattr(audio.ffmpeg, 'run', lambda *a, **k: None)
    # Patch os.unlink to raise
    monkeypatch.setattr(os, 'unlink', lambda x: (_ for _ in ()).throw(Exception('unlink fail')))
    audio_data = b'RIFF....'
    filename = audio.save_wav_file(audio_data, filename='unlink.wav', logger=mock_logger)
    assert filename.endswith('.wav') 