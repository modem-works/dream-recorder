import pytest
import scripts.test_luma_key as luma

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