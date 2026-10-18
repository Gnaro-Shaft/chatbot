"""RGPD — Consentement explicite.

Implémenté l'article 6 du RGPD : base légale par consentement.
Le consentement doit être explicite, informé, et rétractable.
"""

from __future__ import annotations

CONSENT_TEXT = """
╔══════════════════════════════════════════════════════════════╗
║  CONSENTEMENT RGPD                                           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Ce chatbot utilise une IA générative pour répondre à vos    ║
║  questions.                                                   ║
║                                                              ║
║  Vos échanges sont conservés uniquement en mémoire pendant    ║
║  la durée de la session. Aucune donnée n'est enregistrée      ║
║  sur un serveur ni transmise à un tiers.                     ║
║                                                              ║
║  À la fermeture de la session, tous les échanges sont         ║
║  supprimés (droit à l'oubli, article 17 RGPD).              ║
║                                                              ║
║  Vous pouvez en tout moment :                                ║
║    • exporter vos échanges en format JSON (/export)           ║
║    • corriger ou annuler une réponse (/undo, /correct)        ║
║    • quitter à tout moment (/quit)                            ║
║                                                              ║
║  Continuer implique votre consentement à ce traitement.       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def display_consent() -> None:
    """Affiche le texte de consentement RGPD.

    :return: None
    """
    print(CONSENT_TEXT)


def get_consent() -> bool:
    """Demande le consentement utilisateur.

    Le consentement n'est pas enregistré (pas de persistance).
    L'absence de réponse (EOF, Ctrl+C) revient à un "non".

    :return: True si l'utilisateur a accepté, False sinon
    """
    display_consent()
    try:
        answer = input("  Consent ? [o/n] : ").strip().lower()
        return answer.startswith("o") or answer == ""
    except (EOFError, KeyboardInterrupt):
        return False
