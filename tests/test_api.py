import pytest

def test_index_page(test_client):
    resp = test_client.get('/')
    assert resp.status_code == 200
    assert b'<html' in resp.data

def test_dreams_page(test_client):
    resp = test_client.get('/dreams')
    assert resp.status_code == 200
    assert b'<html' in resp.data

def test_api_config(test_client):
    resp = test_client.get('/api/config')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'is_development' in data
    assert 'playback_duration' in data

def test_gpio_single_tap(test_client, mocker):
    mock_emit = mocker.patch('dream_recorder.socketio.emit')
    resp = test_client.post('/api/gpio_single_tap')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'success'
    mock_emit.assert_called_with('device_event', {'eventType': 'single_tap'})

def test_gpio_double_tap(test_client, mocker):
    mock_emit = mocker.patch('dream_recorder.socketio.emit')
    resp = test_client.post('/api/gpio_double_tap')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'success'
    mock_emit.assert_called_with('device_event', {'eventType': 'double_tap'})

def test_clock_config_path(test_client):
    resp = test_client.get('/api/clock-config-path')
    assert resp.status_code in (200, 500)  # 500 if not set

def test_notify_config_reload(test_client, mocker):
    mock_emit = mocker.patch('dream_recorder.socketio.emit')
    resp = test_client.post('/api/notify_config_reload')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'reload event emitted'
    mock_emit.assert_called_with('reload_config')

def test_delete_dream_success(test_client, mocker, mock_dream_db):
    mock_dream_db.get_dream.return_value = {
        'id': 1, 'video_filename': 'dream1.mp4', 'thumb_filename': 'thumb1.jpg', 'audio_filename': 'audio1.wav'
    }
    mock_dream_db.delete_dream.return_value = True
    mocker.patch('os.path.exists', return_value=True)
    mock_remove = mocker.patch('os.remove')
    resp = test_client.delete('/api/dreams/1')
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
    assert mock_remove.call_count == 3  # video, thumb, audio

def test_delete_dream_not_found(test_client, mock_dream_db):
    mock_dream_db.get_dream.return_value = None
    resp = test_client.delete('/api/dreams/999')
    assert resp.status_code == 404 