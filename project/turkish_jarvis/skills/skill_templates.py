"""Skill templates — boilerplate generators for new agent skills.

Provides:
    - SKILL.md frontmatter + body templates per category.
    - Python stub generation for quick implementation.
    - ``create_skill_template`` to scaffold a complete skill directory.
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path
from typing import Any

from turkish_jarvis.skills.skill_parser import SkillDefinition, SkillParameter, SkillTool


# ------------------------------------------------------------------
# Category-specific description snippets
# ------------------------------------------------------------------

_CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "web": "Web scraping, HTTP requests, API interactions, and browser automation.",
    "dev": "Development tasks including code generation, Git operations, build scripts, and deployment.",
    "data": "Data processing, CSV/JSON handling, database queries, and analytical pipelines.",
    "system": "System administration, file operations, process management, and OS-level tasks.",
    "media": "Image, video, and audio processing, generation, and manipulation.",
    "comm": "Communication, email, social media, chat, and notification workflows.",
    "general": "General-purpose utility skill for miscellaneous tasks.",
}

_CATEGORY_WORKFLOWS: dict[str, str] = {
    "web": textwrap.dedent(
        """\
        ## Workflow

        1. Identify the target URL or endpoint.
        2. Fetch or scrape the required data.
        3. Parse and extract structured information.
        4. Return or persist the results.

        ## Common Pitfalls

        - Always respect robots.txt.
        - Handle rate-limiting (HTTP 429) gracefully.
        - Validate URLs before making requests.
        """
    ),
    "dev": textwrap.dedent(
        """\
        ## Workflow

        1. Understand the codebase context.
        2. Generate or modify code according to best practices.
        3. Run linters / type-checkers.
        4. Provide usage examples or tests.

        ## Common Pitfalls

        - Do NOT hard-code secrets.
        - Prefer async I/O in network-bound tools.
        - Keep functions single-purpose and well-typed.
        """
    ),
    "data": textwrap.dedent(
        """\
        ## Workflow

        1. Load data from the specified source.
        2. Validate schema and handle missing values.
        3. Transform / analyse as requested.
        4. Export or visualise results.

        ## Common Pitfalls

        - Never mutate raw input in-place; work on copies.
        - Watch for memory usage with large files.
        - Sanitise SQL parameters to prevent injection.
        """
    ),
    "system": textwrap.dedent(
        """\
        ## Workflow

        1. Inspect the current system state.
        2. Identify the required operation (read, write, execute).
        3. Perform the operation with safety checks.
        4. Log the outcome and rollback on failure.

        ## Common Pitfalls

        - Never execute arbitrary shell commands without validation.
        - Check file permissions before destructive operations.
        - Avoid blocking the event loop with synchronous OS calls.
        """
    ),
    "media": textwrap.dedent(
        """\
        ## Workflow

        1. Accept or locate the media asset.
        2. Apply the requested transformation or generation.
        3. Optimise output format and quality.
        4. Save or stream the result.

        ## Common Pitfalls

        - Validate media formats before processing.
        - Guard against huge file sizes (OOM risk).
        - Prefer streaming for audio/video to reduce memory.
        """
    ),
    "comm": textwrap.dedent(
        """\
        ## Workflow

        1. Identify the communication channel and recipient.
        2. Compose the message according to channel constraints.
        3. Send with appropriate rate-limiting and retries.
        4. Confirm delivery or log failure.

        ## Common Pitfalls

        - Do NOT send unsolicited bulk messages.
        - Redact sensitive data before logging.
        - Respect API rate limits to avoid bans.
        """
    ),
    "general": textwrap.dedent(
        """\
        ## Workflow

        1. Analyse the user request.
        2. Delegate to the most specific sub-tool if applicable.
        3. Return a concise, actionable result.

        ## Common Pitfalls

        - Keep responses focused; avoid over-explaining.
        - Fall back gracefully when inputs are ambiguous.
        """
    ),
}


# ------------------------------------------------------------------
# SKILL.md template
# ------------------------------------------------------------------

_SKILL_MD_TEMPLATE = textwrap.dedent(
    """\
    ---
    name: {name}
    description: {description}
    category: {category}
    version: {version}
    author: {author}
    license: {license}
    tools:
    {tools_yaml}
    examples:
    {examples_yaml}
    ---

    # {title}

    {description}

    {workflow}

    ## Example Usage

    ```python
    # TODO: Add a concrete example
    ```
    """
)


# ------------------------------------------------------------------
# Python module stub template
# ------------------------------------------------------------------

_PYTHON_STUB_TEMPLATE = textwrap.dedent(
    """\
    \"\"\"Auto-generated skill stub for {name}.

    Category : {category}
    Version  : {version}
    Author   : {author}
    \"\"\"

    from typing import Any

    SKILL_NAME = {name!r}
    SKILL_DESCRIPTION = {description!r}
    SKILL_CATEGORY = {category!r}
    SKILL_VERSION = {version!r}
    SKILL_AUTHOR = {author!r}
    SKILL_LICENSE = {license!r}

    {functions}

    SKILL_TOOLS = {tools_dict!r}
    """
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _indent_yaml_list(items: list[str], indent: int = 2) -> str:
    """Indent a list of strings as YAML list items."""
    prefix = " " * indent + "- "
    return "\n".join(f"{prefix}{item}" for item in items)


def _tools_to_yaml(tools: list[SkillTool]) -> str:
    """Serialize a list of SkillTools into a YAML snippet."""
    if not tools:
        return '  []'
    lines: list[str] = []
    for t in tools:
        lines.append(f"  - name: {t.name}")
        lines.append(f"    description: {t.description or ''!r}")
        if t.parameters:
            lines.append("    parameters:")
            for p in t.parameters:
                lines.append(f"      {p.name}:")
                lines.append(f"        type: {p.ptype}")
                lines.append(f"        description: {p.description or ''!r}")
                if p.required:
                    lines.append("        required: true")
                if p.default is not None:
                    lines.append(f"        default: {p.default!r}")
                if p.enum is not None:
                    lines.append(f"        enum: {p.enum!r}")
    return "\n".join(lines)


def _examples_to_yaml(examples: list[str]) -> str:
    """Serialize examples into YAML list format."""
    if not examples:
        return '  []'
    lines: list[str] = []
    for ex in examples:
        for line in ex.splitlines():
            lines.append(f"  - {line!r}")
    return "\n".join(lines) if lines else '  []'


def _tools_to_python_stub(tools: list[SkillTool]) -> str:
    """Generate async function stubs from SkillTool definitions."""
    stubs: list[str] = []
    for t in tools:
        params: list[str] = []
        for p in t.parameters:
            py_type = _json_type_to_python(p.ptype)
            if p.default is not None:
                params.append(f"{p.name}: {py_type} = {p.default!r}")
            elif not p.required:
                params.append(f"{p.name}: {py_type} | None = None")
            else:
                params.append(f"{p.name}: {py_type}")
        sig = ", ".join(params)
        stub = textwrap.dedent(
            f"""\
            async def {t.name}({sig}) -> Any:
                \"\"\"{t.description or f"Execute {t.name}."}\"\"\"
                # TODO: Implement the tool logic here.
                pass

            """
        )
        stubs.append(stub)
    return "\n".join(stubs)


def _json_type_to_python(jtype: str) -> str:
    mapping = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
        "null": "None",
    }
    return mapping.get(jtype.lower(), "Any")


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def create_skill_template(
    name: str,
    description: str,
    category: str = "general",
    version: str = "0.1.0",
    author: str = "",
    license: str = "MIT",
    tools: list[SkillTool] | None = None,
    examples: list[str] | None = None,
) -> tuple[str, str, SkillDefinition]:
    """Generate a full skill scaffold: SKILL.md body + Python stub + SkillDefinition.

    Args:
        name: Skill identifier (kebab-case recommended).
        description: When to trigger / what it does.
        category: One of web, dev, data, system, media, comm, general.
        version: Semantic version string.
        author: Author name or handle.
        license: License identifier.
        tools: Optional list of SkillTool definitions.
        examples: Optional list of example code strings.

    Returns:
        Tuple of (skill_md_text, python_stub_text, SkillDefinition).
    """
    cat = category if category in ("web", "dev", "data", "system", "media", "comm", "general") else "general"
    tools = tools or []
    examples = examples or []

    # Build the SKILL.md text
    title = name.replace("-", " ").replace("_", " ").title()
    workflow = _CATEGORY_WORKFLOWS.get(cat, _CATEGORY_WORKFLOWS["general"])
    tools_yaml = _tools_to_yaml(tools)
    examples_yaml = _examples_to_yaml(examples)

    skill_md = _SKILL_MD_TEMPLATE.format(
        name=name,
        description=description,
        category=cat,
        version=version,
        author=author or "Anonymous",
        license=license,
        tools_yaml=tools_yaml,
        examples_yaml=examples_yaml,
        title=title,
        workflow=workflow,
    )

    # Build the Python stub
    tools_dict = {
        t.name: {
            "description": t.description,
            "parameters": [{"name": p.name, "type": p.ptype} for p in t.parameters],
        }
        for t in tools
    }
    python_stub = _PYTHON_STUB_TEMPLATE.format(
        name=name,
        description=description,
        category=cat,
        version=version,
        author=author or "Anonymous",
        license=license,
        functions=_tools_to_python_stub(tools),
        tools_dict=tools_dict,
    )

    # Build the SkillDefinition
    skill_def = SkillDefinition(
        name=name,
        description=description,
        category=cat,
        version=version,
        author=author or "Anonymous",
        license=license,
        body=workflow,
        tools=tools,
        examples=examples,
    )

    return skill_md, python_stub, skill_def


def scaffold_skill_directory(
    base_path: str,
    name: str,
    description: str,
    category: str = "general",
    version: str = "0.1.0",
    author: str = "",
    license: str = "MIT",
    tools: list[SkillTool] | None = None,
    examples: list[str] | None = None,
) -> Path:
    """Create a complete skill directory on disk.

    Layout::

        <base_path>/<name>/
        ├── SKILL.md
        ├── __init__.py
        ├── skill.py
        ├── scripts/
        ├── references/
        └── assets/

    Args:
        base_path: Parent directory where the skill folder will be created.
        name: Skill identifier.
        description, category, version, author, license: Skill metadata.
        tools: Tool definitions.
        examples: Example strings.

    Returns:
        Path to the created skill directory.
    """
    skill_md, python_stub, _ = create_skill_template(
        name=name,
        description=description,
        category=category,
        version=version,
        author=author,
        license=license,
        tools=tools,
        examples=examples,
    )

    root = Path(base_path) / name
    root.mkdir(parents=True, exist_ok=True)

    # Write SKILL.md
    (root / "SKILL.md").write_text(skill_md, encoding="utf-8")

    # Write __init__.py
    init_py = textwrap.dedent(
        f"""\
        \"\"\"Skill package: {name}.

        Category: {category}
        Version : {version}
        \"\"\"

        from .skill import *
        """
    )
    (root / "__init__.py").write_text(init_py, encoding="utf-8")

    # Write skill.py
    (root / "skill.py").write_text(python_stub, encoding="utf-8")

    # Create optional subdirectories
    for sub in ("scripts", "references", "assets"):
        (root / sub).mkdir(exist_ok=True)
        # Add .gitkeep so they are tracked by git even if empty
        (root / sub / ".gitkeep").touch()

    return root


# ------------------------------------------------------------------
# Pre-baked example templates for quick copy-paste
# ------------------------------------------------------------------


def web_search_skill() -> tuple[str, str, SkillDefinition]:
    """Return a ready-made web search skill template."""
    return create_skill_template(
        name="web-search",
        description="Search the web using a search engine and return ranked results.",
        category="web",
        tools=[
            SkillTool(
                name="search",
                description="Perform a web search and return results.",
                parameters=[
                    SkillParameter(name="query", ptype="string", description="Search query string.", required=True),
                    SkillParameter(name="max_results", ptype="integer", description="Maximum number of results.", required=False, default=5),
                ],
            ),
        ],
        examples=["results = await search(query='Python asyncio tutorial', max_results=10)"],
    )


def dev_linter_skill() -> tuple[str, str, SkillDefinition]:
    """Return a ready-made linter / code-review skill template."""
    return create_skill_template(
        name="code-linter",
        description="Run static analysis on Python source files and report issues.",
        category="dev",
        tools=[
            SkillTool(
                name="lint_file",
                description="Lint a single Python file and return a report.",
                parameters=[
                    SkillParameter(name="path", ptype="string", description="Path to the Python file.", required=True),
                ],
            ),
        ],
        examples=["report = await lint_file(path='src/main.py')"],
    )


def data_csv_skill() -> tuple[str, str, SkillDefinition]:
    """Return a ready-made CSV processing skill template."""
    return create_skill_template(
        name="csv-processor",
        description="Load, transform, and save CSV files.",
        category="data",
        tools=[
            SkillTool(
                name="load_csv",
                description="Load a CSV file into a list of dictionaries.",
                parameters=[
                    SkillParameter(name="path", ptype="string", description="CSV file path.", required=True),
                    SkillParameter(name="delimiter", ptype="string", description="Field delimiter.", required=False, default=","),
                ],
            ),
            SkillTool(
                name="save_csv",
                description="Save a list of dictionaries to a CSV file.",
                parameters=[
                    SkillParameter(name="path", ptype="string", description="Output CSV file path.", required=True),
                    SkillParameter(name="rows", ptype="array", description="List of row dictionaries.", required=True),
                ],
            ),
        ],
        examples=["rows = await load_csv(path='data.csv')"],
    )


def system_disk_skill() -> tuple[str, str, SkillDefinition]:
    """Return a ready-made disk-usage skill template."""
    return create_skill_template(
        name="disk-monitor",
        description="Monitor disk space and report usage statistics.",
        category="system",
        tools=[
            SkillTool(
                name="get_usage",
                description="Return disk usage for the given path.",
                parameters=[
                    SkillParameter(name="path", ptype="string", description="Directory path to check.", required=False, default="/"),
                ],
            ),
        ],
        examples=["usage = await get_usage(path='/home')"],
    )


def media_thumbnail_skill() -> tuple[str, str, SkillDefinition]:
    """Return a ready-made image thumbnail skill template."""
    return create_skill_template(
        name="image-thumbnail",
        description="Generate thumbnails from image files.",
        category="media",
        tools=[
            SkillTool(
                name="create_thumbnail",
                description="Create a resized thumbnail of an image.",
                parameters=[
                    SkillParameter(name="input_path", ptype="string", description="Source image path.", required=True),
                    SkillParameter(name="output_path", ptype="string", description="Destination thumbnail path.", required=True),
                    SkillParameter(name="size", ptype="integer", description="Max width/height in pixels.", required=False, default=128),
                ],
            ),
        ],
        examples=["await create_thumbnail(input_path='photo.jpg', output_path='thumb.jpg', size=256)"],
    )


def comm_email_skill() -> tuple[str, str, SkillDefinition]:
    """Return a ready-made email composition skill template."""
    return create_skill_template(
        name="email-compose",
        description="Compose and draft emails based on user instructions.",
        category="comm",
        tools=[
            SkillTool(
                name="draft_email",
                description="Draft a professional email body given bullet points.",
                parameters=[
                    SkillParameter(name="recipient", ptype="string", description="Recipient name or email.", required=True),
                    SkillParameter(name="subject", ptype="string", description="Email subject line.", required=True),
                    SkillParameter(name="points", ptype="array", description="List of bullet points to cover.", required=True),
                    SkillParameter(name="tone", ptype="string", description="Tone: formal, casual, friendly.", required=False, default="formal", enum=["formal", "casual", "friendly"]),
                ],
            ),
        ],
        examples=["email = await draft_email(recipient='Alice', subject='Project update', points=['Milestone reached', 'Next steps'])"],
    )
