"""Core — Boucle de conversation.

Le moteur du chatbot : gère l'interaction entre l'utilisateur,
l'IA, l'historique, la journalisation et les commandes spéciales.
Il n'appelle pas directement l'API LLM : il délègue à llm/client.py.
"""

from __future__ import annotations

from collections.abc import Callable

from chatbot.ai_act.logging import SessionLog
from chatbot.ai_act.oversight import correct, undo
from chatbot.ai_act.transparency import display_transparency_banner
from chatbot.config import Settings
from chatbot.core.history import MemoryManager
from chatbot.data_act.interop import export_to_console
from chatbot.llm.client import TavilyError, ask
from chatbot.rgpd.consent import get_consent


class ConversationEngine:
    """Moteur de conversation interactif.

    :cvar settings: Configuration de la session
    :cvar memory: Gestion de l'historique
    :cvar log: Journal des échanges
    """

    def __init__(
        self,
        settings: Settings | None = None,
        get_input: Callable[[], str] | None = None,
    ) -> None:
        """Initialise le moteur.

        :param settings: Configuration (par défaut : depuis .env)
        :param get_input: Fonction pour lire une saisie utilisateur
                         (par défaut: input() du module builtins)
        """
        self.settings = settings or Settings.from_env()
        self.memory = MemoryManager(
            memory_turns=self.settings.memory_turns,
        )
        self.log = SessionLog()
        self._running = False
        self._get_input = get_input or input

    def start(self) -> None:
        """Démare la session : consentement puis boucle de conversation."""
        if not get_consent():
            print("Session annulée — pas de consentement RGPD.")
            return

        display_transparency_banner()
        self._running = True
        self._loop()

    def _loop(self) -> None:
        """Boucle principale de la conversation."""
        print("  (taper /quit pour quitter, /help pour les commandes)\n")
        total_turns = 0

        while self._running:
            try:
                user_input = self._get_input().strip()
            except (EOFError, KeyboardInterrupt):
                print("\n")
                break

            if not user_input:
                continue

            if user_input == "/quit":
                break
            if user_input == "/help":
                self._print_help()
                continue
            if user_input == "/export":
                export_to_console(self.log)
                continue
            if user_input == "/stats":
                self._print_stats()
                continue
            if user_input == "/undo":
                print(undo(self.memory))
                continue
            if user_input.startswith("/correct "):
                correction = user_input[len("/correct "):]
                print(correct(self.memory, correction))
                continue

            try:
                turn = ask(user_input, self.memory.history, self.settings)
            except TavilyError as err:
                print(f"  [Erreur] {err}")
                continue

            self.memory.add(turn)
            self.log.log_turn(turn)
            total_turns += 1

            print(f"\nChatbot: {turn.assistant}")
            if turn.sources:
                print(f"  Sources: {', '.join(turn.sources)}")
            self._print_stats()
            print()

    def _print_help(self) -> None:
        """Affiche l'aide des commandes."""
        print(
            "  Commandes :\n"
            "    /quit       — Quitter et purger la session\n"
            "    /help       — Afficher cette aide\n"
            "    /export     — Exporter les échanges en JSON (Data Act)\n"
            "    /stats      — Statistiques de la session\n"
            "    /undo       — Annuler la dernière réponse (AI Act)\n"
            "    /correct X  — Remplacer la dernière réponse par X (AI Act)\n",
        )

    def _print_stats(self) -> None:
        """Affiche les statistiques de la session."""
        total = len(self.log)
        sources_count = sum(len(e["sources"]) for e in self.log.entries)
        print(
            f"  [Stats] "
            f"tours: {total} | "
            f"sources: {sources_count} | "
            f"mémoire: {len(self.memory)} / {self.settings.memory_turns}",
        )
