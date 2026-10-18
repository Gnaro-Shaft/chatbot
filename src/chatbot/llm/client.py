"""LLM — Client pour l'API Tavily.

Tavily est utilisé comme moteur de recherche web.
La langue des résultats est forcée en français via `language` / `filter_by_language`.
Les réponses sont construites à partir des résultats FR — pas via include_answer
(comme l'`answer` de Tavily suit la langue de la question, pas des instructions FR).
"""

from __future__ import annotations

import logging
import re
import time

import requests

from chatbot.config import Settings
from chatbot.core.prompt import ConversationTurn

logger = logging.getLogger(__name__)

TAVILY_ENDPOINT = "https://api.tavily.com/search"

# Tags HTML / Markdown courants à retirer des snippets
_TAG_RE = re.compile(r"<[^>]+>|\*+|#+|^#+ .*", re.MULTILINE)


class TavilyError(Exception):
    """Erreur renvoyée par l'API Tavily."""

    def __init__(self, status: int, detail: str) -> None:
        """Initialise l'erreur Tavily.

        :param status: Code HTTP
        :param detail: Détail de l'erreur
        """
        self.status = status
        super().__init__(f"Tavily {status} : {detail}")


def ask(
    question: str,
    history: list[ConversationTurn],
    settings: Settings,
) -> ConversationTurn:
    """Envoie une question à Tavily et renvoie une ConversationTurn.

    La question seule est envoyée au moteur de recherche (pas le contexte
    conversationnel qui polluerait les résultats). Le contexte est
    réutilisé uniquement pour construire une requête plus riche.

    :param question: Message de l'utilisateur actuel
    :param history: Historique des tours précédents
    :param settings: Configuration (clé API, profondeur, langue, etc.)
    :return: Un ConversationTurn (question / réponse / sources)
    """
    payload: dict[str, object] = {
        "api_key": settings.tavily_api_key,
        # Préfixe une instruction FR pour que l'answer soit toujours en français
        "query": f"Réponds en français : {question}",
        "search_depth": settings.tavily_search_depth,
        "max_results": settings.tavily_max_results,
        "include_answer": True,
        "include_raw_content": False,
        "language": "fr",
    }

    logger.info("appel Tavily pour : %s", question[:80])
    start = time.perf_counter()

    response = requests.post(TAVILY_ENDPOINT, json=payload, timeout=30)

    elapsed = time.perf_counter() - start
    logger.info("Tavily réponse en %.2fs (status %d)", elapsed, response.status_code)

    if response.status_code == 401:
        raise TavilyError(401, "Clé API invalide ou expirée")
    if response.status_code != 200:
        raise TavilyError(response.status_code, response.text[:200])

    data: dict[str, object] = response.json()
    results: list[dict] = data.get("results", [])
    sources: list[str] = [r.get("url", "") for r in results if r.get("url")]

    # On préfère l'answer de Tavily (LLM) s'il est non vide
    raw_answer: str = (data.get("answer") or "").strip()
    answer = raw_answer if raw_answer else _build_answer_from_results(results)

    logger.info("réponse construite à partir de %d sources", len(sources))
    return ConversationTurn(user=question, assistant=answer, sources=sources)


def _clean_content(raw: str, max_len: int = 250) -> str:
    """Nettoie un contenu brut des tags HTML/Markdown.

    :param raw: Contenu brut d'un résultat Tavily
    :param max_len: Longueur maximale
    :return: Texte nettoyé
    """
    # Retire tags HTML, markdown headings / bold
    cleaned = _TAG_RE.sub("", raw)
    # Éspace multiples
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:max_len]


def _build_answer_from_results(results: list[dict]) -> str:
    """Construit une réponse de synthèse en français.

    :param results: Liste de résultats Tavily
    :return: Texte de synthèse en français
    """
    if not results:
        return "Je n'ai pas trouvé d'information sur ce sujet en ligne."

    lines: list[str] = ["Voici ce que les sources disent :\n"]
    for r in results[:5]:
        title = r.get("title", "Sans titre")
        content = _clean_content(r.get("content", ""))
        lines.append(f"• {title}")
        if content:
            lines.append(f"  {content}")
        lines.append("")  # ligne vide entre résultats

    return "\n".join(lines).strip()
