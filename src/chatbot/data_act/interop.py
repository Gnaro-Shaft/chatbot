"""Data Act — Interopérabilité et export.

Article 2 et 11 du Data Act : les données doivent être
échangeables dans un format standard et réutilisable.
Le format est JSON standard (RFC 8259), sans chiffrage,
sous licence CC0 (domaine public) sauf données personnelles.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from chatbot.ai_act.logging import SessionLog


def build_export(log: SessionLog, version: str = "1.0") -> dict[str, object]:
    """Construit la structure d'export Data Act.

    :param log: SessionLog de la session
    :param version: Version du schéma d'export
    :return: Dictionnaire prêt à sérialiser en JSON
    """
    return {
        "session_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": version,
        "exchanges": log.entries,
        "license": "CC0",
    }


def export_to_console(log: SessionLog) -> dict[str, object]:
    """Exporte la session en format JSON dans le stdout.

    :param log: SessionLog de la session
    :return: La structure exportée
    """
    export = build_export(log)
    print(json.dumps(export, indent=2, ensure_ascii=False))
    return export


def export_to_file(log: SessionLog, path: str = "chatbot_export.json") -> str:
    """Exporte la session dans un fichier JSON.

    :param log: SessionLog de la session
    :param path: Chemin du fichier de sortie
    :return: Le chemin du fichier écrit
    """
    export = build_export(log)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, ensure_ascii=False)
    return path
