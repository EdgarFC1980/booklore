import json
from typing import AsyncIterator

from openai import AsyncOpenAI

from .base import LLMProvider, Message, ToolCall, ToolDefinition, CompletionResult


class OpenAIProvider(LLMProvider):
    """LLM provider for OpenAI API."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key.
            model: The model name (e.g., "gpt-4o-mini", "gpt-4o").
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """Convert Message objects to OpenAI format."""
        result = []
        for msg in messages:
            converted = {"role": msg.role, "content": msg.content}
            if msg.tool_call_id:
                converted["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                converted["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in msg.tool_calls
                ]
            result.append(converted)
        return result

    def _convert_tools(self, tools: list[ToolDefinition] | None) -> list[dict] | None:
        """Convert ToolDefinition objects to OpenAI format."""
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

    def _parse_tool_calls(self, tool_calls) -> list[ToolCall] | None:
        """Parse OpenAI tool calls into ToolCall objects."""
        if not tool_calls:
            return None
        return [
            ToolCall(
                id=tc.id,
                name=tc.function.name,
                arguments=json.loads(tc.function.arguments)
                if tc.function.arguments
                else {},
            )
            for tc in tool_calls
        ]

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> CompletionResult:
        """Generate a completion using OpenAI's chat API."""
        kwargs = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
        }

        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message

        return CompletionResult(
            content=message.content or "",
            tool_calls=self._parse_tool_calls(message.tool_calls),
            finish_reason=choice.finish_reason,
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream a completion using OpenAI's chat API."""
        kwargs = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "stream": True,
        }

        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        stream = await self.client.chat.completions.create(**kwargs)

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def complete_with_tools(
        self,
        messages: list[Message],
        tools: list[ToolDefinition],
        temperature: float = 0.7,
    ) -> CompletionResult:
        """Generate a completion with tool calling support."""
        return await self.complete(messages, tools, temperature)
