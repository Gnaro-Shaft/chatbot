"""Tests pour data_act/interop.py et ai_act/logging.py."""

import json
from unittest.mock import patch

from chatbot.ai_act.logging import LoggedTurn, SessionLog
from chatbot.core.prompt import ConversationTurn
from chatbot.data_act.interop import build_export, export_to_console, export_to_file


def _make_log() -> SessionLog:
    log = SessionLog()
    log.log_turn(ConversationTurn(user="Q1", assistant="R1", sources=["https://a.fr"]))
    log.log_turn(ConversationTurn(user="Q2", assistant="R2", sources=[]))
    return log


def test_log_turn_returns_logged_turn() -> None:
    """log_turn renvoie un LoggedTurn avec id et timestamp."""
    log = SessionLog()
    entry = log.log_turn(ConversationTurn(user="Q", assistant="R"))
    assert isinstance(entry, LoggedTurn)
    assert len(entry.id) > 0
    assert "T" in entry.timestamp  # ISO 8601
    assert entry.turn.user == "Q"
    assert len(log) == 1


def test_log_entries_format() -> None:
    """entries() renvoie une liste de dicts exportables."""
    log = _make_log()
    entries = log.entries
    assert len(entries) == 2
    assert entries[0]["input"] == "Q1"
    assert entries[0]["output"] == "R1"
    assert entries[0]["sources"] == ["https://a.fr"]
    assert entries[0]["model"] == "tavily-research"


def test_log_clear() -> None:
    """clear() efface le journal."""
    log = _make_log()
    log.clear()
    assert len(log) == 0


def test_build_export_structure() -> None:
    """build_export renvoie la structure attendue Data Act."""
    log = _make_log()
    export = build_export(log)
    assert "session_id" in export
    assert "timestamp" in export
    assert "exchanges" in export
    assert "version" in export
    assert "license" in export
    assert export["license"] == "CC0"
    assert len(export["exchanges"]) == 2  # type: ignore[operator]


def test_export_to_console_prints_json() -> None:
    """export_to_console affiche du JSON dans le stdout."""
    log = _make_log()
    with patch("builtins.print") as mock_print:
        export_to_console(log)
        called = mock_print.call_args_list[0].args[0]
        parsed = json.loads(called)
        assert "exchanges" in parsed


def test_export_to_file(tmp_path: object) -> None:
    """export_to_file écrit un fichier JSON valide."""
    log = _make_log()
    path = tmp_path / "export.json"
    written_path = export_to_file(log, str(path))
    with open(written_path, encoding="utf-8") as f:
        data = json.load(f)
    assert "exchanges" in data
    assert len(data["exchanges"]) == 2
