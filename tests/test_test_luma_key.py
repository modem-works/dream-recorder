import pytest
import scripts.test_luma_key as luma
import sys
import os
import builtins
import importlib
import subprocess
import shutil
import tempfile

class FakeResponse:
    def __init__(self, status_code, text=''):
        self.status_code = status_code
        self.text = text

def test_check_luma_api_key_200(monkeypatch):
    monkeypatch.setattr(luma.requests, 'get', lambda *a, **k: FakeResponse(200))
    assert luma.check_luma_api_key('key') is True

def test_check_luma_api_key_401(monkeypatch):
    monkeypatch.setattr(luma.requests, 'get', lambda *a, **k: FakeResponse(401))
    assert luma.check_luma_api_key('key') is False

def test_check_luma_api_key_other(monkeypatch, capsys):
    monkeypatch.setattr(luma.requests, 'get', lambda *a, **k: FakeResponse(500, 'fail'))
    assert luma.check_luma_api_key('key') is False
    out = capsys.readouterr().out
    assert 'Unexpected response' in out

def test_check_luma_api_key_exception(monkeypatch, capsys):
    def raise_exc(*a, **k): raise Exception('fail')
    monkeypatch.setattr(luma.requests, 'get', raise_exc)
    assert luma.check_luma_api_key('key') is False
    out = capsys.readouterr().out
    assert 'Error:' in out

def _patched_luma_script(tmp_path, return_value):
    """Create a temp copy of the script with check_luma_api_key always returning return_value."""
    orig = os.path.join(os.path.dirname(__file__), '../scripts/test_luma_key.py')
    with open(orig, 'r') as f:
        code = f.read()
    # Patch the function
    code = code.replace(
        'def check_luma_api_key(api_key):',
        f'def check_luma_api_key(api_key):\n    return {return_value}\n#'
    )
    tmp_script = tmp_path / 'test_luma_key_patch.py'
    tmp_script.write_text(code)
    return str(tmp_script)

def test_main_block_valid_key_subprocess(tmp_path):
    script = _patched_luma_script(tmp_path, 'True')
    result = subprocess.run([sys.executable, script, 'valid'], capture_output=True, text=True)
    assert 'Valid Luma Labs API key.' in result.stdout

def test_main_block_invalid_key_subprocess(tmp_path):
    script = _patched_luma_script(tmp_path, 'False')
    result = subprocess.run([sys.executable, script, 'invalid'], capture_output=True, text=True)
    assert 'Invalid Luma Labs API key.' in result.stdout

def test_main_block_missing_key_subprocess(tmp_path):
    script = _patched_luma_script(tmp_path, 'True')
    # Remove env var if present
    env = os.environ.copy()
    env.pop('LUMALABS_API_KEY', None)
    result = subprocess.run([sys.executable, script], capture_output=True, text=True, env=env)
    assert 'Usage:' in result.stdout
    assert result.returncode == 1 