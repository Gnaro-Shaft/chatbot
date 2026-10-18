"""LLM — Client pour l'API Tavily.

Tavily est utilisé comme moteur de recherche web.
La langue des résultats est poussée en français via `language: fr`.
Si l'answer de Tavily revient en anglais (question en anglais),
elle est traduite via MyMemory avant d'être renvoyée.
"""

from __future__ import annotations

import logging
import re
import time

import requests

from chatbot.ai_act.translate import translate_to_french
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

    La question est traduite en français avant d'être envoyée au moteur de
    recherche pour améliorer la qualité des résultats FR. L'answer de Tavily
    est traduite en français si elle ne l'est pas déjà.

    :param question: Message de l'utilisateur (n'importe quelle langue)
    :param history: Historique des tours précédents
    :param settings: Configuration (clé API, profondeur, langue, etc.)
    :return: Un ConversationTurn (question / réponse FR / sources)
    """
    # On traduit la question en FR pour améliorer le classement des résultats
    fr_question = translate_to_french(question)

    payload: dict[str, object] = {
        "api_key": settings.tavily_api_key,
        "query": fr_question,
        "search_depth": settings.tavily_search_depth,
        "max_results": settings.tavily_max_results,
        "include_answer": True,
        "include_raw_content": False,
        "language": "fr",
    }

    logger.info("appel Tavily pour : %s", fr_question[:80])
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

    raw_answer: str = (data.get("answer") or "").strip()
    if raw_answer:
        # La réponse de Tavily peut être en anglais → on force le français
        answer = translate_to_french(raw_answer)
    else:
        answer = _build_answer_from_results(results)

    logger.info("réponse finale traduite en français (%d sources)", len(sources))
    return ConversationTurn(user=question, assistant=answer, sources=sources)


def _clean_content(raw: str, max_len: int = 250) -> str:
    """Nettoie un contenu brut des tags HTML/Markdown.

    :param raw: Contenu brut d'un résultat Tavily
    :param max_len: Longueur maximale
    :return: Texte nettoyé
    """
    cleaned = _TAG_RE.sub("", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:max_len]


def _build_answer_from_results(results: list[dict]) -> str:
    """Construit une réponse en français à partir des résultats.

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
        lines.append("")

    return "\n".join(lines).strip()
