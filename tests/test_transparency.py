"""Tests pour ai_act/transparency.py et ai_act/oversight.py."""

from unittest.mock import patch

from chatbot.ai_act.oversight import correct, undo
from chatbot.ai_act.transparency import TAKEOVER_BANNER, display_transparency_banner
from chatbot.core.history import MemoryManager
from chatbot.core.prompt import ConversationTurn


def test_display_transparency_banner_prints() -> None:
    """display_transparency_banner affiche le texte exact."""
    with patch("builtins.print") as mock_print:
        display_transparency_banner()
        mock_print.assert_called_once_with(TAKEOVER_BANNER)


def test_oversight_undo() -> None:
    """undo() supprime le dernier tour."""
    mgr = MemoryManager()
    mgr.add(ConversationTurn(user="Q", assistant="R"))
    msg = undo(mgr)
    assert "annulée" in msg.lower()
    assert len(mgr) == 0


def test_oversight_undo_empty() -> None:
    """undo() sur un historique vide renvoie un message d'info."""
    mgr = MemoryManager()
    msg = undo(mgr)
    assert "Aucun" in msg


def test_oversight_correct() -> None:
    """correct() remplace la dernière réponse."""
    mgr = MemoryManager()
    mgr.add(ConversationTurn(user="Q", assistant="faux", sources=[]))
    msg = correct(mgr, "bon")
    assert "corrigée" in msg.lower()
    assert mgr.last().assistant == "bon"


def test_oversight_correct_empty() -> None:
    """correct() sur un historique vide renvoie un message d'info."""
    mgr = MemoryManager()
    msg = correct(mgr, "nouvelle réponse")
    assert "Aucun" in msg
