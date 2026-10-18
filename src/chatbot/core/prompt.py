"""Core — Construction du prompt système.

Chaque échange avec le LLM est construit à partir d'un prompt système
fixe + l'historique de conversation. Ce module gère l'assemblage.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SYSTEM_PROMPT = """Tu es un assistant conversationnel bienveillant
et factuel.

Règles :
- Réponds en français de manière claire et concise
- Cite les sources quand tu te bases sur une recherche
- Admets ce que tu ne sais pas
- Ne fabrique jamais d'information (zéro hallucination)

Les réponses sont générées par une IA et peuvent contenir des erreurs.
L'utilisateur reste en contrôle de la conversation.
"""


@dataclass
class ConversationTurn:
    """Un tour de conversation (une demande + une réponse).

    :cvar user: Message de l'utilisateur
    :cvar assistant: Réponse de l'assistant
    :cvar sources: URLs des sources éventuelles
    """

    user: str
    assistant: str
    sources: list[str] = field(default_factory=list)


def build_prompt(
    history: list[ConversationTurn],
    new_message: str,
    system: str = SYSTEM_PROMPT,
) -> list[dict[str, str]]:
    """Construit la séquence de messages à envoyer au LLM.

    :param history: Historique des tours précédents
    :param new_message: Nouvel message de l'utilisateur
    :param system: Prompt système
    :return: Liste de messages formatés pour l'API (role/content)
    """
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system},
    ]

    for turn in history:
        content = turn.assistant
        if turn.sources:
            srcs = ", ".join(turn.sources)
            content += f"\n\nSources : {srcs}"
        messages.append({"role": "user", "content": turn.user})
        messages.append({"role": "assistant", "content": content})

    messages.append({"role": "user", "content": new_message})

    return messages
