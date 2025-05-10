import pytest
import time

def test_connect(socketio_client):
    received = socketio_client.get_received()
    assert any(x['name'] == 'state_update' for x in received)

def test_start_and_stop_recording(socketio_client):
    socketio_client.emit('start_recording')
    time.sleep(0.1)
    received = socketio_client.get_received()
    assert any(x['name'] == 'state_update' for x in received)
    socketio_client.emit('stop_recording')
    time.sleep(0.1)
    received = socketio_client.get_received()
    assert any(x['name'] == 'state_update' for x in received)

def test_show_previous_dream(socketio_client, mock_dream_db):
    # Mock at least one dream
    mock_dream_db.get_all_dreams.return_value = [
        {'video_filename': 'test.mp4'}
    ]
    socketio_client.emit('show_previous_dream')
    time.sleep(0.1)
    received = socketio_client.get_received()
    assert any(x['name'] == 'play_video' for x in received) 