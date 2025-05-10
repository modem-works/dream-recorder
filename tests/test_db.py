import pytest
import tempfile
import os
from functions.dream_db import DreamDB, DreamData

def test_get_all_dreams(mock_dream_db):
    mock_dream_db.get_all_dreams.return_value = [
        {'id': 1, 'video_filename': 'dream1.mp4'},
        {'id': 2, 'video_filename': 'dream2.mp4'}
    ]
    dreams = mock_dream_db.get_all_dreams()
    assert len(dreams) == 2
    assert dreams[0]['video_filename'] == 'dream1.mp4'

def test_get_all_dreams_empty(mock_dream_db):
    mock_dream_db.get_all_dreams.return_value = []
    dreams = mock_dream_db.get_all_dreams()
    assert dreams == []

def test_get_dream_not_found(mock_dream_db):
    mock_dream_db.get_dream.return_value = None
    dream = mock_dream_db.get_dream(999)
    assert dream is None

def test_delete_dream(mock_dream_db):
    mock_dream_db.delete_dream.return_value = True
    result = mock_dream_db.delete_dream(1)
    assert result is True
    mock_dream_db.delete_dream.assert_called_with(1)

def test_delete_dream_not_found(mock_dream_db):
    mock_dream_db.delete_dream.return_value = False
    result = mock_dream_db.delete_dream(999)
    assert result is False

@pytest.fixture
def temp_db_path():
    fd, path = tempfile.mkstemp(suffix='.sqlite3')
    os.close(fd)
    yield path
    os.remove(path)

@pytest.fixture
def dream_db(temp_db_path):
    return DreamDB(db_path=temp_db_path)

def test_save_and_get_dream(dream_db):
    data = DreamData(
        user_prompt='u', generated_prompt='g', audio_filename='a', video_filename='v', thumb_filename='t', status='completed'
    ).model_dump()
    dream_id = dream_db.save_dream(data)
    dream = dream_db.get_dream(dream_id)
    assert dream['user_prompt'] == 'u'
    assert dream['generated_prompt'] == 'g'
    assert dream['audio_filename'] == 'a'
    assert dream['video_filename'] == 'v'
    assert dream['thumb_filename'] == 't'
    assert dream['status'] == 'completed'

def test_save_dream_missing_field_raises(dream_db):
    data = {'user_prompt': 'u', 'generated_prompt': 'g', 'audio_filename': 'a'}  # missing video_filename
    with pytest.raises(ValueError):
        dream_db.save_dream(data)

def test_update_dream_and_error_handling(dream_db):
    data = DreamData(
        user_prompt='u', generated_prompt='g', audio_filename='a', video_filename='v'
    ).model_dump()
    dream_id = dream_db.save_dream(data)
    # Update status
    assert dream_db.update_dream(dream_id, {'status': 'updated'})
    dream = dream_db.get_dream(dream_id)
    assert dream['status'] == 'updated'
    # Update with empty dict does nothing
    assert dream_db.update_dream(dream_id, {}) is None
    # Update with invalid field triggers sqlite3.Error
    with pytest.raises(Exception):
        dream_db.update_dream(dream_id, {'not_a_column': 'x'})

def test_row_to_dict(dream_db):
    data = DreamData(
        user_prompt='u', generated_prompt='g', audio_filename='a', video_filename='v'
    ).model_dump()
    dream_id = dream_db.save_dream(data)
    dream = dream_db.get_dream(dream_id)
    # _row_to_dict is used internally, but we can check the output is a dict
    assert isinstance(dream, dict) 