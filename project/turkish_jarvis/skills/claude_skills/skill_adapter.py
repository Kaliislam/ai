"""Claude skill'lerini TurkishJARVIS skill formatina donusturur.

`adapt_claude_skill(skill_dir)` bir SKILL.md dosyasini okur,
parseller ve projenin `SkillDefinition` + `GeneratedSkillModule`
formatina cevirir. Boylece Claude awesome-skills koleksiyonu
TurkishJARVIS skill registry'sine native olarak entegre olur.
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

from turkish_jarvis.skills.claude_skills.claude_skill_parser import (
    _extract_examples,
    _extract_tools_from_body,
    _extract_yaml_frontmatter,
    _guess_category,
    fetch_skill_from_github,
    parse_claude_skill_dir,
)
from turkish_jarvis.skills.skill_loader import GeneratedSkillModule, SkillLoader
from turkish_jarvis.skills.skill_parser import SkillDefinition, SkillParameter, SkillTool


# ---------------------------------------------------------------------------
# Code generation: Claude skill body -> Python module
# ---------------------------------------------------------------------------

def _generate_module_code(skill: SkillDefinition) -> str:
    """Bir SkillDefinition'dan calistirilabilir Python modulu uretir.

    Her tool icin async bir fonksiyon uretilir; fonksiyon govdesi
    LLM prompt'u olarak skill'in Markdown body + tool adi + parametrelerini
    icerir. Boylece her calistirmede guncel LLM yaniti alinir.
    """
    lines: list[str] = [
        '"""Auto-generated skill module for: {name}"""',
        "from __future__ import annotations",
        "import asyncio",
        "import json",
        "from typing import Any",
        "",
        "async def _llm_generate(prompt: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:",
        '    """Stub LLM caller — replaced at runtime by the real client."""',
        "    try:",
        '        from turkish_jarvis.llm.client import LLMClient  # type: ignore[import]',
        "        client = LLMClient()",
        "        return await client.generate(prompt, temperature=temperature, max_tokens=max_tokens)",
        "    except Exception:",
        "        return f'[LLM_STUB] {len(prompt)} chars'",
        "",
    ]

    for tool in skill.tools:
        params_sig = []
        for p in tool.parameters:
            default = ""
            if p.default is not None:
                default = f" = {repr(p.default)}"
            params_sig.append(f"{p.name}: {p.ptype}{default}")
        sig = ", ".join(params_sig) if params_sig else ""

        # Prompt olusturma
        prompt_body = textwrap.dedent(f"""
            You are executing the skill '{skill.name}' — tool '{tool.name}'.

            SKILL CONTEXT:
            {skill.body[:3000]}

            PARAMETERS:
            {{json.dumps(locals(), ensure_ascii=False, indent=2)}}

            Execute the tool according to the skill instructions.
            Return concise, structured output.
        """)

        func_lines = [
            f"async def {tool.name}({sig}) -> dict[str, Any]:",
            f'    """{tool.description or "Auto-generated tool"}"""',
            "    import json",
            f"    prompt = {repr(prompt_body.strip())}",
            '    raw = await _llm_generate(prompt, temperature=0.6, max_tokens=4096)',
            '    try:',
            '        return json.loads(raw)',
            '    except Exception:',
            '        return {"result": raw, "tool": "' + tool.name + '"}',
            "",
        ]
        lines.extend(func_lines)

    return "\n".join(lines).format(name=skill.name)


async def adapt_claude_skill(
    skill_dir: Path | str,
    loader: SkillLoader | None = None,
    register: bool = True,
) -> GeneratedSkillModule | None:
    """Claude skill dizinini TurkishJARVIS formatina donusturur.

    Args:
        skill_dir: Skill dizin yolu (yerel) veya GitHub'daki skill adi.
        loader: Mevcut SkillLoader; None ise yeni olusturulur.
        register: True ise loader'a kaydedilir.

    Returns:
        GeneratedSkillModule veya hata durumunda None.
    """
    skill_dir_path = Path(skill_dir) if not isinstance(skill_dir, str) or Path(skill_dir).exists() else None

    if skill_dir_path and skill_dir_path.exists():
        skill = parse_claude_skill_dir(skill_dir_path)
    else:
        # GitHub'dan fetch et
        skill_name = str(skill_dir).strip("/").split("/")[-1]
        skill = await fetch_skill_from_github(skill_name)

    if skill is None:
        return None

    # Tool bos ise body'den cikar
    if not skill.tools:
        skill.tools = _extract_tools_from_body(skill.body, skill.name)

    # Hic tool yoksa default bir 'execute' tool ekle
    if not skill.tools:
        skill.tools.append(
            SkillTool(
                name="execute",
                description=f"Execute the {skill.name} skill with user instructions",
                parameters=[
                    SkillParameter(name="instructions", ptype="string", description="User instructions", required=True),
                ],
                returns="string",
            )
        )

    code = _generate_module_code(skill)

    # Gecici modul olarak yaz ve yukle
    tmp_dir = Path(tempfile.gettempdir()) / "tj_claude_skills"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    mod_path = tmp_dir / f"{skill.name.replace('-', '_')}.py"
    mod_path.write_text(code, encoding="utf-8")

    spec = importlib.util.spec_from_file_location(skill.name, mod_path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    wrapper = GeneratedSkillModule(skill=skill, module=mod)

    if register and loader is not None:
        loader._loaded[skill.name] = wrapper  # type: ignore[attr-defined]

    return wrapper


class ClaudeSkillAdapter:
    """Toplu Claude skill adaptasyonu ve yonetimi.

    Kullanim:
        adapter = ClaudeSkillAdapter(loader=registry._loader)
        await adapter.load_all_local("/path/to/awesome-claude-skills")
        await adapter.load_from_github("file-organizer")
    """

    def __init__(self, loader: SkillLoader | None = None) -> None:
        self.loader = loader or SkillLoader()
        self.adapted: dict[str, GeneratedSkillModule] = {}

    async def load_all_local(self, repo_root: Path | str) -> list[GeneratedSkillModule]:
        """Yerel repo'daki tum skill'leri adapt et."""
        from turkish_jarvis.skills.claude_skills.claude_skill_parser import discover_skills

        skills = discover_skills(Path(repo_root))
        results: list[GeneratedSkillModule] = []
        for skill_def in skills:
            wrapper = await adapt_claude_skill(
                skill_dir=Path(repo_root) / skill_def.name,
                loader=self.loader,
                register=True,
            )
            if wrapper:
                self.adapted[wrapper.skill.name] = wrapper
                results.append(wrapper)
        return results

    async def load_from_github(self, skill_name: str) -> GeneratedSkillModule | None:
        """GitHub'dan tek bir skill indirip adapt et."""
        wrapper = await adapt_claude_skill(
            skill_dir=skill_name,
            loader=self.loader,
            register=True,
        )
        if wrapper:
            self.adapted[wrapper.skill.name] = wrapper
        return wrapper

    def list_adapted(self) -> list[str]:
        """Adapt edilmis skill isimlerini doner."""
        return list(self.adapted.keys())

    async def execute(self, skill_name: str, tool_name: str, **kwargs: Any) -> Any:
        """Adapt edilmis bir skill'in tool'unu calistirir."""
        wrapper = self.adapted.get(skill_name)
        if wrapper is None:
            raise KeyError(f"Skill '{skill_name}' not adapted.")
        return await wrapper.execute(tool_name, **kwargs)

    def get_skill_definition(self, skill_name: str) -> SkillDefinition | None:
        """Adapt edilmis skill'in SkillDefinition'ini doner."""
        wrapper = self.adapted.get(skill_name)
        return wrapper.skill if wrapper else None
