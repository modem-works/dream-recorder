import pytest
import sys
import types

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