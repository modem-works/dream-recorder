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

def test_gpio_single_tap(test_client):
    resp = test_client.post('/api/gpio_single_tap')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'success'

def test_gpio_double_tap(test_client):
    resp = test_client.post('/api/gpio_double_tap')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'success'

def test_clock_config_path(test_client):
    resp = test_client.get('/api/clock-config-path')
    assert resp.status_code in (200, 500)  # 500 if not set

def test_notify_config_reload(test_client):
    resp = test_client.post('/api/notify_config_reload')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'reload event emitted' 