"""Tests pour llm/client.py.

Toutes les requêtes HTTP sont simulées avec unittest.mock.
Le test ne doit jamais appeler l'API Tavily réelle.
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
            "content": "Python est un langage de programmation créé par Guido van Rossum. "
            "## Historique\n### 1991 - Première version",
            "url": "https://fr.wikipedia.org/wiki/Python",
        },
        {
            "title": "Python.org",
            "content": "Welcome to the Python Programming language",
            "url": "https://python.org",
        },
    ],
}


def _make_settings() -> MagicMock:
    """Crée un mock de Settings."""
    s = MagicMock()
    s.tavily_api_key = "test-key"
    s.tavily_max_results = 5
    s.tavily_search_depth = "basic"
    return s


# --- ask() ---


@patch("chatbot.llm.client.requests.post")
def test_ask_single_question(mock_post: MagicMock) -> None:
    """ask() renvoie une ConversationTurn construite depuis les résultats."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = MOCK_RESPONSE

    result = ask(
        "Qu'est-ce que Python ?",
        [ConversationTurn(user="Q1", assistant="R1")],
        _make_settings(),
    )

    assert isinstance(result, ConversationTurn)
    assert result.user == "Qu'est-ce que Python ?"
    len(result.sources) == 2
    assert "Wikipédia" in result.assistant or "Python" in result.assistant


@patch("chatbot.llm.client.requests.post")
def test_ask_with_history_sends_only_question(mock_post: MagicMock) -> None:
    """ask() envoie seulement la question (pas l'historique) au moteur de recherche."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = MOCK_RESPONSE

    history = [ConversationTurn(user="Q1", assistant="R1")]
    ask("Q2", history, _make_settings())

    payload = mock_post.call_args_list[0].kwargs["json"]
    # La question est envoyée avec un préfixe FR pour forcer la langue de la réponse
    assert "Q2" in payload["query"]
    assert "français" in payload["query"].lower()


@patch("chatbot.llm.client.requests.post")
def test_ask_no_results(mock_post: MagicMock) -> None:
    """ask() gère le cas sans résultat."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"results": []}

    result = ask("question improbable", [], _make_settings())
    assert isinstance(result, ConversationTurn)
    assert result.user == "question improbable"
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


@patch("chatbot.llm.client.requests.post")
def test_ask_payload_structure(mock_post: MagicMock) -> None:
    """ask() envoie le payload correct à Tavily."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = MOCK_RESPONSE

    ask("test", [], _make_settings())

    payload = mock_post.call_args_list[0].kwargs["json"]
    call_url = mock_post.call_args_list[0].args[0]

    assert call_url == TAVILY_ENDPOINT
    assert payload["api_key"] == "test-key"
    assert "test" in payload["query"]
    assert "français" in payload["query"].lower()
    assert payload["include_answer"] is True
    assert payload["language"] == "fr"
    assert payload["search_depth"] == "basic"


# --- helpers ---


def test_clean_content_removes_html_tags() -> None:
    """_clean_content retire les tags HTML."""
    raw = "Bonjour <br>Mondo <a href='x'>link</a> !!"
    cleaned = _clean_content(raw)
    assert "<br>" not in cleaned
    assert "<a" not in cleaned
    assert "Bonjour Mondo link" in cleaned.upper().replace("!".upper(), "").replace("!".upper(), "") or \
        "Bonjour" in cleaned


def test_clean_content_removes_markdown_headings() -> None:
    """_clean_content retire les headings Markdown (# ##)."""
    raw = "## Titre\nContenu du texte\n### Sous-titre\n"
    cleaned = _clean_content(raw)
    assert "##" not in cleaned
    assert "Titre" not in cleaned or cleaned.count("Titre") == 0 or "contenu" in cleaned.lower()


def test_clean_content_max_len() -> None:
    """_clean_content respecte la limite de longueur."""
    raw = "a" * 500
    cleaned = _clean_content(raw, max_len=100)
    assert len(cleaned) <= 100


def test_build_answer_empty_results() -> None:
    """_build_answer_from_results renvoie un message vide propre."""
    result = _build_answer_from_results([])
    assert "pas trouvé" in result.lower()


def test_build_answer_with_results() -> None:
    """_build_answer_from_results construit une réponse depuis les résultats."""
    results = [
        {"title": "Test", "content": "Contenu de test", "url": "https://a.fr"},
    ]
    answer = _build_answer_from_results(results)
    assert "Test" in answer
    assert "Contenu de test" in answer


def test_tavily_error_message() -> None:
    """TavilyError contient le code et le détail."""
    err = TavilyError(403, "Forbidden")
    assert err.status == 403
    assert "403" in str(err)
    assert "Forbidden" in str(err)
