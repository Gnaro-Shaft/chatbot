"""UI — Interface terminal avec prompt_toolkit.

Fournit un prompt coloré, une auto-complétion des commandes,
un historique en mémoire et un affichage structuré.
"""

from __future__ import annotations

from dataclasses import dataclass

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import InMemoryHistory

# Auto-complétion à la Tab
COMPLETER = WordCompleter(
    [
        "/quit",
        "/help",
        "/export",
        "/stats",
        "/undo",
        "/correct",
    ],
)

# Prompt "Vous: > " en cyan + vert
PROMPT = ANSI("\033[36mVous:\033[0m \033[32m>\033[0m ")

# Bannière
BANNER = (
    "\033[44;37m  "
    "Chatbot CLI  —  RGPD / AI Act / Data Act  "
    "\033[0m\n"
)

# Aide
HELP_TEXT = (
    "\033[1mCommandes :\033[0m\n"
    "  \033[33m/quit\033[0m       — Quitter et purger la session\n"
    "  \033[33m/help\033[0m       — Afficher l'aide\n"
    "  \033[33m/export\033[0m     — Export JSON (Data Act)\n"
    "  \033[33m/stats\033[0m      — Statistiques de la session\n"
    "  \033[33m/undo\033[0m      — Annuler la dernière réponse (AI Act)\n"
    "  \033[33m/correct X\033[0m  — Corriger la dernière réponse\n"
)


@dataclass
class PromptUI:
    """Interface utilisateur basée sur prompt_toolkit.

    :cvar session: Session prompt_toolkit avec historique
    """

    session: PromptSession = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.session is None:
            self.session = PromptSession(
                history=InMemoryHistory(),
                completer=COMPLETER,
            )

    def user_input(self) -> str:
        """Lit une ligne de l'utilisateur.

        :return: La saisie (stripped)
        """
        return self.session.prompt(PROMPT).strip()

    def info(self, msg: str) -> None:
        """Affiche un message d'information (cyan)."""
        print(f"\033[36m{msg}\033[0m")

    def error(self, msg: str) -> None:
        """Affiche un message d'erreur (rouge)."""
        print(f"\033[31m[Erreur]\033[0m \033[31m{msg}\033[0m")

    def success(self, msg: str) -> None:
        """Affiche un message de succès (vert)."""
        print(f"\033[32m{msg}\033[0m")

    def chatbot_msg(self, msg: str) -> None:
        """Affiche un message du chatbot (bleu clair)."""
        print(f"\033[94mChatbot:\033[0m  {msg}")

    def sources(self, urls: list[str]) -> None:
        """Affiche les sources (jaune, italique)."""
        print(f"\033[33m  Sources:\033[0m  {' | '.join(urls)}")

    def stats_line(
        self, turns: int, sources: int, memory_max: int
    ) -> None:
        """Affiche la ligne de statistiques (gris)."""
        print(
            f"\033[90m  [Stats] tours: {turns} | "
            f"sources: {sources} | "
            f"mémoire: {min(turns, memory_max)}/{memory_max}\033[0m",
        )

    def banner(self) -> None:
        """Affiche la bannière du chatbot."""
        import sys

        sys.stdout.write(BANNER + "\n")

    def help(self) -> None:
        """Affiche l'aide des commandes."""
        import sys

        sys.stdout.write(HELP_TEXT + "\n")
