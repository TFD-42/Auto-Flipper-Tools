"""
Wrapper de conversation Ollama avec tool-calling, utilisé pour piloter le
choix du firmware (étape 1) et la navigation modulaire par catégorie
(étape 2, mode 1b uniquement).

Le modèle propose/explique/questionne en langage naturel, mais toute action
sur le filesystem ou le device passe par un tool call structuré exécuté par
du code Python déterministe (jamais du texte libre parsé à l'aveugle).

Nécessite un modèle Ollama qui supporte le tool-calling (ex: qwen2.5,
llama3.1, mistral-nemo — voir https://ollama.com/search?c=tools).
"""

from __future__ import annotations

import json
import logging
from typing import Callable, Optional

import requests

logger = logging.getLogger(__name__)

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen2.5:7b"


class OllamaUnavailable(RuntimeError):
    pass


def chat_with_tools(
    model: str,
    system_prompt: str,
    user_message: str,
    history: Optional[list[dict]] = None,
    tools: Optional[list[dict]] = None,
    on_tool_call: Optional[Callable[[str, dict], str]] = None,
) -> tuple[str, list[dict]]:
    """Envoie un message à Ollama, exécute les tool calls demandés via on_tool_call,
    et retourne (réponse texte finale, historique mis à jour).
    """
    messages = list(history or [])
    if not messages:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    payload = {"model": model, "messages": messages, "stream": False}
    if tools:
        payload["tools"] = tools

    try:
        resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=120)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        raise OllamaUnavailable(
            "Ollama n'est pas accessible sur localhost:11434 — "
            "installe-le depuis https://ollama.ai et lance-le (`ollama serve`)."
        ) from e

    data = resp.json()
    message = data["message"]
    messages.append(message)

    tool_calls = message.get("tool_calls") or []
    for call in tool_calls:
        fn_name = call["function"]["name"]
        fn_args = call["function"].get("arguments", {})
        logger.info("Tool call: %s(%s)", fn_name, fn_args)

        if on_tool_call is None:
            result = f"Erreur: aucun handler configuré pour {fn_name}"
        else:
            try:
                result = on_tool_call(fn_name, fn_args)
            except (
                Exception
            ) as e:  # noqa: BLE001 - on renvoie l'erreur au modèle, pas de crash
                result = f"Erreur lors de l'exécution de {fn_name}: {e}"

        messages.append({"role": "tool", "content": str(result)})

    if tool_calls:
        # Redemande une réponse texte au modèle maintenant qu'il a les résultats des tools
        follow_up = requests.post(
            OLLAMA_CHAT_URL,
            json={"model": model, "messages": messages, "stream": False},
            timeout=120,
        )
        follow_up.raise_for_status()
        final_message = follow_up.json()["message"]
        messages.append(final_message)
        return final_message.get("content", ""), messages

    return message.get("content", ""), messages
