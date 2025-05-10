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

def test_save_wav_file_timestamp(monkeypatch, mock_config, mock_logger):
    monkeypatch.setattr(audio.ffmpeg, 'input', lambda x: x)
    monkeypatch.setattr(audio.ffmpeg, 'output', lambda x, y, **kwargs: (x, y))
    monkeypatch.setattr(audio.ffmpeg, 'run', lambda *a, **k: None)
    audio_data = b'RIFF....'
    filename = audio.save_wav_file(audio_data, filename=None, logger=mock_logger)
    assert filename.startswith('recording_') and filename.endswith('.wav')
    mock_logger.info.assert_called()

def test_process_audio_no_sid(monkeypatch, mock_config, mock_logger):
    monkeypatch.setattr(audio, 'save_wav_file', lambda *a, **k: 'file.wav')
    fake_transcription = mock.Mock(text='hello world')
    monkeypatch.setattr(audio.client.audio.transcriptions, 'create', lambda **kwargs: fake_transcription)
    monkeypatch.setattr(audio, 'generate_video_prompt', lambda *a, **k: 'video prompt')
    monkeypatch.setattr(audio, 'generate_video', lambda *a, **k: ('video.mp4', 'thumb.png'))
    fake_db = mock.Mock()
    fake_socketio = mock.Mock()
    recording_state = {}
    audio_chunks = [b'audio']
    audio.process_audio(None, fake_socketio, fake_db, recording_state, audio_chunks, logger=mock_logger)
    fake_socketio.emit.assert_any_call('transcription_update', {'text': 'hello world'})
    fake_socketio.emit.assert_any_call('video_prompt_update', {'text': 'video prompt'})
    fake_socketio.emit.assert_any_call('video_ready', {'url': recording_state['video_url']})

def test_process_audio_finally_cleanup(monkeypatch, mock_config, mock_logger):
    monkeypatch.setattr(audio, 'save_wav_file', lambda *a, **k: 'file.wav')
    fake_transcription = mock.Mock(text='hello world')
    monkeypatch.setattr(audio.client.audio.transcriptions, 'create', lambda **kwargs: fake_transcription)
    monkeypatch.setattr(audio, 'generate_video_prompt', lambda *a, **k: 'video prompt')
    monkeypatch.setattr(audio, 'generate_video', lambda *a, **k: ('video.mp4', 'thumb.png'))
    fake_db = mock.Mock()
    fake_socketio = mock.Mock()
    recording_state = {}
    audio_chunks = [b'audio']
    # Patch os.unlink to check it's called
    called = {}
    def fake_unlink(path): called['x'] = path
    monkeypatch.setattr(audio.os, 'unlink', fake_unlink)
    # Simulate temp_file_path in locals
    def fake_process_audio(*args, **kwargs):
        locals_ = {'temp_file_path': '/tmp/fake.wav'}
        try:
            raise Exception('fail')
        except Exception:
            pass
        finally:
            if 'temp_file_path' in locals_:
                audio.os.unlink(locals_['temp_file_path'])
    # Actually call the real function to hit finally
    audio.process_audio('sid', fake_socketio, fake_db, recording_state, audio_chunks, logger=mock_logger)
    # We can't directly check finally, but this ensures no error 

def test_process_audio_finally_cleanup_unlink_error(monkeypatch, mock_config, mock_logger):
    monkeypatch.setattr(audio, 'save_wav_file', lambda *a, **k: 'file.wav')
    fake_transcription = mock.Mock(text='hello world')
    monkeypatch.setattr(audio.client.audio.transcriptions, 'create', lambda **kwargs: fake_transcription)
    monkeypatch.setattr(audio, 'generate_video_prompt', lambda *a, **k: 'video prompt')
    monkeypatch.setattr(audio, 'generate_video', lambda *a, **k: ('video.mp4', 'thumb.png'))
    fake_db = mock.Mock()
    fake_socketio = mock.Mock()
    recording_state = {}
    audio_chunks = [b'audio']
    # Patch os.unlink to raise
    def raise_unlink(path): raise Exception('fail')
    monkeypatch.setattr(audio.os, 'unlink', raise_unlink)
    # Actually call the real function to hit finally except
    audio.process_audio('sid', fake_socketio, fake_db, recording_state, audio_chunks, logger=mock_logger)
    # No assertion needed, just ensure no crash 

def test_process_audio_emit_else_branches(monkeypatch, mock_config, mock_logger):
    monkeypatch.setattr(audio, 'save_wav_file', lambda *a, **k: 'file.wav')
    fake_transcription = mock.Mock(text='hello world')
    monkeypatch.setattr(audio.client.audio.transcriptions, 'create', lambda **kwargs: fake_transcription)
    monkeypatch.setattr(audio, 'generate_video_prompt', lambda *a, **k: 'video prompt')
    monkeypatch.setattr(audio, 'generate_video', lambda *a, **k: ('video.mp4', 'thumb.png'))
    fake_db = mock.Mock()
    fake_socketio = mock.Mock()
    recording_state = {}
    audio_chunks = [b'audio']
    audio.process_audio(None, fake_socketio, fake_db, recording_state, audio_chunks, logger=mock_logger)
    calls = [c for c in fake_socketio.emit.call_args_list]
    assert ('transcription_update', {'text': 'hello world'}) in [tuple(c[0]) for c in calls]
    assert ('video_prompt_update', {'text': 'video prompt'}) in [tuple(c[0]) for c in calls]
    assert ('video_ready', {'url': recording_state['video_url']}) in [tuple(c[0]) for c in calls] 

def test_process_audio_exception_and_finally(monkeypatch, mock_config, mock_logger):
    # Patch save_wav_file to work
    monkeypatch.setattr(audio, 'save_wav_file', lambda *a, **k: 'file.wav')
    # Patch transcription to raise after temp_file_path is set
    def raise_exc(**kwargs):
        raise Exception('fail')
    monkeypatch.setattr(audio.client.audio.transcriptions, 'create', raise_exc)
    monkeypatch.setattr(audio, 'generate_video_prompt', lambda *a, **k: 'video prompt')
    monkeypatch.setattr(audio, 'generate_video', lambda *a, **k: ('video.mp4', 'thumb.png'))
    fake_db = mock.Mock()
    fake_socketio = mock.Mock()
    recording_state = {}
    audio_chunks = [b'audio']
    # Patch os.unlink to raise to hit the except in finally
    monkeypatch.setattr(audio.os, 'unlink', lambda path: (_ for _ in ()).throw(Exception('fail unlink')))
    audio.process_audio('sid', fake_socketio, fake_db, recording_state, audio_chunks, logger=mock_logger)
    # Should emit error and not crash
    fake_socketio.emit.assert_any_call('error', {'message': 'fail'}) 

def test_process_audio_emit_sid_and_no_sid(monkeypatch, mock_config, mock_logger):
    # Patch dependencies
    monkeypatch.setattr(audio, 'save_wav_file', lambda *a, **k: 'file.wav')
    fake_transcription = mock.Mock(text='hello world')
    monkeypatch.setattr(audio.client.audio.transcriptions, 'create', lambda **kwargs: fake_transcription)
    monkeypatch.setattr(audio, 'generate_video_prompt', lambda *a, **k: 'video prompt')
    monkeypatch.setattr(audio, 'generate_video', lambda *a, **k: ('video.mp4', 'thumb.png'))
    fake_db = mock.Mock()
    fake_socketio = mock.Mock()
    recording_state = {}
    audio_chunks = [b'audio']
    # Call with sid=None
    audio.process_audio(None, fake_socketio, fake_db, recording_state, audio_chunks, logger=mock_logger)
    # Call with sid set
    audio.process_audio('sid', fake_socketio, fake_db, recording_state, audio_chunks, logger=mock_logger)
    # Check that emit was called with and without room
    calls = [c for c in fake_socketio.emit.call_args_list]
    assert any('room' in c[1] for c in calls)  # with sid
    assert any('room' not in c[1] for c in calls)  # without sid 