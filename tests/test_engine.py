"""Tests pour core/engine.py — couverture des branches de commandes."""

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


def _simulate(inputs: list[str]) -> MagicMock:
    """Crée un mock de input qui consomme une liste de chaînes."""
    it = iter(inputs)
    return patch("builtins.input", side_effect=lambda *_: next(it))


@patch("chatbot.core.engine.ask")
@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_undo_command(
    mock_banner: MagicMock, mock_consent: MagicMock, mock_ask: MagicMock,
    capsys: object,
) -> None:
    """/undo supprime la dernière réponse de l'historique."""
    mock_ask.return_value = ConversationTurn(
        user="Q", assistant="R-a-supprimer"
    )
    engine = ConversationEngine(_make_settings())
    with _simulate(["Q", "/undo", "/quit"]):
        engine.start()

    captured = capsys.readouterr()
    assert "annulée" in captured.out.lower()
    assert len(engine.memory) == 0


@patch("chatbot.core.engine.ask")
@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_correct_command(
    mock_banner: MagicMock, mock_consent: MagicMock, mock_ask: MagicMock,
    capsys: object,
) -> None:
    """/correct remplace la dernière réponse."""
    mock_ask.return_value = ConversationTurn(user="Q", assistant="ancienne réponse")
    engine = ConversationEngine(_make_settings())
    with _simulate(["Q", "/correct nouvelle réponse", "/quit"]):
        engine.start()

    captured = capsys.readouterr()
    assert "corrigée" in captured.out.lower()
    assert engine.memory.last().assistant == "nouvelle réponse"


@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_help_command(
    mock_banner: MagicMock, mock_consent: MagicMock, capsys: object,
) -> None:
    """/help affiche l'aide sans appeler le LLM."""
    engine = ConversationEngine(_make_settings())
    with patch("chatbot.core.engine.ask"), \
         _simulate(["/help", "/quit"]):
        engine.start()

    captured = capsys.readouterr()
    assert "/undo" in captured.out
    assert "/correct" in captured.out
    assert "/export" in captured.out


@patch("chatbot.core.engine.export_to_console")
@patch("chatbot.core.engine.ask")
@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_export_command(
    mock_banner: MagicMock, mock_consent: MagicMock,
    mock_ask: MagicMock, mock_export: MagicMock,
) -> None:
    """/export appelle export_to_console."""
    mock_ask.return_value = ConversationTurn(user="Q", assistant="R")
    engine = ConversationEngine(_make_settings())
    with _simulate(["Q", "/export", "/quit"]):
        engine.start()
    mock_export.assert_called_once()


@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_empty_input_is_skipped(
    mock_banner: MagicMock, mock_consent: MagicMock, capsys: object,
) -> None:
    """Une ligne vide est ignorée, ni /quit ni LLM n'est appelé."""
    engine = ConversationEngine(_make_settings())
    with patch("chatbot.core.engine.ask") as mock_ask, \
         _simulate(["", "  ", "/quit"]):
        engine.start()
    mock_ask.assert_not_called()


@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_tavily_error_is_handled(
    mock_banner: MagicMock, mock_consent: MagicMock, capsys: object,
) -> None:
    """L'erreur Tavily est capturée et affichée, le chatbot continue."""
    engine = ConversationEngine(_make_settings())
    with patch("chatbot.core.engine.ask", side_effect=TavilyError(500, "Serveur down")): 
        with _simulate(["question", "/quit"]):
            engine.start()
    captured = capsys.readouterr()
    assert "Erreur" in captured.out


@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_eof_ends_loop(
    mock_banner: MagicMock, mock_consent: MagicMock,
) -> None:
    """Un EOF (Ctrl+D) termine proprement la boucle."""
    engine = ConversationEngine(_make_settings())
    it = iter([])
    with patch("chatbot.core.engine.ask"), \
         patch("builtins.input", side_effect=lambda *_: (_ for _ in ()).throw(EOFError)):
        engine.start()
    assert len(engine.memory) == 0


@patch("chatbot.core.engine.get_consent", return_value=False)
def test_engine_no_consent_branch(
    mock_consent: MagicMock, capsys: object,
) -> None:
    """Pas de consentement : le chatbot ne démarre pas."""
    engine = ConversationEngine(_make_settings())
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
    engine = ConversationEngine(_make_settings())
    with patch("chatbot.core.engine.ask", return_value=ConversationTurn(
        user="Q", assistant="R", sources=["https://a.fr"]
    )), _simulate(["Q", "/stats", "/quit"]):
        engine.start()
    captured = capsys.readouterr()
    assert "Tours:  1" in captured.out
    assert "Sources: 1" in captured.out
    assert "Sources: https://a.fr" in captured.out


@patch("chatbot.core.engine.get_consent", return_value=True)
@patch("chatbot.core.engine.display_transparency_banner")
def test_engine_sources_displayed_when_present(
    mock_banner: MagicMock, mock_consent: MagicMock, capsys: object,
) -> None:
    """Les sources sont affichées quand elles sont présentes."""
    turn = ConversationTurn(
        user="Q", assistant="R", sources=["https://a.fr", "https://b.fr"]
    )
    engine = ConversationEngine(_make_settings())
    with patch("chatbot.core.engine.ask", return_value=turn), _simulate(["Q", "/quit"]):
        engine.start()
    captured = capsys.readouterr()
    assert "https://a.fr, https://b.fr" in captured.out
