"""AI Act — Supervision humaine.

Article 14 du AI Act : l'utilisateur doit pouvoir
annuler une réponse ou corriger la dernière réponse.
Ce module gèrent les commandes /undo et /correct.
"""

from __future__ import annotations

from chatbot.core.history import MemoryManager


def undo(manager: MemoryManager) -> str:
    """Annule le dernier tour de conversation.

    :param manager: MemoryManager de la session
    :return: Message de confirmation ou d'information
    """
    removed = manager.remove_last()
    if removed is None:
        return "Aucun tour à annuler."
    return f"Réponse annulée : « {removed.assistant[:60]}… »"


def correct(manager: MemoryManager, new_answer: str) -> str:
    """Corrige la dernière réponse de l'assistant.

    :param manager: MemoryManager de la session
    :param new_answer: Nouvelle réponse fournie par l'humain
    :return: Message de confirmation
    """
    updated = manager.replace_last(new_answer)
    if updated is None:
        return "Aucun tour à corriger."
    return f"Réponse corrigée par l'humain : « {new_answer[:60]}… »"
