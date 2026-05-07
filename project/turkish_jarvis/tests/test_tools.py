"""Tests for the tool registry (tools/registry.py)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from turkish_jarvis.tools.registry import ToolRegistry


def sample_add(a: int, b: int) -> int:
    """Sample sync tool."""
    return a + b


async def sample_async_echo(text: str) -> str:
    """Sample async tool."""
    await asyncio.sleep(0.001)
    return text


class TestToolRegistry:
    """Unit tests for ToolRegistry registration and execution."""

    def test_register_and_get(self) -> None:
        """A tool registered by name should be retrievable."""
        registry = ToolRegistry()
        schema: dict[str, Any] = {
            "description": "Add two numbers",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
                "required": ["a", "b"],
            },
        }
        registry.register("add", sample_add, schema)
        func = registry.get("add")
        assert func is sample_add

    def test_register_duplicate_raises(self) -> None:
        """Registering the same name twice should raise ValueError."""
        registry = ToolRegistry()
        schema = {"description": "x", "parameters": {}}
        registry.register("dup", sample_add, schema)
        with pytest.raises(ValueError, match="already registered"):
            registry.register("dup", sample_add, schema)

    def test_get_missing_raises(self) -> None:
        """Getting an unregistered tool should raise KeyError."""
        registry = ToolRegistry()
        with pytest.raises(KeyError, match="not found"):
            registry.get("missing")

    def test_get_schemas_format(self) -> None:
        """get_schemas should return OpenAI-compatible function schemas."""
        registry = ToolRegistry()
        schema = {
            "description": "Echo text",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        }
        registry.register("echo", sample_add, schema)
        schemas = registry.get_schemas()
        assert len(schemas) == 1
        assert schemas[0]["type"] == "function"
        assert schemas[0]["function"]["name"] == "echo"

    def test_execute_sync_tool(self) -> None:
        """execute should run a sync tool and return its result."""
        registry = ToolRegistry()
        schema = {"description": "x", "parameters": {}}
        registry.register("add", sample_add, schema)
        result = asyncio.run(registry.execute("add", {"a": 2, "b": 3}))
        assert result == 5

    @pytest.mark.asyncio
    async def test_execute_async_tool(self) -> None:
        """execute should await an async tool and return its result."""
        registry = ToolRegistry()
        schema = {"description": "x", "parameters": {}}
        registry.register("echo", sample_async_echo, schema)
        result = await registry.execute("echo", {"text": "hello"})
        assert result == "hello"
