import json
from typing import AsyncIterator

from anthropic import AsyncAnthropic

from .base import LLMProvider, Message, ToolCall, ToolDefinition, CompletionResult


class AnthropicProvider(LLMProvider):
    """LLM provider for Anthropic Claude API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key.
            model: The model name (e.g., "claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022").
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        """
        Convert Message objects to Anthropic format.

        Returns:
            Tuple of (system_prompt, messages_list).
        """
        system_prompt = None
        result = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
                continue

            if msg.role == "tool":
                # Anthropic expects tool results in a specific format
                result.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content,
                        }
                    ],
                })
            elif msg.tool_calls:
                # Assistant message with tool calls
                content = []
                if msg.content:
                    content.append({"type": "text", "text": msg.content})
                for tc in msg.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                result.append({"role": "assistant", "content": content})
            else:
                result.append({"role": msg.role, "content": msg.content})

        return system_prompt, result

    def _convert_tools(self, tools: list[ToolDefinition] | None) -> list[dict] | None:
        """Convert ToolDefinition objects to Anthropic format."""
        if not tools:
            return None
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            }
            for tool in tools
        ]

    def _parse_response(self, response) -> CompletionResult:
        """Parse Anthropic response into CompletionResult."""
        content_parts = []
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    )
                )

        return CompletionResult(
            content="".join(content_parts),
            tool_calls=tool_calls if tool_calls else None,
            finish_reason=response.stop_reason,
        )

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> CompletionResult:
        """Generate a completion using Anthropic's messages API."""
        system_prompt, converted_messages = self._convert_messages(messages)

        kwargs = {
            "model": self.model,
            "messages": converted_messages,
            "max_tokens": 4096,
            "temperature": temperature,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        response = await self.client.messages.create(**kwargs)
        return self._parse_response(response)

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream a completion using Anthropic's messages API."""
        system_prompt, converted_messages = self._convert_messages(messages)

        kwargs = {
            "model": self.model,
            "messages": converted_messages,
            "max_tokens": 4096,
            "temperature": temperature,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def complete_with_tools(
        self,
        messages: list[Message],
        tools: list[ToolDefinition],
        temperature: float = 0.7,
    ) -> CompletionResult:
        """Generate a completion with tool calling support."""
        return await self.complete(messages, tools, temperature)
