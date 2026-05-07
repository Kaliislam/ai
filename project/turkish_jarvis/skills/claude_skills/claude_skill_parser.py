"""Awesome-claude-skills repo yapisi parser.

Her skill dizinindeki SKILL.md, README.md veya setup.md dosyalarini okur;
skill adi, aciklamasi, parametreler, kullanim ornekleri ve Markdown body'yi
cikararak SkillDefinition nesneleri uretir.
"""

from __future__ import annotations

import asyncio
import os
import re
import textwrap
from pathlib import Path
from typing import Any

from turkish_jarvis.skills.skill_parser import (
    SkillDefinition,
    SkillParameter,
    SkillTool,
)


def _extract_yaml_frontmatter(md_text: str) -> tuple[dict[str, Any], str]:
    """Bir Markdown metninin basindaki YAML frontmatter'i ayiklar.

    Returns:
        (frontmatter_dict, body_without_frontmatter)
    """
    if md_text.strip().startswith("---"):
        parts = md_text.split("---", 2)
        if len(parts) >= 3:
            raw_yaml = parts[1].strip()
            body = parts[2].strip()
            # Basit YAML key:value parse (yaml k"utuphanesi yoksa calisir)
            fm: dict[str, Any] = {}
            for line in raw_yaml.splitlines():
                if ":" in line and not line.strip().startswith("#"):
                    key, val = line.split(":", 1)
                    fm[key.strip()] = val.strip().strip('"').strip("'")
            return fm, body
    return {}, md_text


def _guess_category(skill_name: str, description: str, body: str) -> str:
    """Skill adi, aciklamasi ve iceriginden kategori tahmini yapar."""
    text = f"{skill_name} {description} {body}".lower()
    mapping = {
        "web": ["web", "browser", "http", "download", "url", "scrape", "fetch"],
        "dev": ["code", "git", "developer", "debug", "build", "test", "changelog", "artifact"],
        "data": ["csv", "data", "analysis", "research", "analytics", "lead"],
        "system": ["file", "organize", "system", "folder", "disk", "invoice"],
        "media": ["image", "video", "audio", "photo", "png", "jpg", "svg", "media", "theme", "canvas", "design"],
        "comm": ["email", "slack", "comms", "communication", "twitter", "social", "resume", "internal"],
    }
    for cat, keywords in mapping.items():
        for kw in keywords:
            if kw in text:
                return cat
    return "general"


def _extract_tools_from_body(body: str, skill_name: str) -> list[SkillTool]:
    """Markdown body'den olasi tool/ fonksiyon tanimlarini cikarir.

    Kod bloklari icindeki fonksiyon imzalari, bash script'ler veya
    acikca belirtilen 'Instructions' bolumleri taranir.
    """
    tools: list[SkillTool] = []
    # 1. Fonksiyon imzalari: `def function_name(...)` veya `async def function_name(...)`
    func_pattern = re.compile(
        r"(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)",
        re.MULTILINE,
    )
    for match in func_pattern.finditer(body):
        func_name = match.group(1)
        args_raw = match.group(2)
        params: list[SkillParameter] = []
        for arg in args_raw.split(","):
            arg = arg.strip()
            if not arg or arg == "self" or arg.startswith("*"):
                continue
            # type hint varsa ayir
            if ":" in arg:
                name, ptype = arg.split(":", 1)
                name = name.strip()
                ptype = ptype.strip().lower()
                # basit type map
                if "str" in ptype:
                    ptype = "string"
                elif "int" in ptype:
                    ptype = "integer"
                elif "float" in ptype:
                    ptype = "number"
                elif "bool" in ptype:
                    ptype = "boolean"
                elif "list" in ptype or "dict" in ptype:
                    ptype = "array"
                else:
                    ptype = "string"
            else:
                name = arg
                ptype = "string"
            # default deger varsa ayir
            default: Any = None
            if "=" in name:
                name, default_str = name.split("=", 1)
                name = name.strip()
                default = default_str.strip().strip('"').strip("'")
            params.append(SkillParameter(name=name, ptype=ptype, required=(default is None), default=default))
        tools.append(
            SkillTool(
                name=func_name,
                description=f"Auto-extracted function from {skill_name}",
                parameters=params,
                returns="string",
            )
        )

    # 2. Bash script calistirma ornekleri: ```bash python scripts/xxx.py ...
    bash_pattern = re.compile(r"```bash\s*\n\s*python\s+scripts/(\S+)\.py\s+(.*?)\n", re.DOTALL)
    for match in bash_pattern.finditer(body):
        script_name = match.group(1)
        args_line = match.group(2).strip()
        params = []
        # "URL" gibi buyuk harfli placeholder'lari parametre olarak al
        for ph in re.findall(r'"[^"]*"|\S+', args_line):
            ph = ph.strip().strip('"')
            if ph.startswith("-") or ph.startswith("$"):
                continue
            if ph.isupper() or ("{" in ph and "}" in ph):
                pname = ph.strip("{}").lower().replace(" ", "_")
                if pname not in [p.name for p in params]:
                    params.append(SkillParameter(name=pname, ptype="string", required=True))
        if params:
            tools.append(
                SkillTool(
                    name=script_name,
                    description=f"Run script extracted from {skill_name}",
                    parameters=params,
                    returns="string",
                )
            )
    return tools


def _extract_examples(body: str) -> list[str]:
    """Markdown body'den '## Example' bolumlerini cikarir."""
    examples: list[str] = []
    pattern = re.compile(r"##\s*Example[s]?\s*\n(.*?)(?=\n##\s|\Z)", re.DOTALL | re.IGNORECASE)
    for match in pattern.finditer(body):
        examples.append(textwrap.dedent(match.group(1).strip()))
    return examples


def parse_claude_skill_dir(skill_dir: Path) -> SkillDefinition | None:
    """Bir skill dizinini tarar ve SkillDefinition uretir.

    Oncelikli dosya sirasi: SKILL.md > README.md > setup.md
    """
    candidates = ["SKILL.md", "README.md", "readme.md", "setup.md", "SETUP.md"]
    skill_file: Path | None = None
    for cand in candidates:
        candidate = skill_dir / cand
        if candidate.exists():
            skill_file = candidate
            break

    if skill_file is None:
        return None

    raw = skill_file.read_text(encoding="utf-8")
    fm, body = _extract_yaml_frontmatter(raw)

    name = fm.get("name", skill_dir.name)
    description = fm.get("description", "")
    category = _guess_category(name, description, body)

    tools = _extract_tools_from_body(body, name)
    examples = _extract_examples(body)

    # YAML'da tools listesi varsa onu kullan
    raw_tools = fm.get("tools")
    if raw_tools and isinstance(raw_tools, list):
        for t in raw_tools:
            if isinstance(t, dict):
                params = [
                    SkillParameter(
                        name=p.get("name", "arg"),
                        ptype=p.get("type", "string"),
                        description=p.get("description", ""),
                        required=p.get("required", True),
                    )
                    for p in t.get("parameters", [])
                ]
                tools.append(
                    SkillTool(
                        name=t.get("name", "tool"),
                        description=t.get("description", ""),
                        parameters=params,
                        returns=t.get("returns", "string"),
                    )
                )

    return SkillDefinition(
        name=name,
        description=description,
        category=category,
        version=fm.get("version", "1.0.0"),
        author=fm.get("author", ""),
        license=fm.get("license", ""),
        body=body,
        tools=tools,
        examples=examples,
        raw_frontmatter=fm,
    )


def discover_skills(repo_root: Path) -> list[SkillDefinition]:
    """Awesome-claude-skills repo kokunden tum skill dizinlerini kesfet.

    Her alt dizin bir skill olarak degerlendirilir. Gizli dizinler (.
    ile baslayan), __pycache__, scripts, docs, .github vb. goz ardi edilir.
    """
    skills: list[SkillDefinition] = []
    ignore_names = {
        ".git",
        ".github",
        "scripts",
        "docs",
        "__pycache__",
        "node_modules",
        "venv",
        ".venv",
        "resources",
        "assets",
        "templates",
        "themes",
        "examples",
    }
    if not repo_root.exists():
        return skills

    for item in repo_root.iterdir():
        if not item.is_dir():
            continue
        if item.name.startswith(".") or item.name in ignore_names:
            continue
        skill = parse_claude_skill_dir(item)
        if skill is not None:
            skills.append(skill)
    return skills


async def fetch_skill_from_github(skill_name: str, repo: str = "ComposioHQ/awesome-claude-skills", branch: str = "master") -> SkillDefinition | None:
    """GitHub'dan tek bir skill'in SKILL.md dosyasini indirir ve parse eder.

    Args:
        skill_name: Skill dizin adi (ornegin 'file-organizer').
        repo: 'owner/repo' formatinda GitHub repo.
        branch: Dal adi.

    Returns:
        SkillDefinition veya hata durumunda None.
    """
    import urllib.request
    import asyncio

    url = f"https://raw.githubusercontent.com/{repo}/{branch}/{skill_name}/SKILL.md"
    try:
        loop = asyncio.get_running_loop()
        raw = await loop.run_in_executor(None, lambda: urllib.request.urlopen(url, timeout=20).read().decode("utf-8"))
    except Exception:
        return None

    fm, body = _extract_yaml_frontmatter(raw)
    name = fm.get("name", skill_name)
    description = fm.get("description", "")
    category = _guess_category(name, description, body)
    tools = _extract_tools_from_body(body, name)
    examples = _extract_examples(body)

    return SkillDefinition(
        name=name,
        description=description,
        category=category,
        version=fm.get("version", "1.0.0"),
        author=fm.get("author", ""),
        license=fm.get("license", ""),
        body=body,
        tools=tools,
        examples=examples,
        raw_frontmatter=fm,
    )


if __name__ == "__main__":  # pragma: no cover
    # Basit CLI test
    import sys

    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        skills = discover_skills(path)
        for s in skills:
            print(f"- {s.name} ({s.category}): {s.description[:80]}...")
            print(f"  tools: {[t.name for t in s.tools]}")
    else:
        print("Usage: python claude_skill_parser.py <repo_root>")
