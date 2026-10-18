"""AI Act — Traduction et détection de langue.

Permet au chatbot de répondre TOUJOURS en français, même si la question
ou la réponse de l'IA est dans une autre langue.

Le module utilise l'API MyMemory (gratuit, sans clé) pour la traduction.
Détection de langue via un comptage de caractères accentués (heuristique simple).
"""

from __future__ import annotations

import logging
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

# Cache en mémoire — effacé à la fin de la session (RGPD Art. 17)
_MEM_CACHE: dict[str, str] = {}

# Lettres avec accent propre au français
_ACCENTS = set("àâéèêëîïôûüÿçàÈÊÎÏÔÛÜÇ")

# Stopwords françaises (un sous-ensemble représentatif)
_FR_STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "et", "ou", "mais",
    "en", "de", "du", "au", "aux", "ceci", "cela", "ces", "cet",
    "cette", "son", "sa", "ses", "leur", "leurs", "mon", "ma",
    "mes", "nous", "vous", "ils", "elles", "être", "avoir",
    "faire", "aller", "dire", "voir", "venir",
}


def is_french(text: str) -> bool:
    """Détermine si un texte est probablement en français.

    Utilise deux signaux :
    1. Nombre de caractères accentués (≥2 = probablement FR)
    2. Fraction de stopwords françaises (≥20 % = probablement FR)

    :param text: Texte à tester
    :return: True si le texte ressemble au français
    """
    if not text.strip():
        return False

    # Signal 1 : caractères accentués (1 seul suffit pour un texte court)
    accented = sum(1 for c in text if c in _ACCENTS)
    if accented >= 1:
        return True

    # Signal 2 : stopwords
    words = text.lower().replace(".", " ").replace(",", " ").split()
    if not words:
        return False
    fr_words = sum(1 for w in words if w in _FR_STOPWORDS)
    ratio = fr_words / len(words)
    return ratio >= 0.20


def translate_to_french(text: str) -> str:
    """Traduit un texte en français via MyMemory si nécessaire.

    :param text: Texte source (toute langue)
    :return: Texte en français (traduit ou identique si déjà FR)
    """
    if not text.strip():
        return text
    if is_french(text):
        return text

    key = text.strip()[:100]
    if key in _MEM_CACHE:
        logger.info("traduction en cache : '%s'…", key[:50])
        return _MEM_CACHE[key]

    translated = _mymemory_translate(text)
    if translated:
        _MEM_CACHE[key] = translated
        logger.info("traduction ajoutée au cache (%d entrées)", len(_MEM_CACHE))
        return translated

    logger.warning("traduction échouée, retour du texte original")
    return text  # fallback : on garde le texte d'origine


def _mymemory_translate(text: str, max_chars: int = 500) -> str:
    """Appelle MyMemory pour traduire en français.

    MyMemory limite les requêtes à 500 caractères.
    On traduit les 500 premiers caractères maximum.

    :param text: Texte à traduire
    :param max_chars: Limite de la requête
    :return: Texte traduit, ou chaîne vide si échec
    """
    snippet = text[:max_chars]
    url = f"https://api.mymemory.translated.net/get?q={quote(snippet)}&langpair=en|fr"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        translated = data.get("responseData", {}).get("translatedText", "").strip()
        return translated
    except Exception as e:  # noqa: BLE001 — tout retour du texte d'origine si échec
        logger.error("MyMemory : %s — retour texte original", e)
        return ""
