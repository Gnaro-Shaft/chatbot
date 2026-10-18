"""Tests pour core/history.py."""

from chatbot.core.history import MemoryManager
from chatbot.core.prompt import ConversationTurn


def _turn(user: str, answer: str, sources: list[str] | None = None) -> ConversationTurn:
    """Fabrique un ConversationTurn test."""
    return ConversationTurn(
        user=user,
        assistant=answer,
        sources=sources or [],
    )


def test_add_and_history() -> None:
    """add() puis history renvoie le tour ajouté."""
    mgr = MemoryManager(memory_turns=10)
    mgr.add(_turn("Q1", "R1"))
    mgr.add(_turn("Q2", "R2"))
    assert len(mgr.history) == 2
    assert mgr.history[0].user == "Q1"
    assert mgr.history[1].assistant == "R2"


def test_sliding_window() -> None:
    """L'historique est tronqué à memory_turns."""
    mgr = MemoryManager(memory_turns=3)
    for i in range(5):
        mgr.add(_turn(f"Q{i}", f"R{i}"))

    # On ne conserve que les 3 derniers
    assert len(mgr.history) == 3
    assert mgr.history[0].user == "Q2"  # Q0 et Q1 évincés


def test_last() -> None:
    """last() renvoie le dernier tour."""
    mgr = MemoryManager()
    assert mgr.last() is None
    mgr.add(_turn("Q", "R"))
    assert mgr.last().assistant == "R"


def test_remove_last() -> None:
    """remove_last() supprime et renvoie le dernier tour."""
    mgr = MemoryManager()
    turn = _turn("Q", "R")
    mgr.add(turn)
    removed = mgr.remove_last()
    assert removed is not None
    assert removed.user == "Q"
    assert len(mgr) == 0
    assert mgr.remove_last() is None  # vide


def test_replace_last_correct() -> None:
    """replace_last() modifie la réponse du dernier tour."""
    mgr = MemoryManager()
    mgr.add(_turn("Q", "R-ancienne"))
    updated = mgr.replace_last("R-corrigée")

    assert updated is not None
    assert updated.assistant == "R-corrigée"
    assert updated.user == "Q"
    assert mgr.last().assistant == "R-corrigée"


def test_replace_last_empty() -> None:
    """replace_last() sur un historique vide renvoie None."""
    mgr = MemoryManager()
    assert mgr.replace_last("R") is None


def test_clear() -> None:
    """clear() efface tout l'historique."""
    mgr = MemoryManager()
    mgr.add(_turn("Q", "R"))
    mgr.add(_turn("Q2", "R2"))
    mgr.clear()
    assert len(mgr) == 0
    assert mgr.last() is None
