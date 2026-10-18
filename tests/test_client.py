"""Tests pour llm/client.py.

Toutes les requêtes HTTP sont simulées avec unittest.mock.
Aucun appel à l'API Tavily réelle.
"""

from unittest.mock import MagicMock, patch

import pytest

from chatbot.core.prompt import ConversationTurn
from chatbot.llm.client import (
    TAVILY_ENDPOINT,
    TavilyError,
    _build_answer_from_results,
    _clean_content,
    ask,
)


MOCK_RESPONSE = {
    "results": [
        {
            "title": "Python - Wikipédia",
            "content": "Python est un langage de programmation créé par Guido van Rossum.",
            "url": "https://fr.wikipedia.org/wiki/Python",
        },
        {
            "title": "Python.org",
            "content": "Welcome to the Python Programming Language community.",
            "url": "https://python.org",
        },
    ]
}

MOCK_RESPONSE_WITH_ANSWER = {
    "answer": "Python is a high-level programming language created by Guido van Rossum.",
    "results": MOCK_RESPONSE["results"],
}


def _make_settings() -> MagicMock:
    s = MagicMock()
    s.tavily_api_key = "test-key"
    s.tavily_max_results = 5
    s.tavily_search_depth = "basic"
    return s


# --- ask() ---


@patch("chatbot.llm.client.requests.post")
def test_ask_single_question(mock_post: MagicMock) -> None:
    """ask() renvoie une ConversationTurn avec les sources."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = MOCK_RESPONSE

    result = ask(
        "Qu'est-ce que Python ?",
        [ConversationTurn(user="Q1", assistant="R1")],
        _make_settings(),
    )

    assert isinstance(result, ConversationTurn)
    assert result.user == "Qu'est-ce que Python ?"
    assert len(result.sources) == 2
    assert "Wikipédia" in result.assistant or "Python" in result.assistant.upper()


@patch("chatbot.llm.client.requests.post")
def test_ask_sends_tavily_payload(mock_post: MagicMock) -> None:
    """ask() envoie le bon payload à Tavily."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = MOCK_RESPONSE

    ask("Quelle est la capitale de la France ?", [], _make_settings())

    payload = mock_post.call_args_list[0].kwargs["json"]
    call_url = mock_post.call_args_list[0].args[0]

    assert call_url == TAVILY_ENDPOINT
    assert payload["api_key"] == "test-key"
    # La question est préfixée par l'instruction FR ou traduite
    assert "capitale" in payload["query"].lower()
    assert payload["include_answer"] is True
    assert payload["language"] == "fr"
    assert payload["search_depth"] == "basic"


@patch("chatbot.llm.client.requests.post")
def test_ask_no_results(mock_post: MagicMock) -> None:
    """ask() gère le cas sans résultat."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"results": []}

    result = ask("question improbable", [], _make_settings())
    assert result.sources == []
    assert "pas trouvé" in result.assistant.lower()


@patch("chatbot.llm.client.requests.post")
def test_ask_http_error_401(mock_post: MagicMock) -> None:
    """ask() lève TavilyError en cas d'erreur 401."""
    mock_post.return_value.status_code = 401
    mock_post.return_value.text = "Unauthorized"

    with pytest.raises(TavilyError) as exc_info:
        ask("bonjour", [], _make_settings())
    assert exc_info.value.status == 401


@patch("chatbot.llm.client.requests.post")
def test_ask_http_error_500(mock_post: MagicMock) -> None:
    """ask() lève TavilyError en cas d'erreur 500."""
    mock_post.return_value.status_code = 500
    mock_post.return_value.text = "Internal Server Error"

    with pytest.raises(TavilyError) as exc_info:
        ask("bonjour", [], _make_settings())
    assert exc_info.value.status == 500


@patch("chatbot.llm.client.translate_to_french")
@patch("chatbot.llm.client.requests.post")
def test_ask_answer_translated(mock_post: MagicMock, mock_translate: MagicMock) -> None:
    """L'answer de Tavily est passé par translate_to_french."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = MOCK_RESPONSE_WITH_ANSWER
    mock_translate.side_effect = lambda t: "La réponse est en français." if len(t) > 20 else t

    result = ask("What is Python?", [], _make_settings())
    assert "français" in result.assistant.lower()
    # translate_to_french est appelée au moins 2 fois : question + answer
    assert mock_translate.call_count >= 2


# --- helpers ---


def test_clean_content_removes_html() -> None:
    """_clean_content retire les tags HTML."""
    cleaned = _clean_content("Bonjour <br>Mondo <a href='x'>link</a> !!")
    assert "<br>" not in cleaned
    assert "<a" not in cleaned
    assert "Bonjour" in cleaned


def test_clean_content_removes_markdown_headings() -> None:
    """_clean_content retire les headings Markdown."""
    cleaned = _clean_content("## Titre\n### Sous-titre\nContent")
    assert "##" not in cleaned
    assert "###" not in cleaned


def test_clean_content_max_len() -> None:
    """_clean_content respecte la limite de longueur."""
    cleaned = _clean_content("a" * 500, max_len=100)
    assert len(cleaned) <= 100


def test_build_answer_empty() -> None:
    """_build_answer_from_results renvoie un message vide propre."""
    result = _build_answer_from_results([])
    assert "pas trouvé" in result.lower()


def test_build_answer_with_results() -> None:
    """_build_answer_from_results construit une réponse depuis les résultats."""
    results = [
        {"title": "Test", "content": "Un contenu de test", "url": "https://a.fr"},
    ]
    answer = _build_answer_from_results(results)
    assert "Test" in answer
    assert "Un contenu de test" in answer


def test_tavily_error_message() -> None:
    """TavilyError contient le code et le détail."""
    err = TavilyError(403, "Forbidden")
    assert err.status == 403
    assert "403" in str(err)
    assert "Forbidden" in str(err)
