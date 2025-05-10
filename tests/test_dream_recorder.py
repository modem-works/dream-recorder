import pytest
import sys
import types
import os
import subprocess

def test_sample_dreams_initialization_success_and_failure(monkeypatch):
    # Patch os.path.exists to always return False (simulate missing DB)
    monkeypatch.setattr('os.path.exists', lambda path: False)
    # Patch subprocess.run to simulate success and failure
    class Result:
        def __init__(self, returncode, stderr=''):
            self.returncode = returncode
            self.stderr = stderr
    calls = []
    def fake_run(cmd, capture_output, text):
        calls.append(cmd)
        if len(calls) == 1:
            return Result(0)
        else:
            return Result(1, 'fail')
    monkeypatch.setattr('subprocess.run', fake_run)
    # Patch print to capture output
    printed = []
    monkeypatch.setattr('builtins.print', lambda *a, **kw: printed.append(a))
    # Patch os.path.dirname to return current dir
    monkeypatch.setattr('os.path.dirname', lambda path: '.')
    # Patch __file__
    monkeypatch.setattr(sys.modules['dream_recorder'], '__file__', 'dream_recorder.py')
    # Import and run the block
    import importlib
    import dream_recorder
    importlib.reload(dream_recorder)
    # Call the function again to simulate failure
    dream_recorder.init_sample_dreams_if_missing()
    # The first call should print success, the second should print warning
    assert any('Sample dreams initialized.' in str(x) for x in printed)
    assert any('Failed to initialize sample dreams.' in str(x) for x in printed)

def test_sample_dreams_initialization_exception(monkeypatch):
    import dream_recorder
    # Patch subprocess.run to raise an exception
    monkeypatch.setattr('subprocess.run', lambda *a, **kw: (_ for _ in ()).throw(Exception('fail')))
    # Patch print to capture output
    printed = []
    monkeypatch.setattr('builtins.print', lambda *a, **kw: printed.append(a))
    # Call the function to trigger the exception branch
    dream_recorder.init_sample_dreams_if_missing()
    assert any('Exception while initializing sample dreams' in str(x) for x in printed)

def test_handle_audio_data_error(monkeypatch, mocker):
    import dream_recorder
    # Patch logger
    logs = []
    class FakeLogger:
        def error(self, msg): logs.append(msg)
        def info(self, msg): pass
        def warning(self, msg): pass
    monkeypatch.setattr(dream_recorder, 'logger', FakeLogger())
    # Patch emit to record calls
    emitted = []
    monkeypatch.setattr(dream_recorder, 'emit', lambda name, data=None: emitted.append((name, data)))
    # Simulate error in bytes(data['data'])
    dream_recorder.recording_state['is_recording'] = True
    dream_recorder.handle_audio_data({'data': object()})
    assert any('Error handling audio data' in msg for msg in logs)
    assert any(name == 'error' for name, _ in emitted)

def test_handle_stop_recording_error(monkeypatch, mocker):
    import dream_recorder
    # Patch logger
    logs = []
    class FakeLogger:
        def warning(self, msg): logs.append(msg)
        def info(self, msg): pass
        def error(self, msg): pass
    monkeypatch.setattr(dream_recorder, 'logger', FakeLogger())
    # Set not recording
    dream_recorder.recording_state['is_recording'] = False
    dream_recorder.handle_stop_recording()
    assert any('Stop recording event received, but not currently recording.' in msg for msg in logs)

def test_handle_show_previous_dream_error(monkeypatch, mocker):
    import dream_recorder
    # Patch dream_db.get_all_dreams to raise
    monkeypatch.setattr(dream_recorder.dream_db, 'get_all_dreams', lambda: (_ for _ in ()).throw(Exception('fail')))
    # Patch logger
    logs = []
    class FakeLogger:
        def error(self, msg): logs.append(msg)
        def info(self, msg): pass
        def warning(self, msg): pass
    monkeypatch.setattr(dream_recorder, 'logger', FakeLogger())
    # Patch socketio.emit to record calls
    emitted = []
    monkeypatch.setattr(dream_recorder.socketio, 'emit', lambda name, data=None: emitted.append((name, data)))
    dream_recorder.handle_show_previous_dream()
    assert any('Error in socket handle_show_previous_dream' in msg for msg in logs)
    assert any(name == 'error' for name, _ in emitted)

def test_handle_show_previous_dream_no_dream(monkeypatch, mocker):
    import dream_recorder
    # Patch dream_db.get_all_dreams to return an empty list
    monkeypatch.setattr(dream_recorder.dream_db, 'get_all_dreams', lambda: [])
    # Patch logger to record warnings
    logs = []
    class FakeLogger:
        def warning(self, msg): logs.append(msg)
        def info(self, msg): pass
        def error(self, msg): pass
    monkeypatch.setattr(dream_recorder, 'logger', FakeLogger())
    # Set video_playback_state to simulate playing
    dream_recorder.video_playback_state['is_playing'] = True
    dream_recorder.video_playback_state['current_index'] = 0
    dream_recorder.handle_show_previous_dream()
    assert any('No dreams found to cycle through.' in msg for msg in logs)

def test_delete_dream_file_deletion_error(test_client, mocker, mock_dream_db):
    # Simulate dream exists and delete_dream returns True
    mock_dream_db.get_dream.return_value = {
        'id': 1, 'video_filename': 'dream1.mp4', 'thumb_filename': 'thumb1.jpg', 'audio_filename': 'audio1.wav'
    }
    mock_dream_db.delete_dream.return_value = True
    # Patch os.path.exists to True so it tries to remove
    mocker.patch('os.path.exists', return_value=True)
    # Patch os.remove to raise exception
    mocker.patch('os.remove', side_effect=Exception('fail'))
    # Patch get_config
    mocker.patch('dream_recorder.get_config', return_value={
        'VIDEOS_DIR': '.', 'THUMBS_DIR': '.', 'RECORDINGS_DIR': '.'
    })
    # Patch logger
    mock_logger = mocker.Mock()
    mocker.patch('dream_recorder.logger', mock_logger)
    resp = test_client.delete('/api/dreams/1')
    # Should still succeed, but logger.error should be called
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
    assert mock_logger.error.called

def test_api_gpio_single_tap_error(test_client, mocker):
    mocker.patch('dream_recorder.socketio.emit', side_effect=Exception('fail'))
    resp = test_client.post('/api/gpio_single_tap')
    data = resp.get_json()
    assert resp.status_code == 500
    assert data['status'] == 'error'
    assert 'fail' in data['message']

def test_api_gpio_double_tap_error(test_client, mocker):
    mocker.patch('dream_recorder.socketio.emit', side_effect=Exception('fail'))
    resp = test_client.post('/api/gpio_double_tap')
    data = resp.get_json()
    assert resp.status_code == 500
    assert data['status'] == 'error'
    assert 'fail' in data['message']

def test_api_delete_dream_error(test_client, mocker):
    mocker.patch('dream_recorder.dream_db.get_dream', side_effect=Exception('fail'))
    resp = test_client.delete('/api/dreams/1')
    data = resp.get_json()
    assert resp.status_code == 500
    assert data['success'] is False
    assert 'fail' in data['message']

def test_serve_media_error(test_client, mocker):
    mocker.patch('dream_recorder.send_file', side_effect=FileNotFoundError)
    resp = test_client.get('/media/missingfile.mp4')
    assert resp.status_code == 404
    assert b'File not found' in resp.data

def test_serve_thumbnail_error(test_client, mocker):
    mocker.patch('dream_recorder.send_file', side_effect=FileNotFoundError)
    mocker.patch('functions.config_loader.get_config', return_value={'THUMBS_DIR': 'thumbs'})
    resp = test_client.get('/media/thumbs/missingthumb.jpg')
    assert resp.status_code == 404
    assert b'Thumbnail not found' in resp.data 