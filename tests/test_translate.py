"""Tests pour ai_act/translate.py.

L'API MyMemory est mockée — aucun appel réseau réel.
"""

from unittest.mock import MagicMock, patch

from chatbot.ai_act.translate import (
    _MEM_CACHE,
    _mymemory_translate,
    is_french,
    translate_to_french,
)

MYMEMORY_OK = {
    "responseData": {"translatedText": "Bonjour le monde", "match": 0.95},
    "responseStatus": 200,
}


# --- is_french ---


def test_is_french_with_accents() -> None:
    """Un texte avec 2+ caractères accentués est détecté en français."""
    assert is_french("Bonjour, comment ça va ?")
    assert is_french("L'hôpital est proche")
    assert is_french("Il y a été être")


def test_is_french_without_accents_short_english() -> None:
    """Un texte court en anglais n'est pas français."""
    assert not is_french("Hello world")
    assert not is_french("The quick brown fox jumps")


def test_is_french_empty() -> None:
    """Une chaîne vide ou espace n'est pas détectée en français."""
    assert not is_french("")
    assert not is_french("   ")


def test_is_french_french_stopwords() -> None:
    """Un texte sans accents mais riche en stopwords FR est accepté."""
    text = "le la les un une des et ou mais"  # 10/10 stopwords
    assert is_french(text)


# --- translate_to_french ---


def test_translate_already_french_no_network() -> None:
    """Un texte déjà en français n'appelle pas MyMemory."""
    import chatbot.ai_act.translate as mod

    mod._MEM_CACHE.clear()
    with patch("chatbot.ai_act.translate.requests.get") as mock_get:
        mock_get.return_value = _fake_response(200)
        result = translate_to_french("Bonjour, comment ça va ?")
        assert result == "Bonjour, comment ça va ?"
        mock_get.assert_not_called()


@patch("chatbot.ai_act.translate.requests.get")
def test_translate_english(mock_get: MagicMock) -> None:
    """Un texte en anglais est traduit via MyMemory."""
    import chatbot.ai_act.translate as mod

    mod._MEM_CACHE.clear()
    mock_get.return_value = _fake_response(200, json_data=MYMEMORY_OK)

    result = translate_to_french("Hello world how are you")
    assert result == "Bonjour le monde"
    mock_get.assert_called_once()
    url = mock_get.call_args.args[0]
    assert "langpair=en|fr" in url


@patch("chatbot.ai_act.translate.requests.get")
def test_translate_cache(mock_get: MagicMock) -> None:
    """Deux traductions identiques : la 2e est servie par le cache."""
    import chatbot.ai_act.translate as mod

    mod._MEM_CACHE.clear()
    mock_get.return_value = _fake_response(200, json_data=MYMEMORY_OK)

    r1 = translate_to_french("Cache test text not french")
    r2 = translate_to_french("Cache test text not french")
    assert r1 == r2
    assert mock_get.call_count == 1  # 1 seul appel réseau
    assert len(mod._MEM_CACHE) == 1


@patch(
    "chatbot.ai_act.translate.requests.get",
    side_effect=Exception("réseau down"),
)
def test_translate_graceful_fallback(mock_get: MagicMock) -> None:
    """En cas d'erreur réseau, on renvoie le texte d'origine."""
    import chatbot.ai_act.translate as mod

    mod._MEM_CACHE.clear()
    original = "some english text that is not in french language at all"
    result = translate_to_french(original)
    assert result == original


@patch("chatbot.ai_act.translate.requests.get")
def test_translate_empty_string(mock_get: MagicMock) -> None:
    """Une chaîne vide est renvoyée sans appel réseau."""
    import chatbot.ai_act.translate as mod

    mod._MEM_CACHE.clear()
    assert translate_to_french("") == ""
    mock_get.assert_not_called()


# --- helpers ---


def test_mymemory_translate_ok() -> None:
    """_mymemory_translate appelle MyMemory et renvoie le texte traduit."""
    with patch("chatbot.ai_act.translate.requests.get") as mock_get:
        mock_get.return_value = _fake_response(200, json_data=MYMEMORY_OK)
        result = _mymemory_translate("Hello")
        assert result == "Bonjour le monde"


def test_mymemory_translate_error() -> None:
    """_mymemory_translate renvoie une chaîne vide en cas d'erreur."""
    with patch(
        "chatbot.ai_act.translate.requests.get",
        side_effect=Exception("down"),
    ):
        result = _mymemory_translate("Hello")
        assert result == ""


# --- mock helpers ---


class _FakeResp:
    """Mini fausse réponse requests."""

    def __init__(self, status: int, json_data: dict | None = None) -> None:
        self.status_code = status
        self._json = json_data or {}

    def json(self) -> dict:
        return self._json

    def raise_for_status(self) -> None:
        pass


def _fake_response(status: int = 200, json_data: dict | None = None) -> _FakeResp:
    return _FakeResp(status, json_data)
