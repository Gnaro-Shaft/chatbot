"""Tests pour chatbot/ui.py — les méthodes de la UI ne touchent pas l'API LLM."""

from chatbot.ui import BANNER, HELP_TEXT, PROMPT, PromptUI


def test_prompt_ui_default_session() -> None:
    """PromptUI crée une session prompt_toolkit par défaut."""
    ui = PromptUI()
    assert ui.session is not None


def test_banners_contain_ansi() -> None:
    """Les constantes de couleurs contiennent des codes ANSI."""
    assert "\033[" in BANNER
    assert "\033[" in HELP_TEXT
    # PROMPT est un objet ANSI — on vérifie qu'il est bien un ANSI
    from prompt_toolkit.formatted_text import ANSI as ANSIType
    assert isinstance(PROMPT, ANSIType)


def test_help_content() -> None:
    """HELP_TEXT contient toutes les commandes."""
    assert "/quit" in HELP_TEXT
    assert "/help" in HELP_TEXT
    assert "/export" in HELP_TEXT
    assert "/stats" in HELP_TEXT
    assert "/undo" in HELP_TEXT
    assert "/correct" in HELP_TEXT


def test_ui_methods_no_error(capsys: object) -> None:
    """Les méthodes d'affichage ne lèvent pas d'exception."""
    ui = PromptUI()
    ui.info("test info")
    ui.error("test erreur")
    ui.success("test succès")
    ui.chatbot_msg("bonjour")
    ui.sources(["https://a.fr", "https://b.fr"])
    ui.stats_line(3, 5, 10)
    ui.banner()
    ui.help()
    captured = capsys.readouterr()
    assert len(captured.out) > 0
