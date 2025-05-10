import pytest
from dream_recorder import app, socketio
from unittest.mock import patch, MagicMock

@pytest.fixture(scope='module')
def test_client():
    with app.test_client() as client:
        yield client

@pytest.fixture(scope='module')
def socketio_client():
    test_client = socketio.test_client(app)
    yield test_client
    test_client.disconnect()

@pytest.fixture(autouse=True)
def mock_dream_db(monkeypatch):
    mock_db = MagicMock()
    monkeypatch.setattr('dream_recorder.dream_db', mock_db)
    return mock_db 