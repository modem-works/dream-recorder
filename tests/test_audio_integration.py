import pytest
from unittest import mock
from functions import audio

@pytest.fixture
def mock_config(monkeypatch):
    monkeypatch.setattr(audio, 'get_config', lambda: {
        'AUDIO_CHANNELS': 1,
        'AUDIO_SAMPLE_WIDTH': 2,
        'AUDIO_FRAME_RATE': 44100,
        'RECORDINGS_DIR': '/tmp',
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

def test_generate_video_prompt_success(monkeypatch, mock_config, mock_logger):
    fake_response = mock.Mock()
    fake_response.choices = [mock.Mock(message=mock.Mock(content='Generated prompt'))]
    monkeypatch.setattr(audio.client.chat.completions, 'create', lambda **kwargs: fake_response)
    result = audio.generate_video_prompt('transcript', luma_extend=False, logger=mock_logger)
    assert result == 'Generated prompt'

def test_generate_video_prompt_error(monkeypatch, mock_config, mock_logger):
    def raise_exc(**kwargs): raise Exception('gpt fail')
    monkeypatch.setattr(audio.client.chat.completions, 'create', raise_exc)
    result = audio.generate_video_prompt('transcript', luma_extend=False, logger=mock_logger)
    assert result is None
    mock_logger.error.assert_called()

def test_process_audio_success(monkeypatch, mock_config, mock_logger):
    # Patch save_wav_file
    monkeypatch.setattr(audio, 'save_wav_file', lambda *a, **k: 'file.wav')
    # Patch OpenAI Whisper
    fake_transcription = mock.Mock(text='hello world')
    fake_audio = mock.Mock()
    monkeypatch.setattr(audio.client.audio.transcriptions, 'create', lambda **kwargs: fake_transcription)
    # Patch generate_video_prompt
    monkeypatch.setattr(audio, 'generate_video_prompt', lambda *a, **k: 'video prompt')
    # Patch generate_video
    monkeypatch.setattr(audio, 'generate_video', lambda *a, **k: ('video.mp4', 'thumb.png'))
    # Patch dream_db
    fake_db = mock.Mock()
    # Patch socketio
    fake_socketio = mock.Mock()
    recording_state = {}
    audio_chunks = [b'audio']
    audio.process_audio('sid', fake_socketio, fake_db, recording_state, audio_chunks, logger=mock_logger)
    assert recording_state['transcription'] == 'hello world'
    assert recording_state['video_prompt'] == 'video prompt'
    assert recording_state['status'] == 'complete'
    assert recording_state['video_url'].endswith('video.mp4')
    fake_socketio.emit.assert_any_call('transcription_update', {'text': 'hello world'}, room='sid')
    fake_socketio.emit.assert_any_call('video_prompt_update', {'text': 'video prompt'}, room='sid')
    fake_socketio.emit.assert_any_call('video_ready', {'url': recording_state['video_url']}, room='sid')
    fake_db.save_dream.assert_called()
    mock_logger.info.assert_called()

def test_process_audio_error(monkeypatch, mock_config, mock_logger):
    # Patch save_wav_file to raise
    def raise_exc(*a, **k): raise Exception('fail')
    monkeypatch.setattr(audio, 'save_wav_file', raise_exc)
    fake_db = mock.Mock()
    fake_socketio = mock.Mock()
    recording_state = {}
    audio_chunks = [b'audio']
    audio.process_audio('sid', fake_socketio, fake_db, recording_state, audio_chunks, logger=mock_logger)
    assert recording_state['status'] == 'error'
    fake_socketio.emit.assert_any_call('error', {'message': 'fail'})
    mock_logger.error.assert_called() 