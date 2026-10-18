"""Tests pour core/engine.py — couverture des branches de commandes."""

from collections.abc import Callable
from unittest.mock import MagicMock, patch

from chatbot.core.engine import ConversationEngine
from chatbot.core.prompt import ConversationTurn
from chatbot.llm.client import TavilyError


def _make_settings() -> MagicMock:
    s = MagicMock()
    s.tavily_api_key = "test"
    s.tavily_max_results = 5
    s.tavily_search_depth = "basic"
    s.memory_turns = 5
    s.log_level = "DEBUG"
    return s


def _make_get_input(inputs: list[str]) -> MagicMock:
    """Crée un mock get_input qui consomme une liste de chaînes."""
    it = iter(inputs)
    mock = MagicMock()
    mock.side_effect = lambda: next(it)
    return mock


@patch("chatbot.core.engine.ask")
@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_single_turn(
    mock_banner: MagicMock, mock_consent: MagicMock, mock_ask: MagicMock,
    capsys: object,
) -> None:
    """Un tour de conversation s'effectue correctement."""
    mock_ask.return_value = ConversationTurn(
        user="bonjour",
        assistant="salut, comment puis-je t'aider ?",
        sources=[],
    )
    get_input = _make_get_input(["bonjour", "/quit"])
    with patch("chatbot.core.engine.get_consent", return_value=True):
        engine = ConversationEngine(
            _make_settings(), get_input=get_input
        )
        engine.start()
    captured = capsys.readouterr()
    assert "salut, comment puis-je t'aider ?" in captured.out


@patch("chatbot.core.engine.ask")
@patch("chatbot.core.engine.get_consent", return_value=False)
def test_engine_no_consent(
    mock_consent: MagicMock, mock_ask: MagicMock, capsys: object,
) -> None:
    """Sans consentement, le chatbot ne démarre pas."""
    get_input = _make_get_input(["/quit"])
    engine = ConversationEngine(_make_settings(), get_input=get_input)
    engine.start()
    mock_ask.assert_not_called()
    captured = capsys.readouterr()
    assert "Session annulée" in captured.out


@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_undo_command(
    mock_banner: MagicMock, mock_consent: MagicMock, capsys: object,
) -> None:
    """/undo supprime la dernière réponse de l'historique."""
    with patch("chatbot.core.engine.ask", return_value=ConversationTurn(
        user="Q", assistant="à supprimer"
    )):
        get_input = _make_get_input(["Q", "/undo", "/quit"])
        engine = ConversationEngine(_make_settings(), get_input=get_input)
        engine.start()
    captured = capsys.readouterr()
    assert "annulée" in captured.out.lower()


@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_correct_command(
    mock_banner: MagicMock, mock_consent: MagicMock, capsys: object,
) -> None:
    """/correct remplace la dernière réponse."""
    with patch("chatbot.core.engine.ask", return_value=ConversationTurn(
        user="Q", assistant="ancienne"
    )):
        get_input = _make_get_input(["Q", "/correct nouvelle", "/quit"])
        engine = ConversationEngine(_make_settings(), get_input=get_input)
        engine.start()
    captured = capsys.readouterr()
    assert "corrigée" in captured.out.lower()


@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_help_command(
    mock_banner: MagicMock, mock_consent: MagicMock, capsys: object,
) -> None:
    """/help affiche l'aide sans appeler le LLM."""
    get_input = _make_get_input(["/help", "/quit"])
    with patch("chatbot.core.engine.ask"):
        engine = ConversationEngine(_make_settings(), get_input=get_input)
        engine.start()
    captured = capsys.readouterr()
    assert "/undo" in captured.out
    assert "/correct" in captured.out
    assert "/export" in captured.out


@patch("chatbot.core.engine.export_to_console")
@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_export_command(
    mock_banner: MagicMock, mock_consent: MagicMock,
    mock_export: MagicMock,
) -> None:
    """/export appelle export_to_console."""
    get_input = _make_get_input(["Q", "/export", "/quit"])
    with patch("chatbot.core.engine.ask", return_value=ConversationTurn(
        user="Q", assistant="R"
    )):
        engine = ConversationEngine(_make_settings(), get_input=get_input)
        engine.start()
    mock_export.assert_called_once()


@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_empty_input_is_skipped(
    mock_banner: MagicMock, mock_consent: MagicMock, capsys: object,
) -> None:
    """Une ligne vide est ignorée, ni /quit ni LLM n'est appelé."""
    get_input = _make_get_input(["", "  ", "/quit"])
    with patch("chatbot.core.engine.ask") as mock_ask:
        engine = ConversationEngine(_make_settings(), get_input=get_input)
        engine.start()
    mock_ask.assert_not_called()


@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_tavily_error_is_handled(
    mock_banner: MagicMock, mock_consent: MagicMock, capsys: object,
) -> None:
    """L'erreur Tavily est affichée, le chatbot continue."""
    get_input = _make_get_input(["question", "/quit"])
    with patch("chatbot.core.engine.ask",
               side_effect=TavilyError(500, "Serveur down")):
        engine = ConversationEngine(_make_settings(), get_input=get_input)
        engine.start()
    captured = capsys.readouterr()
    assert "Erreur" in captured.out


@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_eof_ends_loop(
    mock_banner: MagicMock, mock_consent: MagicMock,
) -> None:
    """Un EOF (Ctrl+D) termine proprement la boucle."""
    def _raise_eof() -> str:
        raise EOFError

    engine = ConversationEngine(_make_settings(), get_input=_raise_eof)
    with patch("chatbot.core.engine.ask"):
        engine.start()
    assert len(engine.memory) == 0


@patch("chatbot.core.engine.get_consent", return_value=False)
def test_engine_no_consent_branch(
    mock_consent: MagicMock, capsys: object,
) -> None:
    """Pas de consentement : le chatbot ne démarre pas."""
    get_input = _make_get_input(["/quit"])
    engine = ConversationEngine(_make_settings(), get_input=get_input)
    with patch("chatbot.core.engine.display_transparency_banner") as mock_banner:
        engine.start()
    assert not mock_banner.called
    captured = capsys.readouterr()
    assert "Session annulée" in captured.out


@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_stats_command(
    mock_banner: MagicMock, mock_consent: MagicMock, capsys: object,
) -> None:
    """/stats affiche les statistiques de la session."""
    get_input = _make_get_input(["Q", "/stats", "/quit"])
    with patch("chatbot.core.engine.ask", return_value=ConversationTurn(
        user="Q", assistant="R", sources=["https://a.fr"]
    )):
        engine = ConversationEngine(_make_settings(), get_input=get_input)
        engine.start()
    captured = capsys.readouterr()
    assert "tours: 1" in captured.out
    assert "Sources:" in captured.out or "sources:" in captured.out


@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_sources_displayed_when_present(
    mock_banner: MagicMock, mock_consent: MagicMock, capsys: object,
) -> None:
    """Les sources sont affichées quand elles sont présentes."""
    turn = ConversationTurn(
        user="Q", assistant="R",
        sources=["https://a.fr", "https://b.fr"],
    )
    get_input = _make_get_input(["Q", "/quit"])
    with patch("chatbot.core.engine.ask", return_value=turn):
        engine = ConversationEngine(_make_settings(), get_input=get_input)
        engine.start()
    captured = capsys.readouterr()
    assert "https://a.fr, https://b.fr" in captured.out
