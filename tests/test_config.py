"""Tests pour chatbot/config.py."""

import os
from unittest.mock import patch

from chatbot.config import Settings, load_env


def test_load_env_missing_file() -> None:
    """load_env renvoie un dict vide si le fichier n'existe pas."""
    config = load_env("/non/existant/.env")
    assert config == {}


def test_load_env_reads_keyval(tmp_path: object) -> None:
    """load_env lit les paires clé=valeur d'un fichier .env."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# commentaire ignoré\n"
        "FOO=bar\n"
        'BAZ="quoted value"\n'
        "\n",
        encoding="utf-8",
    )
    config = load_env(str(env_file))
    assert config["FOO"] == "bar"
    assert config["BAZ"] == "quoted value"
    assert "commentaire" not in config


def test_settings_defaults(tmp_path: object) -> None:
    """Settings avec un .env vide a les valeurs par défaut."""
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")

    with patch.dict(os.environ, {}, clear=True):
        settings = Settings.from_env(str(env_file))
        assert settings.tavily_api_key == ""
        assert settings.tavily_max_results == 5
        assert settings.tavily_search_depth == "basic"
        assert settings.log_level == "INFO"
        assert settings.memory_turns == 10


def test_settings_from_env_reads_values(tmp_path: object) -> None:
    """Settings.from_env lit les valeurs du .env."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "TAVILY_API_KEY=my-key\n"
        "TAVILY_MAX_RESULTS=10\n"
        "LOG_LEVEL=DEBUG\n"
        "MEMORY_TURNS=3\n",
        encoding="utf-8",
    )

    with patch.dict(os.environ, {}, clear=True):
        settings = Settings.from_env(str(env_file))
        assert settings.tavily_api_key == "my-key"
        assert settings.tavily_max_results == 10
        assert settings.log_level == "DEBUG"
        assert settings.memory_turns == 3
