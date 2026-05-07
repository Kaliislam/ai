"""Skill loader with dynamic module loading / unloading support.

The SkillLoader can:
    - Download SKILL.md files from GitHub.
    - Parse them into SkillDefinition objects.
    - Generate executable Python modules from skill definitions.
    - Dynamically load / unload modules at runtime.
"""

from __future__ import annotations

import asyncio
import importlib.util
import inspect
import os
import sys
import tempfile
import textwrap
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from turkish_jarvis.skills.skill_parser import (
    SkillDefinition,
    fetch_skill_md_from_github,
    parse_skill_md,
)


class GeneratedSkillModule:
    """Wrapper around a dynamically-generated Python module for a skill."""

    def __init__(self, skill: SkillDefinition, module: ModuleType) -> None:
        self.skill = skill
        self.module = module
        self._functions: dict[str, Callable[..., Any]] = {}
        self._discover_functions()

    def _discover_functions(self) -> None:
        """Scan the generated module for async callables matching tool names."""
        for tool in self.skill.tools:
            func_name = tool.name
            candidate = getattr(self.module, func_name, None)
            if candidate is not None and (asyncio.iscoroutinefunction(candidate) or callable(candidate)):
                self._functions[func_name] = candidate

    def get_function(self, name: str) -> Callable[..., Any] | None:
        """Retrieve a tool function by name."""
        return self._functions.get(name)

    def list_functions(self) -> list[str]:
        """Return names of all discovered tool functions."""
        return list(self._functions.keys())

    async def execute(self, tool_name: str, **kwargs: Any) -> Any:
        """Execute a tool function with the given arguments."""
        func = self._functions.get(tool_name)
        if func is None:
            raise KeyError(f"Tool '{tool_name}' not found in skill '{self.skill.name}'.")
        if asyncio.iscoroutinefunction(func):
            return await func(**kwargs)
        return func(**kwargs)


class SkillLoader:
    """Loads, generates, and manages SKILL.md-based skills as Python modules.

    Skills are stored in a local directory tree organised by category:
        skills/
        ├── web/
        ├── dev/
        ├── data/
        ├── system/
        ├── media/
        └── comm/
    """

    def __init__(self, base_dir: str | None = None) -> None:
        """Initialize the loader.

        Args:
            base_dir: Root directory where generated skill modules are persisted.
                      Defaults to ``<package>/skills/``.
        """
        if base_dir is None:
            pkg_dir = Path(__file__).resolve().parent
            self.base_dir = pkg_dir
        else:
            self.base_dir = Path(base_dir)

        self._loaded: dict[str, GeneratedSkillModule] = {}
        self._ensure_categories()

    def _ensure_categories(self) -> None:
        """Create category subdirectories if they do not exist."""
        for cat in ("web", "dev", "data", "system", "media", "comm", "general"):
            (self.base_dir / cat).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------

    @staticmethod
    def generate_python_code(skill: SkillDefinition) -> str:
        """Generate an async Python module from a SkillDefinition.

        Each tool becomes an async function with type hints derived from
        the parameter schema.
        """
        lines: list[str] = [
            f'"""Auto-generated skill module for {skill.name}.',
            f"",
            f"Category : {skill.category}",
            f"Version  : {skill.version}",
            f"Author   : {skill.author}",
            f"License  : {skill.license}",
            f'"""',
            f"",
            f"from typing import Any",
            f"",
            f"# Skill metadata",
            f"SKILL_NAME = {skill.name!r}",
            f"SKILL_DESCRIPTION = {skill.description!r}",
            f"SKILL_CATEGORY = {skill.category!r}",
            f"SKILL_VERSION = {skill.version!r}",
            f"SKILL_AUTHOR = {skill.author!r}",
            f"SKILL_LICENSE = {skill.license!r}",
            f"",
            f"",
        ]

        for tool in skill.tools:
            lines.append(f"async def {tool.name}(")
            # Build parameters with type hints and defaults
            sig_parts: list[str] = []
            for p in tool.parameters:
                py_type = _json_type_to_python(p.ptype)
                if p.default is not None:
                    sig_parts.append(f"    {p.name}: {py_type} = {p.default!r}")
                elif not p.required:
                    sig_parts.append(f"    {p.name}: {py_type} | None = None")
                else:
                    sig_parts.append(f"    {p.name}: {py_type}")

            if sig_parts:
                lines.append(",\n".join(sig_parts))
            lines.append(") -> Any:")
            # Docstring
            desc = tool.description or f"Execute {tool.name}."
            lines.append(f'    """{desc}"""')
            lines.append("    # TODO: Implement the tool logic here.")
            lines.append("    pass")
            lines.append("")
            lines.append("")

        # Add a metadata dictionary for introspection
        tools_meta = []
        for tool in skill.tools:
            tools_meta.append(
                f"        {tool.name!r}: {{"
                f"'description': {tool.description!r}, "
                f"'parameters': [{', '.join(repr(p.name) for p in tool.parameters)}]"
                f"}},"
            )
        lines.append("SKILL_TOOLS = {")
        lines.extend(tools_meta)
        lines.append("}")
        lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _module_path_for(self, skill: SkillDefinition) -> Path:
        """Return the intended file path for a generated module."""
        cat_dir = self.base_dir / skill.category
        safe_name = skill.name.replace("-", "_").replace(" ", "_")
        return cat_dir / f"{safe_name}.py"

    def _write_module(self, skill: SkillDefinition, code: str) -> Path:
        """Persist generated code to the category subdirectory."""
        path = self._module_path_for(skill)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code, encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_module_from_path(self, path: Path, module_name: str) -> ModuleType:
        """Dynamically import a Python file as a module."""
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create module spec for {path}")
        module = importlib.util.module_from_spec(spec)
        # Ensure the parent package is in sys.modules so relative imports work
        pkg_name = "turkish_jarvis.skills.generated"
        if pkg_name not in sys.modules:
            sys.modules[pkg_name] = ModuleType(pkg_name)
        module.__package__ = pkg_name
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def load_skill(self, skill: SkillDefinition, *, persist: bool = True) -> GeneratedSkillModule:
        """Load a SkillDefinition by generating and importing its Python module.

        Args:
            skill: Parsed skill definition.
            persist: If True, write the generated .py file to disk.

        Returns:
            A GeneratedSkillModule wrapper.
        """
        if skill.name in self._loaded:
            return self._loaded[skill.name]

        code = self.generate_python_code(skill)
        if persist:
            path = self._write_module(skill, code)
            module_name = f"turkish_jarvis.skills.generated.{skill.name.replace('-', '_')}"
            module = self._load_module_from_path(path, module_name)
        else:
            module = self._load_from_string(code, skill.name)

        wrapper = GeneratedSkillModule(skill, module)
        self._loaded[skill.name] = wrapper
        return wrapper

    def _load_from_string(self, code: str, skill_name: str) -> ModuleType:
        """Compile and execute Python code in a transient module."""
        module_name = f"__transient_skill_{skill_name.replace('-', '_')}__"
        module = ModuleType(module_name)
        module.__package__ = "turkish_jarvis.skills.generated"
        sys.modules[module_name] = module
        exec(compile(code, f"<skill-{skill_name}>", "exec"), module.__dict__)
        return module

    # ------------------------------------------------------------------
    # Public API: GitHub / file / directory
    # ------------------------------------------------------------------

    async def load_from_github(self, repo: str, skill_path: str, *, persist: bool = True) -> GeneratedSkillModule:
        """Download a SKILL.md from GitHub, parse it, and load the skill.

        Args:
            repo: Repository in "owner/repo" format.
            skill_path: Path to the SKILL.md inside the repo.
            persist: Persist the generated module to disk.

        Returns:
            A GeneratedSkillModule wrapper.
        """
        raw_md = await fetch_skill_md_from_github(repo, skill_path)
        skill = parse_skill_md(raw_md)
        return self.load_skill(skill, persist=persist)

    def load_from_file(self, path: str, *, persist: bool = True) -> GeneratedSkillModule:
        """Load a local SKILL.md file.

        Args:
            path: Path to the local SKILL.md file.
            persist: Persist the generated module to disk.

        Returns:
            A GeneratedSkillModule wrapper.
        """
        content = Path(path).read_text(encoding="utf-8")
        skill = parse_skill_md(content)
        return self.load_skill(skill, persist=persist)

    def load_all_from_directory(self, directory: str, *, persist: bool = True) -> list[GeneratedSkillModule]:
        """Recursively find all SKILL.md files in a directory and load them.

        Args:
            directory: Root directory to scan.
            persist: Persist generated modules to disk.

        Returns:
            List of loaded GeneratedSkillModule wrappers.
        """
        results: list[GeneratedSkillModule] = []
        for root, _dirs, files in os.walk(directory):
            for fname in files:
                if fname.lower() == "skill.md":
                    full = Path(root) / fname
                    try:
                        wrapper = self.load_from_file(str(full), persist=persist)
                        results.append(wrapper)
                    except Exception as exc:
                        # Log but continue so one bad file doesn't break the batch
                        print(f"[SkillLoader] Failed to load {full}: {exc}")
        return results

    # ------------------------------------------------------------------
    # Management
    # ------------------------------------------------------------------

    def unload(self, skill_name: str) -> bool:
        """Unload a skill and remove it from the registry.

        If the skill was persisted to disk, the generated .py file is
        also deleted.

        Returns:
            True if the skill was found and removed.
        """
        wrapper = self._loaded.pop(skill_name, None)
        if wrapper is None:
            return False

        # Clean up sys.modules
        for mod_name in list(sys.modules):
            if skill_name.replace("-", "_") in mod_name and "__transient_skill_" in mod_name:
                del sys.modules[mod_name]

        # Remove persisted file if present
        path = self._module_path_for(wrapper.skill)
        if path.exists():
            path.unlink()
        return True

    def list_loaded(self) -> list[dict[str, Any]]:
        """Return metadata for all currently loaded skills."""
        return [
            {
                "name": w.skill.name,
                "category": w.skill.category,
                "version": w.skill.version,
                "tools": w.list_functions(),
                "path": str(self._module_path_for(w.skill)),
            }
            for w in self._loaded.values()
        ]

    def get_skill(self, name: str) -> SkillDefinition:
        """Retrieve the SkillDefinition for a loaded skill by name."""
        try:
            return self._loaded[name].skill
        except KeyError as exc:
            raise KeyError(f"Skill '{name}' is not loaded.") from exc

    def get_wrapper(self, name: str) -> GeneratedSkillModule:
        """Retrieve the full GeneratedSkillModule wrapper by name."""
        try:
            return self._loaded[name]
        except KeyError as exc:
            raise KeyError(f"Skill '{name}' is not loaded.") from exc

    def __len__(self) -> int:
        return len(self._loaded)

    def __contains__(self, name: str) -> bool:
        return name in self._loaded


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_JSON_TYPE_MAP: dict[str, str] = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "array": "list",
    "object": "dict",
    "null": "None",
}


def _json_type_to_python(jtype: str) -> str:
    """Map a JSON-schema-ish type string to a Python type hint."""
    return _JSON_TYPE_MAP.get(jtype.lower(), "Any")
