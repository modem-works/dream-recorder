import pytest
import time

def test_connect(socketio_client):
    received = socketio_client.get_received()
    assert any(x['name'] == 'state_update' for x in received)

def test_start_and_stop_recording(socketio_client, mocker):
    # Start recording
    socketio_client.emit('start_recording')
    time.sleep(0.1)
    received = socketio_client.get_received()
    assert any(x['name'] == 'state_update' and x['args'][0]['status'] == 'recording' for x in received)
    # Stream audio chunk
    socketio_client.emit('stream_recording', {'data': [1, 2, 3, 4]})
    # Patch process_audio to simulate immediate processing
    mock_process = mocker.patch('dream_recorder.process_audio', autospec=True)
    socketio_client.emit('stop_recording')
    time.sleep(0.1)
    received = socketio_client.get_received()
    assert any(x['name'] == 'state_update' and x['args'][0]['status'] == 'processing' for x in received)
    mock_process.assert_called_once()

def test_playback_flow(socketio_client, mock_dream_db):
    # Mock two dreams
    mock_dream_db.get_all_dreams.return_value = [
        {'video_filename': 'dream1.mp4'},
        {'video_filename': 'dream2.mp4'}
    ]
    # Play latest dream
    socketio_client.emit('show_previous_dream')
    time.sleep(0.1)
    received = socketio_client.get_received()
    assert any(x['name'] == 'play_video' and 'dream1.mp4' in x['args'][0]['video_url'] for x in received)
    # Play previous dream (should wrap around)
    socketio_client.emit('show_previous_dream')
    time.sleep(0.1)
    received = socketio_client.get_received()
    assert any(x['name'] == 'play_video' and 'dream2.mp4' in x['args'][0]['video_url'] for x in received)

def test_no_dreams_playback(socketio_client, mock_dream_db):
    mock_dream_db.get_all_dreams.return_value = []
    socketio_client.emit('show_previous_dream')
    time.sleep(0.1)
    received = socketio_client.get_received()
    # Should emit error or not emit play_video
    assert not any(x['name'] == 'play_video' for x in received)

def test_multiple_clients_receive_state(socketio_client, mocker):
    from dream_recorder import app, socketio as sio
    client2 = sio.test_client(app)
    try:
        socketio_client.emit('start_recording')
        time.sleep(0.1)
        received1 = socketio_client.get_received()
        received2 = client2.get_received()
        assert any(x['name'] == 'state_update' for x in received1)
        assert any(x['name'] == 'state_update' for x in received2)
    finally:
        client2.disconnect()

def test_process_audio_external_api_failure(socketio_client, mocker):
    def fake_process_audio(*args, **kwargs):
        socketio = args[1]
        socketio.emit('error', {'message': 'External API failed'})
    mocker.patch('dream_recorder.process_audio', side_effect=fake_process_audio)
    socketio_client.emit('start_recording')
    socketio_client.emit('stop_recording')
    time.sleep(0.1)
    received = socketio_client.get_received()
    assert any(x['name'] == 'error' and 'External API failed' in x['args'][0]['message'] for x in received)

def test_large_audio_stream(socketio_client):
    socketio_client.emit('start_recording')
    for _ in range(100):
        socketio_client.emit('stream_recording', {'data': [1]*1024})
    socketio_client.emit('stop_recording')
    # No assertion, just ensure no crash

def test_state_reset_after_recording(socketio_client, mocker):
    mocker.patch('dream_recorder.process_audio', autospec=True)
    socketio_client.emit('start_recording')
    socketio_client.emit('stop_recording')
    # Start again, should reset state
    socketio_client.emit('start_recording')
    received = socketio_client.get_received()
    assert any(x['name'] == 'state_update' and x['args'][0]['status'] == 'recording' for x in received) 