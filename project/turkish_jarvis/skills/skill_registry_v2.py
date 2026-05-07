"""Skill registry v2 — organised, searchable, and executable skill collection.

SkillRegistryV2 is the next-generation registry that sits above the legacy
ToolRegistry.  It stores SkillDefinition objects by category and provides
semantic search, batched loading, and execution of skill tools.

Categories
----------
    web     — Web scraping, search, HTTP/API interactions
    dev     — Development, coding, Git, build & deploy
    data    — Data processing, analysis, database operations
    system  — System management, file operations, OS tasks
    media   — Image, video, audio processing
    comm    — Communication, email, social, messaging
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from turkish_jarvis.skills.skill_loader import GeneratedSkillModule, SkillLoader
from turkish_jarvis.skills.skill_parser import SkillDefinition, parse_skill_md


class SkillRegistryV2:
    """Next-generation skill registry with category organisation and search."""

    CATEGORIES = ("web", "dev", "data", "system", "media", "comm", "general")

    def __init__(self, loader: SkillLoader | None = None) -> None:
        """Initialise the registry with optional shared SkillLoader.

        Args:
            loader: A SkillLoader instance used to materialise skills.
                    If None, a default loader is created.
        """
        self._skills: dict[str, SkillDefinition] = {}
        self._by_category: dict[str, set[str]] = {c: set() for c in self.CATEGORIES}
        self._wrappers: dict[str, GeneratedSkillModule] = {}
        self._loader = loader or SkillLoader()
        self._legacy_registry: Any | None = None  # populated lazily

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_skill(self, skill: SkillDefinition) -> None:
        """Register a skill definition and index it by category.

        Args:
            skill: Parsed skill definition.

        Raises:
            ValueError: If a skill with the same name is already registered.
        """
        if skill.name in self._skills:
            raise ValueError(f"Skill '{skill.name}' is already registered.")
        self._skills[skill.name] = skill
        cat = skill.category if skill.category in self.CATEGORIES else "general"
        self._by_category[cat].add(skill.name)

    def register_from_loader(self, skill_name: str) -> GeneratedSkillModule:
        """Pull a skill that has already been loaded into the shared SkillLoader.

        Args:
            skill_name: Name of a skill already present in the loader.

        Returns:
            The GeneratedSkillModule wrapper.
        """
        wrapper = self._loader.get_wrapper(skill_name)
        self._wrappers[skill_name] = wrapper
        if skill_name not in self._skills:
            self.register_skill(wrapper.skill)
        return wrapper

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_skill(self, name: str) -> SkillDefinition:
        """Retrieve a skill definition by name.

        Raises:
            KeyError: If the skill is not registered.
        """
        try:
            return self._skills[name]
        except KeyError as exc:
            raise KeyError(f"Skill '{name}' not found in registry.") from exc

    def get_by_category(self, category: str) -> list[SkillDefinition]:
        """Return all skills belonging to a given category.

        Args:
            category: One of the canonical categories.

        Returns:
            List of SkillDefinition objects.
        """
        cat = category if category in self.CATEGORIES else "general"
        return [self._skills[name] for name in self._by_category[cat] if name in self._skills]

    def all_skills(self) -> list[SkillDefinition]:
        """Return every registered skill definition."""
        return list(self._skills.values())

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str) -> list[SkillDefinition]:
        """Search skill names, descriptions, and tool names.

        The query is split into words and matched case-insensitively.
        Results are ranked by number of matching fields.

        Args:
            query: Free-text search query.

        Returns:
            List of matching SkillDefinition objects, best matches first.
        """
        words = [w.lower() for w in query.split() if w]
        scored: list[tuple[int, SkillDefinition]] = []

        for skill in self._skills.values():
            score = 0
            haystack = (
                skill.name.lower()
                + " "
                + skill.description.lower()
                + " "
                + skill.category.lower()
            )
            for tool in skill.tools:
                haystack += " " + tool.name.lower() + " " + tool.description.lower()

            for w in words:
                if w in skill.name.lower():
                    score += 3
                if w in skill.description.lower():
                    score += 2
                if w in haystack:
                    score += 1

            if score > 0:
                scored.append((score, skill))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored]

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def execute(self, skill_name: str, tool_name: str, **kwargs: Any) -> Any:
        """Execute a specific tool from a registered skill.

        If the skill wrapper has not been materialised yet, the registry
        attempts to generate it via the shared SkillLoader.

        Args:
            skill_name: Registered skill name.
            tool_name: Tool/function name inside the skill.
            **kwargs: Arguments forwarded to the tool.

        Returns:
            Tool return value.

        Raises:
            KeyError: If skill or tool is missing.
        """
        wrapper = self._wrappers.get(skill_name)
        if wrapper is None:
            skill = self.get_skill(skill_name)
            wrapper = self._loader.load_skill(skill)
            self._wrappers[skill_name] = wrapper

        return await wrapper.execute(tool_name, **kwargs)

    async def execute_by_schema(self, skill_name: str, arguments: dict[str, Any]) -> Any:
        """Execute the *single* tool of a skill when the skill exposes exactly one tool.

        This is useful for agents that dispatch by skill name rather than
        individual tool name.

        Args:
            skill_name: Skill name.
            arguments: Keyword arguments for the sole tool.

        Raises:
            KeyError: If the skill has zero or more than one tool.
        """
        skill = self.get_skill(skill_name)
        if len(skill.tools) != 1:
            raise KeyError(
                f"Skill '{skill_name}' must expose exactly one tool for schema dispatch, "
                f"but has {len(skill.tools)} tools."
            )
        return await self.execute(skill_name, skill.tools[0].name, **arguments)

    # ------------------------------------------------------------------
    # OpenAI-compatible schemas
    # ------------------------------------------------------------------

    def get_schemas(self) -> list[dict[str, Any]]:
        """Return all registered skill tools as OpenAI function-calling schemas."""
        schemas: list[dict[str, Any]] = []
        for skill in self._skills.values():
            schemas.extend(skill.to_openai_schema())
        return schemas

    def get_legacy_registry(self) -> Any:
        """Build a ToolRegistry-compatible wrapper populated with all skills.

        Returns:
            A ToolRegistry instance (lazy-imported so the old registry is not
            required at import time).
        """
        if self._legacy_registry is not None:
            return self._legacy_registry

        from turkish_jarvis.tools.registry import ToolRegistry

        reg = ToolRegistry()
        for skill in self._skills.values():
            for schema in skill.to_openai_schema():
                func_name = schema["function"]["name"]
                description = schema["function"]["description"]
                parameters = schema["function"]["parameters"]

                # Create a thin async adapter that delegates back to this registry
                async def _make_adapter(sn: str = skill.name, tn: str = func_name) -> Any:
                    async def adapter(**kwargs: Any) -> Any:
                        # Determine actual tool name (strip skill prefix if present)
                        actual_tool = tn
                        if actual_tool.startswith(f"{sn}__"):
                            actual_tool = actual_tool[len(sn) + 2:]
                        return await self.execute(sn, actual_tool, **kwargs)

                    return adapter

                # Need to bind immediately to avoid closure capture issues
                adapter = _make_adapter()
                reg.register(func_name, adapter, {"description": description, "parameters": parameters})
        self._legacy_registry = reg
        return reg

    # ------------------------------------------------------------------
    # Batch loading
    # ------------------------------------------------------------------

    async def load_from_github(self, repo: str, skill_path: str) -> SkillDefinition:
        """Download a SKILL.md from GitHub and register it.

        Args:
            repo: Repository in "owner/repo" format.
            skill_path: Path to SKILL.md inside the repo.

        Returns:
            The registered SkillDefinition.
        """
        wrapper = await self._loader.load_from_github(repo, skill_path)
        self._wrappers[wrapper.skill.name] = wrapper
        self.register_skill(wrapper.skill)
        return wrapper.skill

    def load_from_file(self, path: str) -> SkillDefinition:
        """Load a local SKILL.md and register it.

        Args:
            path: Path to the local SKILL.md file.

        Returns:
            The registered SkillDefinition.
        """
        wrapper = self._loader.load_from_file(path)
        self._wrappers[wrapper.skill.name] = wrapper
        self.register_skill(wrapper.skill)
        return wrapper.skill

    def load_all_from_directory(self, directory: str) -> list[SkillDefinition]:
        """Recursively load every SKILL.md in a directory tree.

        Args:
            directory: Root directory to scan.

        Returns:
            List of registered SkillDefinition objects.
        """
        wrappers = self._loader.load_all_from_directory(directory)
        skills: list[SkillDefinition] = []
        for w in wrappers:
            self._wrappers[w.skill.name] = w
            self.register_skill(w.skill)
            skills.append(w.skill)
        return skills

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    async def discover(self, repo: str = "VoltAgent/awesome-agent-skills") -> list[dict[str, Any]]:
        """Discover available skills by scanning the awesome-agent-skills repo README.

        This is a lightweight discovery mechanism that parses the README for
        embedded skill links and returns metadata records.

        Args:
            repo: Repository to scan. Defaults to VoltAgent's list.

        Returns:
            List of discovered skill metadata dictionaries.
                Each dict contains: name, source_repo, skill_path, description.
        """
        import aiohttp

        url = f"https://raw.githubusercontent.com/{repo}/main/README.md"
        discovered: list[dict[str, Any]] = []

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    # Try master fallback
                    url = f"https://raw.githubusercontent.com/{repo}/master/README.md"
                    async with session.get(url) as resp2:
                        if resp2.status != 200:
                            raise ValueError(f"Cannot discover skills: README fetch failed ({resp.status}).")
                        readme = await resp2.text()
                else:
                    readme = await resp.text()

        # Heuristic: look for markdown links that point to GitHub repos containing /skills/
        # Pattern: [name](https://github.com/owner/repo/tree/branch/skills/...)
        link_pattern = re.compile(
            r"\[([^\]]+)\]\(https://github\.com/([^/]+/[^/]+)(?:/tree/[^/]+)?(/skills/[^)]+)\)"
        )
        for match in link_pattern.finditer(readme):
            discovered.append(
                {
                    "name": match.group(1).strip(),
                    "source_repo": match.group(2),
                    "skill_path": match.group(3),
                    "description": "",
                }
            )

        # Also look for `owner/repo/skills/...` inline code blocks or raw links
        raw_pattern = re.compile(
            r"(?:^|\s)`?([^/\s]+/[^/\s]+)(/skills/[^\s\)`]+)`?"
        )
        for match in raw_pattern.finditer(readme):
            entry = {
                "name": match.group(2).split("/")[-1] or "unknown",
                "source_repo": match.group(1),
                "skill_path": match.group(2),
                "description": "",
            }
            if entry not in discovered:
                discovered.append(entry)

        return discovered

    async def discover_and_load(
        self,
        repo: str = "VoltAgent/awesome-agent-skills",
        max_skills: int = 5,
    ) -> list[SkillDefinition]:
        """Discover skills and immediately load the first ``max_skills`` ones.

        Args:
            repo: Repository to scan.
            max_skills: Cap on how many skills to auto-load.

        Returns:
            List of successfully loaded SkillDefinition objects.
        """
        candidates = await self.discover(repo)
        loaded: list[SkillDefinition] = []
        for cand in candidates[:max_skills]:
            try:
                # Heuristic: the skill path may or may not end with /SKILL.md
                skill_path = cand["skill_path"]
                if not skill_path.endswith("SKILL.md"):
                    skill_path = skill_path.rstrip("/") + "/SKILL.md"
                skill = await self.load_from_github(cand["source_repo"], skill_path)
                loaded.append(skill)
            except Exception as exc:
                print(f"[SkillRegistryV2] Auto-load failed for {cand['name']}: {exc}")
        return loaded

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def list_categories(self) -> dict[str, list[str]]:
        """Return a mapping of category -> skill names."""
        return {cat: sorted(names) for cat, names in self._by_category.items() if names}

    def __len__(self) -> int:
        return len(self._skills)

    def __contains__(self, name: str) -> bool:
        return name in self._skills

    def __repr__(self) -> str:
        counts = {cat: len(names) for cat, names in self._by_category.items() if names}
        return f"<SkillRegistryV2 skills={len(self)} categories={counts}>"
