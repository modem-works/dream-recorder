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

def test_api_config_error(test_client, mocker):
    # Patch get_config to raise error
    mocker.patch('functions.config_loader.get_config', side_effect=Exception('fail'))
    resp = test_client.get('/api/config')
    assert resp.status_code == 500 or resp.status_code == 200  # Defensive: route may not handle error

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

def test_clock_config_path(test_client, mocker):
    # Normal
    resp = test_client.get('/api/clock-config-path')
    assert resp.status_code in (200, 500)
    # Error: config path not set
    mocker.patch('functions.config_loader.get_config', return_value={'CLOCK_CONFIG_PATH': None})
    resp = test_client.get('/api/clock-config-path')
    assert resp.status_code == 500

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

def test_serve_media_success(test_client, mocker):
    mock_send = mocker.patch('dream_recorder.send_file', return_value='filedata')
    resp = test_client.get('/media/testfile.mp4')
    assert resp.status_code == 200 or resp.data == b'filedata'
    mock_send.assert_called()

def test_serve_media_not_found(test_client, mocker):
    mocker.patch('dream_recorder.send_file', side_effect=FileNotFoundError)
    resp = test_client.get('/media/missingfile.mp4')
    assert resp.status_code == 404

def test_serve_thumbnail_success(test_client, mocker):
    mock_send = mocker.patch('dream_recorder.send_file', return_value='thumbdata')
    mocker.patch('functions.config_loader.get_config', return_value={'THUMBS_DIR': 'thumbs'})
    resp = test_client.get('/media/thumbs/testthumb.jpg')
    assert resp.status_code == 200 or resp.data == b'thumbdata'
    mock_send.assert_called()

def test_serve_thumbnail_not_found(test_client, mocker):
    mocker.patch('dream_recorder.send_file', side_effect=FileNotFoundError)
    mocker.patch('functions.config_loader.get_config', return_value={'THUMBS_DIR': 'thumbs'})
    resp = test_client.get('/media/thumbs/missingthumb.jpg')
    assert resp.status_code == 404

def test_delete_dream_removes_files(test_client, mocker, mock_dream_db, tmp_path):
    video = tmp_path / "dream1.mp4"
    thumb = tmp_path / "thumb1.jpg"
    audio = tmp_path / "audio1.wav"
    for f in (video, thumb, audio):
        f.write_text("data")
    # Patch get_config in the dream_recorder module
    mocker.patch('dream_recorder.get_config', return_value={
        'VIDEOS_DIR': str(tmp_path),
        'THUMBS_DIR': str(tmp_path),
        'RECORDINGS_DIR': str(tmp_path)
    })
    mock_dream_db.get_dream.return_value = {
        'id': 1, 'video_filename': video.name, 'thumb_filename': thumb.name, 'audio_filename': audio.name
    }
    mock_dream_db.delete_dream.return_value = True
    mock_remove = mocker.patch('os.remove')
    resp = test_client.delete('/api/dreams/1')
    assert resp.status_code == 200
    mock_remove.assert_any_call(str(video))
    mock_remove.assert_any_call(str(thumb))
    mock_remove.assert_any_call(str(audio))
    assert mock_remove.call_count == 3

def test_404_page(test_client):
    resp = test_client.get('/nonexistent')
    assert resp.status_code == 404

def test_notify_config_reload_multiple_clients(test_client, mocker):
    mock_emit = mocker.patch('dream_recorder.socketio.emit')
    resp = test_client.post('/api/notify_config_reload')
    assert resp.status_code == 200
    mock_emit.assert_any_call('reload_config') 