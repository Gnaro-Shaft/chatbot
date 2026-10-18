"""LLM — Client pour l'API Tavily."""

from __future__ import annotations

import logging
import time

import requests

from chatbot.config import Settings
from chatbot.core.prompt import ConversationTurn, build_prompt

logger = logging.getLogger(__name__)

TAVILY_ENDPOINT = "https://api.tavily.com/search"


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
    """Envoie une question au LLM via Tavily et renvoie la réponse.

    :param question: Message de l'utilisateur
    :param history: Historique des tours précédents
    :param settings: Configuration (clé API, profondeur, etc.)
    :return: Un ConversationTurn contenant la réponse et les sources
    """
    messages = build_prompt(history, question)

    last_user_msg = messages[-1]["content"]
    context = "\n".join(
        f"{turn.user} → {turn.assistant}"
        for turn in history
    ) if history else ""

    full_query = f"[Contexte]\n{context}\n\n[Question]\n{last_user_msg}".strip()

    payload: dict[str, object] = {
        "api_key": settings.tavily_api_key,
        "query": full_query,
        "search_depth": settings.tavily_search_depth,
        "max_results": settings.tavily_max_results,
        "include_answer": True,
    }

    logger.info("appel Tavily pour : %s", question[:80])
    start = time.perf_counter()

    response = requests.post(
        TAVILY_ENDPOINT,
        json=payload,
        timeout=30,
    )
    elapsed = time.perf_counter() - start
    logger.info("Tavily réponse en %.2fs (status %d)", elapsed, response.status_code)

    if response.status_code == 401:
        raise TavilyError(401, "Clé API invalide ou expirée")
    if response.status_code != 200:
        raise TavilyError(response.status_code, response.text[:200])

    data: dict[str, object] = response.json()

    answer: str = data.get("answer") or data.get("summary", "")
    results = data.get("results", [])
    sources: list[str] = [r.get("url", "") for r in results if r.get("url")]

    # Si la réponse est vide, on construit un fallback à partir des résultats
    if not answer and results:
        answer = "\n".join(f"- {r.get('title', '')} : {r.get('content', '')[:150]}" for r in results[:3])

    logger.info("réponse générée (%d sources)", len(sources))
    return ConversationTurn(user=question, assistant=answer, sources=sources)
