"""Config — Charge les variables d'environnement depuis le fichier .env."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def load_env(env_file: str = ".env") -> dict[str, str]:
    """Charge un fichier .env dans un dictionnaire.

    :param env_file: Chemin vers le fichier .env
    :return: Dictionnaire des variables d'environnement
    """
    config: dict[str, str] = {}
    path = Path(env_file)
    if not path.exists():
        return config

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, val = line.partition("=")
        config[key.strip()] = val.strip().strip('"\'')

    return config


@dataclass(frozen=True)
class Settings:
    """Paramètres de configuration du chatbot.

    :cvar tavily_api_key: Clé API Tavily
    :cvar tavily_max_results: Nombre de résultats par recherche
    :cvar tavily_search_depth: Profondeur de recherche (basic/advanced)
    :cvar log_level: Niveau de log
    :cvar memory_turns: Nombre de tours de conversation à retenir
    """

    tavily_api_key: str = ""
    tavily_max_results: int = 5
    tavily_search_depth: str = "basic"
    log_level: str = "INFO"
    memory_turns: int = 10

    @classmethod
    def from_env(cls, env_file: str = ".env") -> "Settings":
        """Crée une instance de Settings depuis un fichier .env.

        :param env_file: Chemin du fichier .env
        :return: Instance de Settings
        """
        raw = load_env(env_file)
        # Fusion : environnement système a la priorité
        merged: dict[str, Any] = {**raw, **dict(os.environ)}

        return cls(
            tavily_api_key=merged.get("TAVILY_API_KEY", ""),
            tavily_max_results=int(merged.get("TAVILY_MAX_RESULTS", "5")),
            tavily_search_depth=merged.get("TAVILY_SEARCH_DEPTH", "basic"),
            log_level=merged.get("LOG_LEVEL", "INFO"),
            memory_turns=int(merged.get("MEMORY_TURNS", "10")),
        )
