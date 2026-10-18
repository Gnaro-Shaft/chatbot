"""AI Act — Transparence.

Article 50 du AI Act : l'utilisateur doit être informé
qu'il interagit avec un système d'IA.
Ce module affiche la bannière au démarrage de chaque session.
"""

from __future__ import annotations

TAKEOVER_BANNER = """
┌─────────────────────────────────────────────────────────────┐
│  ⚠️  TRANSPARENCE IA (AI Act Article 50)                     │
│  Vous interagissez avec un assistant IA.                   │
│  Les réponses peuvent contenir des inexactitudes.            │
│  Commandes : /undo / /correct <texte> / /export / /quit      │
└─────────────────────────────────────────────────────────────┘
"""


def display_transparency_banner() -> None:
    """Affiche la bannière de transparence IA.

    :return: None
    """
    print(TAKEOVER_BANNER)
