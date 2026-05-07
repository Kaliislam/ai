"""Tool registry with OpenAI-compatible function calling schemas."""

import asyncio
import inspect
from typing import Any, Callable


class ToolRegistry:
    """Central registry for agent tools.

    Tools are registered with a name, callable function, and JSON schema.
    The registry can list schemas in OpenAI function-calling format and
    execute tools by name.
    """

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: dict[str, Callable[..., Any]] = {}
        self._schemas: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        func: Callable[..., Any],
        schema: dict[str, Any],
    ) -> None:
        """Register a new tool.

        Args:
            name: Unique tool name.
            func: Callable implementing the tool logic.
            schema: OpenAI function-calling JSON schema for the tool.

        Raises:
            ValueError: If a tool with the same name already exists.
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered.")
        self._tools[name] = func
        self._schemas[name] = schema

    def get(self, name: str) -> Callable[..., Any]:
        """Retrieve a tool callable by name.

        Args:
            name: Tool name.

        Returns:
            The registered callable.

        Raises:
            KeyError: If the tool is not registered.
        """
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Tool '{name}' not found in registry.") from exc

    def get_schemas(self) -> list[dict[str, Any]]:
        """Return all tool schemas in OpenAI function-calling format.

        Returns:
            List of schema dictionaries with 'type', 'function', etc.
        """
        schemas: list[dict[str, Any]] = []
        for name, schema in self._schemas.items():
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": schema.get("description", ""),
                        "parameters": schema.get("parameters", {}),
                    },
                }
            )
        return schemas

    async def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        """Execute a registered tool with the given arguments.

        Automatically awaits async functions.

        Args:
            name: Tool name.
            arguments: Keyword arguments to pass to the tool.

        Returns:
            The tool result.

        Raises:
            KeyError: If the tool is not registered.
            Exception: Any exception raised by the tool callable.
        """
        func = self.get(name)
        if asyncio.iscoroutinefunction(func):
            return await func(**arguments)
        return func(**arguments)
