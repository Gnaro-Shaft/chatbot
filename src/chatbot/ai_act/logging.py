"""AI Act — Journalisation des échanges.

Article 10 du AI Act : les données utilisées et produites
par le système doivent être traçables pour un audit ultérieur.
La journalisation est effectuée en mémoire (pas de fichier
persistant, conformément au RGPD).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from chatbot.core.prompt import ConversationTurn


@dataclass
class LoggedTurn:
    """Un tour de conversation journalisé.

    :cvar id: Identifiant unique (UUID v4)
    :cvar timestamp: Horodatage ISO 8601 UTC
    :cvar turn: Le ConversationTurn original
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    turn: ConversationTurn = field(  # type: ignore[assignment]
        default_factory=lambda: ConversationTurn(user="", assistant=""),
    )


class SessionLog:
    """Journal des échanges de la session.

    Ne persiste rien : les logs sont en mémoire uniquement.
    Peut être exporté via data_act/interop.py.
    """

    def __init__(self) -> None:
        """Initialise un journal vide."""
        self._entries: list[LoggedTurn] = []

    def log_turn(self, turn: ConversationTurn) -> LoggedTurn:
        """Enregistre un tour dans le journal.

        :param turn: Le tour à journaliser
        :return: L'entrée journalisée
        """
        entry = LoggedTurn(turn=turn)
        self._entries.append(entry)
        return entry

    @property
    def entries(self) -> list[dict[str, object]]:
        """Renvoie les entrées au format exportable Data Act.

        :return: Liste de dicts standardisés
        """
        return [
            {
                "id": e.id,
                "timestamp": e.timestamp,
                "input": e.turn.user,
                "output": e.turn.assistant,
                "sources": e.turn.sources,
                "model": "tavily-research",
            }
            for e in self._entries
        ]

    def clear(self) -> None:
        """Efface le journal (droit à l'oubli)."""
        self._entries.clear()

    def __len__(self) -> int:
        """Nombre d'entrées journalisées."""
        return len(self._entries)
