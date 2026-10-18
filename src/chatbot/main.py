"""Point d'entrée du chatbot.

Démare la session de conversation avec interface TUI (prompt_toolkit).
Les données ne sont stockées qu'en mémoire (pas de persistence disque).
"""

from __future__ import annotations

import logging

from chatbot.config import Settings
from chatbot.core.engine import ConversationEngine
from chatbot.ui import PromptUI


def main() -> None:
    """Point d'entrée du chatbot.

    :return: None
    """
    settings = Settings.from_env()
    logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))

    ui = PromptUI()
    ui.banner()

    engine = ConversationEngine(
        settings=settings,
        get_input=lambda: ui.user_input(),
    )
    engine.start()

    # Purge RGPD : tout est effacé à la fin de la session
    engine.memory.clear()
    engine.log.clear()
    ui.success("  Session terminée. Toutes les données ont été purguées.")


if __name__ == "__main__":
    main()
