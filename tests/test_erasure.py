"""Tests pour rgpd/erasure.py."""

from chatbot.core.history import MemoryManager
from chatbot.core.prompt import ConversationTurn
from chatbot.rgpd.erasure import purge_session
from chatbot.ai_act.logging import SessionLog


def test_purge_session_clears_everything() -> None:
    """purge_session efface memory et log, renvoie True."""
    memory = MemoryManager()
    log = SessionLog()

    memory.add(ConversationTurn(user="Q", assistant="R"))
    log.log_turn(ConversationTurn(user="Q", assistant="R"))

    assert len(memory) == 1
    assert len(log) == 1

    result = purge_session(memory, log)
    assert result is True
    assert len(memory) == 0
    assert len(log) == 0


def test_purge_session_empty_inputs() -> None:
    """purge_session sur des structures vides renvoie True."""
    memory = MemoryManager()
    log = SessionLog()
    assert purge_session(memory, log) is True


def test_purge_session_idempotent() -> None:
    """purge_session deux fois de suite renvoie True."""
    memory = MemoryManager()
    log = SessionLog()
    memory.add(ConversationTurn(user="Q", assistant="R"))
    log.log_turn(ConversationTurn(user="Q", assistant="R"))

    assert purge_session(memory, log) is True
    assert purge_session(memory, log) is True
