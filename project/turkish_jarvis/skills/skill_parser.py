"""SKILL.md format parser for agent skills.

Parses SKILL.md files with YAML frontmatter and Markdown body into structured
SkillDefinition objects that can be loaded into the skill registry.

Supported frontmatter fields:
    - name: str (required) — skill identifier
    - description: str (required) — when to trigger / what it does
    - category: str (optional) — web, dev, data, system, media, comm
    - version: str (optional) — semantic version
    - author: str (optional)
    - license: str (optional)
    - tools: list[dict] (optional) — list of functions the skill provides
    - parameters: dict (optional) — JSON-schema-like parameter definitions
    - examples: list[str] (optional) — usage examples
"""

from __future__ import annotations

import os
import re
import textwrap
from dataclasses import dataclass, field
from typing import Any


try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


@dataclass
class SkillParameter:
    """Represents a single parameter for a skill function."""

    name: str
    ptype: str = "string"
    description: str = ""
    required: bool = True
    default: Any = None
    enum: list[str] | None = None


@dataclass
class SkillTool:
    """Represents a tool/function exposed by a skill."""

    name: str
    description: str = ""
    parameters: list[SkillParameter] = field(default_factory=list)
    returns: str = ""


@dataclass
class SkillDefinition:
    """Structured representation of a parsed SKILL.md file."""

    name: str
    description: str = ""
    category: str = "general"
    version: str = "0.1.0"
    author: str = ""
    license: str = ""
    body: str = ""
    tools: list[SkillTool] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    raw_frontmatter: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_openai_schema(self) -> list[dict[str, Any]]:
        """Convert tools to OpenAI-compatible function-calling schemas."""
        schemas: list[dict[str, Any]] = []
        for tool in self.tools:
            props: dict[str, Any] = {}
            required: list[str] = []
            for p in tool.parameters:
                prop: dict[str, Any] = {
                    "type": p.ptype,
                    "description": p.description,
                }
                if p.enum is not None:
                    prop["enum"] = p.enum
                if p.default is not None:
                    prop["default"] = p.default
                props[p.name] = prop
                if p.required:
                    required.append(p.name)
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": f"{self.name}__{tool.name}",
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": props,
                            "required": required,
                        },
                    },
                }
            )
        return schemas


def _extract_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Split YAML frontmatter from Markdown body.

    Returns:
        Tuple of (frontmatter dict, markdown body).
    """
    # Match --- ... --- anywhere at the start of the file (allow leading whitespace)
    match = re.search(r"^\s*---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content

    fm_text, body = match.group(1), match.group(2)
    if yaml is not None:
        try:
            frontmatter = yaml.safe_load(fm_text) or {}
        except yaml.YAMLError:
            frontmatter = {}
    else:
        # Fallback: very simple key: value parser for basic cases
        frontmatter = _simple_yaml_parse(fm_text)
    return frontmatter, body


def _simple_yaml_parse(text: str) -> dict[str, Any]:
    """Ultra-light YAML subset parser when PyYAML is unavailable."""
    result: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] = []
    indent_stack: list[tuple[int, str]] = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Check if it's a list item
        if stripped.startswith("-"):
            item = stripped[1:].strip()
            current_list.append(item)
            if current_key:
                result[current_key] = current_list[:]
            continue
        # Key: value
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            # Remove surrounding quotes
            if (val.startswith('"') and val.endswith('"')) or (
                val.startswith("'") and val.endswith("'")
            ):
                val = val[1:-1]
            result[key] = val
            current_key = key
            current_list = []
    return result


def _parse_tools_from_frontmatter(tools_data: list[dict[str, Any]] | None) -> list[SkillTool]:
    """Parse the 'tools' list from frontmatter into SkillTool objects."""
    tools: list[SkillTool] = []
    if not tools_data:
        return tools

    for t in tools_data:
        if isinstance(t, str):
            # Just a tool name
            tools.append(SkillTool(name=t))
            continue
        if not isinstance(t, dict):
            continue
        name = t.get("name", "")
        if not name:
            continue
        description = t.get("description", "")
        returns = t.get("returns", "")
        params: list[SkillParameter] = []
        raw_params = t.get("parameters", [])
        if isinstance(raw_params, dict):
            # Object-form parameters: each key is a parameter
            for pname, pdef in raw_params.items():
                if isinstance(pdef, dict):
                    params.append(
                        SkillParameter(
                            name=pname,
                            ptype=pdef.get("type", "string"),
                            description=pdef.get("description", ""),
                            required=pdef.get("required", True),
                            default=pdef.get("default"),
                            enum=pdef.get("enum"),
                        )
                    )
                else:
                    params.append(SkillParameter(name=pname, description=str(pdef)))
        elif isinstance(raw_params, list):
            for p in raw_params:
                if isinstance(p, dict):
                    params.append(
                        SkillParameter(
                            name=p.get("name", ""),
                            ptype=p.get("type", "string"),
                            description=p.get("description", ""),
                            required=p.get("required", True),
                            default=p.get("default"),
                            enum=p.get("enum"),
                        )
                    )
                elif isinstance(p, str):
                    params.append(SkillParameter(name=p))
        tools.append(SkillTool(name=name, description=description, parameters=params, returns=returns))
    return tools


def _extract_examples(body: str) -> list[str]:
    """Extract code-block examples from the Markdown body."""
    examples: list[str] = []
    # Match ```python ... ``` blocks
    for match in re.finditer(r"```(?:python)?\n(.*?)```", body, re.DOTALL):
        examples.append(textwrap.dedent(match.group(1)).strip())
    return examples


def _normalize_category(category: str) -> str:
    """Map a category string to one of the six canonical categories."""
    mapping = {
        "web": ["web", "scraping", "search", "browser", "http", "api", "url"],
        "dev": ["dev", "development", "code", "coding", "programming", "git", "build", "deploy"],
        "data": ["data", "database", "analytics", "csv", "json", "sql", "pandas", "analysis"],
        "system": ["system", "sys", "os", "file", "shell", "process", "management", "config"],
        "media": ["media", "image", "video", "audio", "photo", "picture", "sound", "music"],
        "comm": ["comm", "communication", "email", "slack", "social", "chat", "message", "notify"],
    }
    cat_lower = category.lower().strip()
    for canonical, aliases in mapping.items():
        if cat_lower in aliases:
            return canonical
    return "general"


def parse_skill_md(content: str) -> SkillDefinition:
    """Parse a SKILL.md file content into a SkillDefinition.

    Args:
        content: Full text of a SKILL.md file.

    Returns:
        A populated SkillDefinition dataclass.

    Raises:
        ValueError: If required frontmatter fields (name, description) are missing.
    """
    frontmatter, body = _extract_frontmatter(content)

    name = frontmatter.get("name", "").strip()
    if not name:
        # Try to extract from first H1 heading if frontmatter is absent
        h1_match = re.search(r"^#\s+(.+)", body, re.MULTILINE)
        if h1_match:
            name = h1_match.group(1).strip().lower().replace(" ", "-")
        else:
            raise ValueError("SKILL.md must have a 'name' in frontmatter or a top-level heading.")

    description = frontmatter.get("description", "").strip()
    if not description:
        # Try to extract first paragraph after H1
        para_match = re.search(r"^#\s+.+\n\n(.+?)(?:\n\n|\n##)", body, re.DOTALL)
        if para_match:
            description = para_match.group(1).strip()

    category = _normalize_category(frontmatter.get("category", "general"))
    version = frontmatter.get("version", "0.1.0")
    author = frontmatter.get("author", "")
    license_ = frontmatter.get("license", "")

    tools = _parse_tools_from_frontmatter(frontmatter.get("tools"))
    examples = _extract_examples(body)
    # Also pick up explicit examples list from frontmatter
    if "examples" in frontmatter and isinstance(frontmatter["examples"], list):
        for ex in frontmatter["examples"]:
            if isinstance(ex, str) and ex not in examples:
                examples.append(ex)

    return SkillDefinition(
        name=name,
        description=description,
        category=category,
        version=str(version),
        author=author,
        license=license_,
        body=body.strip(),
        tools=tools,
        examples=examples,
        raw_frontmatter=frontmatter,
    )


async def fetch_skill_md_from_github(repo: str, skill_path: str) -> str:
    """Download a SKILL.md from GitHub via raw.githubusercontent.com.

    Args:
        repo: Repository in "owner/repo" format.
        skill_path: Path to the SKILL.md inside the repo.

    Returns:
        Raw text content of the SKILL.md file.

    Raises:
        ValueError: If the download fails.
    """
    import aiohttp

    # Normalize path
    skill_path = skill_path.lstrip("/")
    url = f"https://raw.githubusercontent.com/{repo}/main/{skill_path}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.text()
            # Try "master" branch fallback
            url_master = f"https://raw.githubusercontent.com/{repo}/master/{skill_path}"
            async with session.get(url_master) as resp2:
                if resp2.status == 200:
                    return await resp2.text()
                raise ValueError(
                    f"Failed to download SKILL.md from {repo}/{skill_path} "
                    f"(HTTP {resp.status} / {resp2.status})"
                )


# Simple test harness when run directly
if __name__ == "__main__":  # pragma: no cover
    _SAMPLE = """
---
name: web-scraper
description: "Scrape web pages and extract structured data."
category: web
version: 1.0.0
tools:
  - name: fetch_page
    description: "Fetch a web page and return its HTML."
    parameters:
      url:
        type: string
        description: "Page URL to fetch."
        required: true
  - name: extract_links
    description: "Extract all links from HTML."
    parameters:
      html:
        type: string
        description: "Raw HTML string."
        required: true
examples:
  - "fetch_page(url='https://example.com')"
---

# Web Scraper

This skill provides web scraping capabilities.

## Workflow

1. Fetch the page HTML.
2. Parse and extract data.

```python
html = await fetch_page("https://example.com")
links = extract_links(html)
```
"""
    skill = parse_skill_md(_SAMPLE)
    print("Name:", skill.name)
    print("Category:", skill.category)
    print("Tools:", [t.name for t in skill.tools])
    print("Examples:", len(skill.examples))
    print("Schema sample:", skill.to_openai_schema()[0] if skill.tools else None)
