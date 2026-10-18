"""Tests pour core/prompt.py."""

from chatbot.core.prompt import SYSTEM_PROMPT, ConversationTurn, build_prompt


def test_conversation_turn_defaults() -> None:
    """ConversationTurn sans sources a une liste vide."""
    turn = ConversationTurn(user="bonjour", assistant="salut")
    assert turn.user == "bonjour"
    assert turn.assistant == "salut"
    assert turn.sources == []


def test_conversation_turn_with_sources() -> None:
    """ConversationTurn avec sources."""
    turn = ConversationTurn(
        user="actualité ?",
        assistant="...",
        sources=["https://a.fr", "https://b.fr"],
    )
    assert turn.sources == ["https://a.fr", "https://b.fr"]


def test_build_prompt_empty_history() -> None:
    """Un prompt sans historique = system + user."""
    msgs = build_prompt([], "bonjour")
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == SYSTEM_PROMPT
    assert msgs[1] == {"role": "user", "content": "bonjour"}


def test_build_prompt_with_history() -> None:
    """Un prompt avec historique inclut les tours précédents."""
    history = [
        ConversationTurn(user="Q1", assistant="R1"),
        ConversationTurn(user="Q2", assistant="R2", sources=["https://x.fr"]),
    ]
    msgs = build_prompt(history, "Q3")

    # system + (user/assistant x 2) + user = 6 messages
    assert len(msgs) == 6
    assert msgs[0]["role"] == "system"

    # Tour 1
    assert msgs[1] == {"role": "user", "content": "Q1"}
    assert msgs[2] == {"role": "assistant", "content": "R1"}

    # Tour 2 avec sources
    assert msgs[3] == {"role": "user", "content": "Q2"}
    assert "Sources : https://x.fr" in msgs[4]["content"]

    # Nouveau message
    assert msgs[5] == {"role": "user", "content": "Q3"}


def test_build_prompt_custom_system() -> None:
    """Un prompt système custom est respecté."""
    msgs = build_prompt([], "hello", system="custom system prompt")
    assert msgs[0]["content"] == "custom system prompt"


def test_build_prompt_multiple_sources_joined() -> None:
    """Plusieurs sources sont jointes par virgule."""
    turn = ConversationTurn(
        user="Q", assistant="R",
        sources=["https://a.fr", "https://b.fr"],
    )
    msgs = build_prompt([turn], "N")
    assistant_msg = msgs[2]
    assert "https://a.fr, https://b.fr" in assistant_msg["content"]
