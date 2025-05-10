import pytest
import scripts.test_openai_key as oai

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