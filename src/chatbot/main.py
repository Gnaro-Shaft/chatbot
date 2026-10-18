"""Point d'entrée du chatbot.

Démare la conversation. Les données ne sont stockées qu'en mémoire
(pas de persistence, pas de logs disque).
"""

from __future__ import annotations

import logging

from chatbot.config import Settings
from chatbot.core.engine import ConversationEngine


def main() -> None:
    """Point d'entrée du chatbot.

    :return: None
    """
    settings = Settings.from_env()
    logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))

    engine = ConversationEngine(settings)
    engine.start()

    # Purge RGPD : tout est effacé à la fin de la session
    engine.memory.clear()
    engine.log.clear()
    print("  Session terminée. Toutes les données ont été purguées.")


if __name__ == "__main__":
    main()
