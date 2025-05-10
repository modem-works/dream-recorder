import pytest

def test_get_all_dreams(mock_dream_db):
    mock_dream_db.get_all_dreams.return_value = [
        {'id': 1, 'video_filename': 'dream1.mp4'},
        {'id': 2, 'video_filename': 'dream2.mp4'}
    ]
    dreams = mock_dream_db.get_all_dreams()
    assert len(dreams) == 2
    assert dreams[0]['video_filename'] == 'dream1.mp4'

def test_delete_dream(mock_dream_db):
    mock_dream_db.delete_dream.return_value = True
    result = mock_dream_db.delete_dream(1)
    assert result is True
    mock_dream_db.delete_dream.assert_called_with(1) 