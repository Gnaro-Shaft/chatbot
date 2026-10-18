"""RGPD — Droit à l'oubli.

Article 17 du RGPD : le donnée personnelle doit être
effacée à la fin de la session. Ce module centralise
la purge de toutes les structures de mémoire.
"""

from __future__ import annotations

from chatbot.ai_act.logging import SessionLog
from chatbot.core.history import MemoryManager


def purge_session(memory: MemoryManager, log: SessionLog) -> bool:
    """Efface tout l'historique et le journal mémoire.

    Implémenté l'effacement complet requis par l'article 17 du RGPD.
    Renvoie True si la purge a réussi.

    :param memory: MemoryManager de la session
    :param log: SessionLog de la session
    :return: True si la purge est complète
    """
    memory.clear()
    log.clear()
    return len(memory) == 0 and len(log) == 0
