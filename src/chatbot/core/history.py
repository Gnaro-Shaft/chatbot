"""Core — Mémoire de conversation en session.

Gère l'historique des échanges. Aucune persistance :
les données ne vivent que pendant la durée de la session.
À la fin, l'objet doit être explicitement effacé
(voir rgpd/erasure.py).
"""

from __future__ import annotations

from chatbot.core.prompt import ConversationTurn


class MemoryManager:
    """Gère la fenêtre glissante de l'historique de conversation.

    :cvar memory_turns: Nombre maximum de tours à conserver
    """

    def __init__(self, memory_turns: int = 10) -> None:
        """Initialise le MemoryManager.

        :param memory_turns: Nombre de tours à retenir
        """
        self._history: list[ConversationTurn] = []
        self.memory_turns = memory_turns

    @property
    def history(self) -> list[ConversationTurn]:
        """Renvoie la liste (non mutable) de l'historique.

        :return: Historique tronqué à memory_turns
        """
        return self._history[-self.memory_turns :]

    def add(self, turn: ConversationTurn) -> None:
        """Ajoute un tour à l'historique.

        :param turn: Tour de conversation
        """
        self._history.append(turn)

    def last(self) -> ConversationTurn | None:
        """Renvoie le dernier tour, ou None si vide.

        :return: Dernier tour ou None
        """
        return self._history[-1] if self._history else None

    def remove_last(self) -> ConversationTurn | None:
        """Supprime et renvoie le dernier tour (pour /undo).

        :return: Le tour supprimé, ou None
        """
        return self._history.pop() if self._history else None

    def replace_last(self, new_answer: str) -> ConversationTurn | None:
        """Remplace la réponse du dernier tour (pour /correct).

        :param new_answer: Nouvelle réponse de l'assistant
        :return: Le tour modifié, ou None
        """
        if not self._history:
            return None
        last = self._history.pop()
        updated = ConversationTurn(
            user=last.user,
            assistant=new_answer,
            sources=last.sources,
        )
        self._history.append(updated)
        return updated

    def clear(self) -> None:
        """Efface tout l'historique (après consentement, en fin de session)."""
        self._history.clear()

    def __len__(self) -> int:
        """Réenvoie le nombre de tours dans l'historique."""
        return len(self._history)
