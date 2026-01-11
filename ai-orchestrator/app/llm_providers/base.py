from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Literal


@dataclass
class Message:
    """A message in a conversation."""
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: str | None = None
    tool_calls: list["ToolCall"] | None = None


@dataclass
class ToolCall:
    """A tool call requested by the model."""
    id: str
    name: str
    arguments: dict


@dataclass
class ToolDefinition:
    """Definition of a tool that the model can call."""
    name: str
    description: str
    parameters: dict = field(default_factory=dict)


@dataclass
class CompletionResult:
    """Result of a completion request."""
    content: str
    tool_calls: list[ToolCall] | None = None
    finish_reason: str | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> CompletionResult:
        """
        Generate a completion for the given messages.

        Args:
            messages: The conversation history.
            tools: Optional list of tools the model can call.
            temperature: Sampling temperature (0.0 to 1.0).

        Returns:
            CompletionResult with the generated content and any tool calls.
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """
        Stream a completion for the given messages.

        Args:
            messages: The conversation history.
            tools: Optional list of tools the model can call.
            temperature: Sampling temperature (0.0 to 1.0).

        Yields:
            Text chunks as they are generated.
        """
        pass

    @abstractmethod
    async def complete_with_tools(
        self,
        messages: list[Message],
        tools: list[ToolDefinition],
        temperature: float = 0.7,
    ) -> CompletionResult:
        """
        Generate a completion that may include tool calls.

        This method is specifically for function calling scenarios where
        the model should decide whether to call tools or respond directly.

        Args:
            messages: The conversation history.
            tools: List of available tools.
            temperature: Sampling temperature (0.0 to 1.0).

        Returns:
            CompletionResult with content and/or tool calls.
        """
        pass
