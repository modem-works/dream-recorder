import pytest
import scripts.test_openai_key as oai
import sys
import os
import builtins
import importlib
import subprocess
import shutil
import tempfile

class FakeClient:
    def __init__(self, raise_exc=None):
        self._raise_exc = raise_exc
        self.models = self
    def list(self):
        if self._raise_exc:
            raise self._raise_exc
        return ['model']

def test_check_openai_api_key_success(monkeypatch):
    monkeypatch.setattr(oai.openai, 'OpenAI', lambda api_key: FakeClient())
    assert oai.check_openai_api_key('key') is True

def test_check_openai_api_key_auth_error(monkeypatch):
    class AuthError(Exception): pass
    monkeypatch.setattr(oai.openai, 'AuthenticationError', AuthError)
    monkeypatch.setattr(oai.openai, 'OpenAI', lambda api_key: FakeClient(raise_exc=AuthError()))
    assert oai.check_openai_api_key('key') is False

def test_check_openai_api_key_other_error(monkeypatch, capsys):
    class AuthError(Exception): pass
    class OtherError(Exception): pass
    monkeypatch.setattr(oai.openai, 'AuthenticationError', AuthError)
    monkeypatch.setattr(oai.openai, 'OpenAI', lambda api_key: FakeClient(raise_exc=OtherError('fail')))
    assert oai.check_openai_api_key('key') is False
    out = capsys.readouterr().out
    assert 'Error:' in out 

def _patched_openai_script(tmp_path, return_value):
    """Create a temp copy of the script with check_openai_api_key always returning return_value."""
    orig = os.path.join(os.path.dirname(__file__), '../scripts/test_openai_key.py')
    with open(orig, 'r') as f:
        code = f.read()
    # Patch the function
    code = code.replace(
        'def check_openai_api_key(api_key):',
        f'def check_openai_api_key(api_key):\n    return {return_value}\n#'
    )
    tmp_script = tmp_path / 'test_openai_key_patch.py'
    tmp_script.write_text(code)
    return str(tmp_script)

def test_main_block_valid_key_subprocess(tmp_path):
    script = _patched_openai_script(tmp_path, 'True')
    result = subprocess.run([sys.executable, script, 'valid'], capture_output=True, text=True)
    assert 'Valid OpenAI API key.' in result.stdout

def test_main_block_invalid_key_subprocess(tmp_path):
    script = _patched_openai_script(tmp_path, 'False')
    result = subprocess.run([sys.executable, script, 'invalid'], capture_output=True, text=True)
    assert 'Invalid OpenAI API key.' in result.stdout

def test_main_block_missing_key_subprocess(tmp_path):
    script = _patched_openai_script(tmp_path, 'True')
    # Remove env var if present
    env = os.environ.copy()
    env.pop('OPENAI_API_KEY', None)
    result = subprocess.run([sys.executable, script], capture_output=True, text=True, env=env)
    assert 'Usage:' in result.stdout
    assert result.returncode == 1 