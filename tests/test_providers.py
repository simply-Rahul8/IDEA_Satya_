import pytest

from engine import providers


def test_default_is_mock(monkeypatch):
    monkeypatch.delenv("SATYA_LLM", raising=False)
    assert isinstance(providers.get_provider(), providers.MockProvider)


def test_mock_is_deterministic():
    p = providers.get_provider()
    assert p.complete("hello").text == p.complete("hello").text
    assert p.complete("hello").text != p.complete("other").text


def test_live_mode_not_silently_mocked(monkeypatch):
    monkeypatch.setenv("SATYA_LLM", "live")
    with pytest.raises(NotImplementedError):
        providers.get_provider()
