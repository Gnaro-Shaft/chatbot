"""Tests pour llm/client.py.

Toutes les requêtes HTTP sont simulées avec unittest.mock.
Le test ne doit jamais appeler l'API Tavily réelle.
"""

from unittest.mock import MagicMock, patch

import pytest

from chatbot.core.prompt import ConversationTurn
from chatbot.llm.client import TavilyError, ask, TAVILY_ENDPOINT


MOCK_RESPONSE = {
    "answer": "Python est un langage de programmation créé par Guido van Rossum.",
    "results": [
        {"title": "Python - Wikipédia", "url": "https://fr.wikipedia.org/wiki/Python"},
        {"title": "Python.org", "url": "https://python.org"},
    ],
}


def _make_settings() -> MagicMock:
    """Crée un mock de Settings."""
    s = MagicMock()
    s.tavily_api_key = "test-key"
    s.tavily_max_results = 5
    s.tavily_search_depth = "basic"
    return s


@patch("chatbot.llm.client.requests.post")
def test_ask_single_question(mock_post: MagicMock) -> None:
    """ask() renvoie un ConversationTurn avec la réponse et les sources."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = MOCK_RESPONSE

    result = ask("Qu'est-ce que Python ?", [ConversationTurn(user="Q1", assistant="R1")], _make_settings())

    assert isinstance(result, ConversationTurn)
    assert result.user == "Qu'est-ce que Python ?"
    assert "Python est un langage" in result.assistant
    assert len(result.sources) == 2
    assert "https://fr.wikipedia.org/wiki/Python" in result.sources


@patch("chatbot.llm.client.requests.post")
def test_ask_with_history_includes_context(mock_post: MagicMock) -> None:
    """ask() avec un historique envoie le contexte au payload."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = MOCK_RESPONSE

    history = [ConversationTurn(user="Q1", assistant="R1")]
    ask("Q2", history, _make_settings())

    payload = mock_post.call_args_list[0].kwargs["json"]
    assert "Q1 → R1" in payload["query"]
    assert "Q2" in payload["query"]


@patch("chatbot.llm.client.requests.post")
def test_ask_no_results(mock_post: MagicMock) -> None:
    """ask() gère le cas sans résultat ni answer."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"answer": "", "results": []}

    result = ask("question improbable", [], _make_settings())
    assert isinstance(result, ConversationTurn)
    assert result.user == "question improbable"
    assert result.sources == []


@patch("chatbot.llm.client.requests.post")
def test_ask_http_error_401(mock_post: MagicMock) -> None:
    """ask() lève TavilyError en cas d'erreur 401."""
    mock_post.return_value.status_code = 401
    mock_post.return_value.text = "Unauthorized"

    with pytest.raises(TavilyError) as exc_info:
        ask("bonjour", [], _make_settings())

    assert exc_info.value.status == 401
    assert "401" in str(exc_info.value)


@patch("chatbot.llm.client.requests.post")
def test_ask_http_error_500(mock_post: MagicMock) -> None:
    """ask() lève TavilyError en cas d'erreur serveur 500."""
    mock_post.return_value.status_code = 500
    mock_post.return_value.text = "Internal Server Error"

    with pytest.raises(TavilyError) as exc_info:
        ask("bonjour", [], _make_settings())

    assert exc_info.value.status == 500


@patch("chatbot.llm.client.requests.post")
def test_ask_payload_structure(mock_post: MagicMock) -> None:
    """ask() envoie le payload correct à l'endpoint Tavily."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = MOCK_RESPONSE

    ask("test", [], _make_settings())

    mock_post.assert_called_once()
    call_url = mock_post.call_args_list[0].args[0]
    payload = mock_post.call_args_list[0].kwargs["json"]

    assert call_url == TAVILY_ENDPOINT
    assert payload["api_key"] == "test-key"
    assert "test" in payload["query"]
    assert payload["include_answer"] is True
    assert payload["search_depth"] == "basic"


def test_tavily_error_message() -> None:
    """TavilyError contient le code et le détail."""
    err = TavilyError(403, "Forbidden")
    assert err.status == 403
    assert "403" in str(err)
    assert "Forbidden" in str(err)
