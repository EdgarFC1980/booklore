import yaml
from typing import AsyncIterator

from .settings import settings
from .llm_providers import (
    LLMProvider,
    OllamaProvider,
    OpenAIProvider,
    AnthropicProvider,
    Message,
    ToolDefinition,
    CompletionResult,
)


class ModelGateway:
    """
    Gateway for accessing LLM providers with tier-based configuration.

    Supports multiple backends (Ollama, OpenAI, Anthropic) with configurable
    tiers for different use cases (e.g., local_light, local_heavy, cloud).
    """

    def __init__(self) -> None:
        with open(settings.models_config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        self.default_tier = cfg.get("default_tier", "local_light")
        self.tiers = cfg.get("tiers", {})
        self._providers: dict[str, LLMProvider] = {}

    def _get_provider(self, tier: str) -> LLMProvider:
        """Get or create a provider for the given tier."""
        if tier in self._providers:
            return self._providers[tier]

        if tier not in self.tiers:
            raise ValueError(f"Unknown tier: {tier}")

        tier_config = self.tiers[tier]
        backend = tier_config.get("backend")

        if backend == "ollama":
            provider = OllamaProvider(
                host=tier_config["host"],
                model=tier_config["model"],
                timeout=tier_config.get("timeout", 120.0),
            )
        elif backend == "openai":
            api_key = tier_config.get("api_key") or settings.openai_api_key
            if not api_key:
                raise ValueError(f"OpenAI API key not configured for tier: {tier}")
            provider = OpenAIProvider(
                api_key=api_key,
                model=tier_config["model"],
            )
        elif backend == "anthropic":
            api_key = tier_config.get("api_key") or settings.anthropic_api_key
            if not api_key:
                raise ValueError(f"Anthropic API key not configured for tier: {tier}")
            provider = AnthropicProvider(
                api_key=api_key,
                model=tier_config["model"],
            )
        else:
            raise ValueError(f"Unsupported backend: {backend}")

        self._providers[tier] = provider
        return provider

    def get_provider(self, tier: str | None = None) -> LLMProvider:
        """
        Get a provider for the specified tier.

        Args:
            tier: The tier name. If None, uses the default tier.

        Returns:
            The LLMProvider instance for the tier.
        """
        return self._get_provider(tier or self.default_tier)

    async def complete(
        self,
        messages: list[Message],
        tier: str | None = None,
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> CompletionResult:
        """
        Generate a completion using the specified tier.

        Args:
            messages: The conversation history.
            tier: The tier to use. If None, uses the default tier.
            tools: Optional list of tools for function calling.
            temperature: Sampling temperature.

        Returns:
            CompletionResult with the generated content.
        """
        provider = self._get_provider(tier or self.default_tier)
        return await provider.complete(messages, tools, temperature)

    async def stream(
        self,
        messages: list[Message],
        tier: str | None = None,
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """
        Stream a completion using the specified tier.

        Args:
            messages: The conversation history.
            tier: The tier to use. If None, uses the default tier.
            tools: Optional list of tools for function calling.
            temperature: Sampling temperature.

        Yields:
            Text chunks as they are generated.
        """
        provider = self._get_provider(tier or self.default_tier)
        async for chunk in provider.stream(messages, tools, temperature):
            yield chunk

    async def complete_with_tools(
        self,
        messages: list[Message],
        tools: list[ToolDefinition],
        tier: str | None = None,
        temperature: float = 0.7,
    ) -> CompletionResult:
        """
        Generate a completion with tool calling support.

        Args:
            messages: The conversation history.
            tools: List of available tools.
            tier: The tier to use. If None, uses the default tier.
            temperature: Sampling temperature.

        Returns:
            CompletionResult with content and/or tool calls.
        """
        provider = self._get_provider(tier or self.default_tier)
        return await provider.complete_with_tools(messages, tools, temperature)

    # Legacy method for backward compatibility
    async def classify(self, prompt: str, tier: str | None = None) -> str:
        """
        Simple text completion (legacy interface).

        Args:
            prompt: The prompt text.
            tier: The tier to use.

        Returns:
            The generated text.
        """
        messages = [Message(role="user", content=prompt)]
        result = await self.complete(messages, tier)
        return result.content
