import pytest
import sys
import types
import builtins
from unittest import mock

@pytest.fixture
def patch_sample_dreams(monkeypatch):
    # Patch DreamDB and DreamData
    fake_db = mock.Mock()
    monkeypatch.setattr('scripts.init_sample_dreams.DreamDB', lambda: fake_db)
    monkeypatch.setattr('scripts.init_sample_dreams.DreamData', mock.Mock(return_value=mock.Mock(model_dump=lambda: {'x': 1})))
    return fake_db

def test_copies_and_inserts(monkeypatch, patch_sample_dreams):
    # Patch os.path.exists to always return False (force copy)
    monkeypatch.setattr('os.path.exists', lambda path: False)
    # Patch shutil.copy2 to record calls
    copy_calls = []
    monkeypatch.setattr('shutil.copy2', lambda src, dst: copy_calls.append((src, dst)))
    # Patch print to capture output
    printed = []
    monkeypatch.setattr(builtins, 'print', lambda *a, **kw: printed.append(a))
    # Patch get_all_dreams to return empty (force insert)
    import scripts.init_sample_dreams as mod
    patch_sample_dreams.get_all_dreams.return_value = []
    mod.main()
    # Should copy and insert for all samples
    assert len(copy_calls) == 8  # 4 videos + 4 thumbs
    assert any('Inserted sample dream' in str(x) for x in printed)

def test_already_exists(monkeypatch, patch_sample_dreams):
    # Patch os.path.exists to always return True (no copy)
    monkeypatch.setattr('os.path.exists', lambda path: True)
    # Patch shutil.copy2 to record calls
    monkeypatch.setattr('shutil.copy2', lambda src, dst: None)
    # Patch print to capture output
    printed = []
    monkeypatch.setattr(builtins, 'print', lambda *a, **kw: printed.append(a))
    # Patch get_all_dreams to return all samples as existing
    import scripts.init_sample_dreams as mod
    patch_sample_dreams.get_all_dreams.return_value = [
        {'video_filename': f'dream_{i}.mp4'} for i in range(1, 5)
    ]
    mod.main()
    # Should print already exists for all samples
    assert all('already exists' in str(x) for x in printed) 