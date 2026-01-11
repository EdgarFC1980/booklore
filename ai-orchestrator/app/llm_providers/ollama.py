import json
from typing import AsyncIterator

import httpx

from .base import LLMProvider, Message, ToolCall, ToolDefinition, CompletionResult


class OllamaProvider(LLMProvider):
    """LLM provider for Ollama local models."""

    def __init__(self, host: str, model: str, timeout: float = 120.0):
        """
        Initialize the Ollama provider.

        Args:
            host: The Ollama server URL (e.g., "http://localhost:11434").
            model: The model name (e.g., "llama3.2:3b-instruct").
            timeout: Request timeout in seconds.
        """
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """Convert Message objects to Ollama format."""
        result = []
        for msg in messages:
            converted = {"role": msg.role, "content": msg.content}
            result.append(converted)
        return result

    def _convert_tools(self, tools: list[ToolDefinition] | None) -> list[dict] | None:
        """Convert ToolDefinition objects to Ollama format."""
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in tools
        ]

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> CompletionResult:
        """Generate a completion using Ollama's chat API."""
        payload = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "stream": False,
            "options": {"temperature": temperature},
        }

        if tools:
            payload["tools"] = self._convert_tools(tools)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.host}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        message = data.get("message", {})
        content = message.get("content", "")

        # Parse tool calls if present
        tool_calls = None
        if "tool_calls" in message:
            tool_calls = [
                ToolCall(
                    id=tc.get("id", f"call_{i}"),
                    name=tc["function"]["name"],
                    arguments=tc["function"]["arguments"]
                    if isinstance(tc["function"]["arguments"], dict)
                    else json.loads(tc["function"]["arguments"]),
                )
                for i, tc in enumerate(message["tool_calls"])
            ]

        return CompletionResult(
            content=content,
            tool_calls=tool_calls,
            finish_reason=data.get("done_reason"),
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream a completion using Ollama's chat API."""
        payload = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "stream": True,
            "options": {"temperature": temperature},
        }

        if tools:
            payload["tools"] = self._convert_tools(tools)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.host}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        message = data.get("message", {})
                        content = message.get("content", "")
                        if content:
                            yield content

    async def complete_with_tools(
        self,
        messages: list[Message],
        tools: list[ToolDefinition],
        temperature: float = 0.7,
    ) -> CompletionResult:
        """Generate a completion with tool calling support."""
        return await self.complete(messages, tools, temperature)
