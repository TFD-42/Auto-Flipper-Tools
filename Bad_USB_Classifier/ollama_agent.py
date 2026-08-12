"""
Ollama chat wrapper with tool-calling, used by payload_setup_agent.py's
Ollama fallback (and by classify_badusb.py's plain classification calls).

The model proposes/explains/asks in natural language, but any action on the
filesystem goes through a structured tool call executed by deterministic
Python code (never blindly-parsed free text).

Requires an Ollama model that supports tool-calling (e.g. qwen2.5,
llama3.1, mistral-nemo — see https://ollama.com/search?c=tools).
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
    """Sends a message to Ollama, executes any requested tool calls via
    on_tool_call, and returns (final text reply, updated history).
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
            "Ollama isn't reachable on localhost:11434 — "
            "install it from https://ollama.ai and start it (`ollama serve`)."
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
            result = f"Error: no handler configured for {fn_name}"
        else:
            try:
                result = on_tool_call(fn_name, fn_args)
            except (
                Exception
            ) as e:  # noqa: BLE001 - surface the error to the model instead of crashing
                result = f"Error while running {fn_name}: {e}"

        messages.append({"role": "tool", "content": str(result)})

    if tool_calls:
        # Ask the model for a text reply now that it has the tool results
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
