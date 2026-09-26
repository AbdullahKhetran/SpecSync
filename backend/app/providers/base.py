"""
base.py — LLMProvider Protocol.

Any provider implementation must satisfy this interface.
Selected at runtime via the LLM_PROVIDER environment variable.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Provider-agnostic interface for JSON-generating LLM calls."""

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict,
    ) -> str:
        """
        Call the LLM and return the raw JSON string.

        Args:
            system_prompt: The role/instruction prompt.
            user_prompt:   The user-facing content (e.g. the PRD text).
            json_schema:   The JSON Schema dict the response must conform to.

        Returns:
            A string that should parse as valid JSON matching json_schema.

        Raises:
            RuntimeError: If the provider fails after any internal retries.
        """
        ...
