"""OpenAI-compatible chat client with tool calling for the skill runtime.

The default LightRAG ``llm_model_func`` does not expose the ``tools=[...]``
parameter required for multi-turn tool-calling agents, so the skill runtime
talks to the model directly via the OpenAI Python SDK against the same
endpoint LightRAG itself uses. xAI Grok exposes an OpenAI-compatible
``/chat/completions`` endpoint that supports function calling on every model
in the Grok family.

This module is intentionally tiny: one async ``chat_with_tools`` function
that takes ``messages`` + ``tools`` and returns a normalized response dict.
The skill runtime owns the multi-turn loop; this layer is just the wire.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ChatToolCall:
    """One tool-call request emitted by the model."""

    id: str
    name: str
    arguments_json: str  # raw string — runtime parses + validates


@dataclass
class ChatResponse:
    """One assistant turn from a chat-completion call.

    ``content`` and ``tool_calls`` are mutually exclusive in practice but the
    spec allows both. Runtime persists both verbatim into the transcript.
    """

    content: str
    tool_calls: list[ChatToolCall]
    finish_reason: str
    usage: dict[str, Any]
    raw_message: dict[str, Any]  # exact dict to push back into messages list


def _client_kwargs() -> dict[str, str]:
    api_key = os.getenv("LLM_BINDING_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "LLM_BINDING_API_KEY not set — skill tool runtime cannot reach the LLM"
        )
    base_url = os.getenv("LLM_BINDING_HOST", "").strip() or "https://api.openai.com/v1"
    return {"api_key": api_key, "base_url": base_url}


def _resolve_model() -> str:
    # Skills are multi-turn reasoning agents — always use the most powerful
    # model available. Theseus pins this to REASONING_LLM_NAME.
    val = os.getenv("REASONING_LLM_NAME", "").strip()
    if val:
        return val
    raise RuntimeError(
        "REASONING_LLM_NAME not set — skill tool runtime requires the "
        "reasoning model to be configured in .env"
    )


async def chat_with_tools(
    messages: list[dict[str, Any]],
    tools: Optional[list[dict[str, Any]]] = None,
    *,
    tool_choice: str | dict[str, Any] = "auto",
    temperature: float = 0.2,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
    timeout: float = 120.0,
) -> ChatResponse:
    """Single chat-completion turn against the configured OpenAI-compatible endpoint.

    Args:
        messages: OpenAI chat-completion ``messages`` list. Caller owns the
            full transcript and appends each assistant + tool message.
        tools: List of tool definitions in OpenAI function-calling shape
            ``[{"type": "function", "function": {...}}]``. Pass ``None`` for
            a plain non-tool turn (used by the runtime's final-answer call).
        tool_choice: ``"auto"`` (default), ``"none"``, ``"required"``, or
            an explicit ``{"type": "function", "function": {"name": ...}}``.
        temperature: Sampling temperature.
        max_tokens: Optional cap on completion length.
        model: Override ``LLM_MODEL`` env var.
        timeout: Per-request timeout in seconds.

    Returns:
        A :class:`ChatResponse` with parsed content + tool-call requests.

    Raises:
        RuntimeError: If env config is missing or the API call fails after
            retries (the SDK retries transient errors automatically).
    """
    # Lazy import — keeps the dep optional for environments that never invoke
    # tools-mode skills (legacy single-shot path doesn't need this).
    try:
        from openai import AsyncOpenAI
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "openai package required for skill tool runtime — install with `pip install openai`"
        ) from exc

    client = AsyncOpenAI(**_client_kwargs(), timeout=timeout)
    chosen_model = model or _resolve_model()

    payload: dict[str, Any] = {
        "model": chosen_model,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = tool_choice
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    logger.debug(
        "skill chat: model=%s msgs=%d tools=%d tool_choice=%s",
        chosen_model,
        len(messages),
        len(tools or []),
        tool_choice if isinstance(tool_choice, str) else "explicit",
    )

    completion = await client.chat.completions.create(**payload)
    choice = completion.choices[0]
    msg = choice.message

    raw_message: dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
    tool_calls: list[ChatToolCall] = []
    if getattr(msg, "tool_calls", None):
        raw_tool_calls = []
        for tc in msg.tool_calls:
            tool_calls.append(
                ChatToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments_json=tc.function.arguments or "{}",
                )
            )
            raw_tool_calls.append(
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments or "{}",
                    },
                }
            )
        raw_message["tool_calls"] = raw_tool_calls

    usage = {}
    if completion.usage is not None:
        usage = {
            "prompt_tokens": completion.usage.prompt_tokens,
            "completion_tokens": completion.usage.completion_tokens,
            "total_tokens": completion.usage.total_tokens,
        }

    return ChatResponse(
        content=msg.content or "",
        tool_calls=tool_calls,
        finish_reason=choice.finish_reason or "",
        usage=usage,
        raw_message=raw_message,
    )
