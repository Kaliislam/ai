"""Claude awesome-skills implementasyonlari.

ComposioHQ/awesome-claude-skills reposundaki en populer 17 skill'in
async Python wrapper'lari. Her skill ~50-150 satir, pratik ve LLM
prompt template + instruction based calisir.

Skills
------
artifacts_builder        — AI artifact olusturma (JSON, HTML, SVG)
brand_guidelines         — Marka rehberi olusturma
canvas_design            — Canvas / sema tasarimi
changelog_generator      — Changelog uretimi
content_research_writer  — Icerik arastirma + yazma
document_skills          — Dokuman isleme
file_organizer           — Dosya organize etme
image_enhancer           — Gorsel prompt gelistirme
internal_comms           — Iletisim sablonlari
invoice_organizer        — Fatura organize etme
lead_research_assistant  — Lead arastirma
meeting_insights_analyzer — Toplanti analizi
tailored_resume_generator — Ozellestirilmis CV
theme_factory            — Tema / UI olusturma
twitter_algorithm_optimizer — Sosyal medya optimize
video_downloader         — Video indirme / cozumleme
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from turkish_jarvis.skills.skill_parser import SkillDefinition


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _llm_generate(
    prompt: str,
    model: str = "default",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """Harici LLM API'sine istek atan basit wrapper.

    TurkceJARVIS projesinde mevcut LLM istemcisi varsa onu kullanir;
yoksa basit bir stub doner (unit test / offline calismasi icin).
    """
    try:
        # Proje icinde varsa orijinal LLM client'i kullan
        from turkish_jarvis.llm.client import LLMClient  # type: ignore[import]
        client = LLMClient(model=model)
        return await client.generate(prompt, temperature=temperature, max_tokens=max_tokens)
    except Exception:
        # Offline / test modu: stub yanit
        await asyncio.sleep(0.05)
        return f"[LLM_STUB] Prompt length: {len(prompt)} chars | model={model}"


async def _web_search(query: str, count: int = 5) -> list[dict[str, str]]:
    """Mevcut web_search modulunu kullanir."""
    try:
        # Web search araci proje icinde farkli yerlerde olabilir
        import importlib
        for mod_path in (
            "turkish_jarvis.tools.web_search",
            "turkish_jarvis.skills.web.search",
            "turkish_jarvis.skills.web",
        ):
            try:
                mod = importlib.import_module(mod_path)
                if hasattr(mod, "web_search"):
                    result = await mod.web_search(query, count=count)  # type: ignore[operator]
                    if result:
                        return result  # type: ignore[return-value]
            except Exception:
                continue
    except Exception:
        pass
    # Stub
    return [{"title": f"Stub result for '{query}'", "link": "#", "snippet": "No web search available."}]


async def _browser_visit(url: str) -> str:
    """Mevcut browser aracini kullanir."""
    try:
        import importlib
        for mod_path in (
            "turkish_jarvis.tools.browser",
            "turkish_jarvis.skills.web.browser",
        ):
            try:
                mod = importlib.import_module(mod_path)
                if hasattr(mod, "browser_visit"):
                    return await mod.browser_visit(url)  # type: ignore[operator]
            except Exception:
                continue
    except Exception:
        pass
    return f"[BROWSER_STUB] Visited {url}"


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9_-]", "-", text.lower().strip())[:60].strip("-")


# ---------------------------------------------------------------------------
# 1. artifacts_builder
# ---------------------------------------------------------------------------

async def artifacts_builder(
    artifact_type: str = "html",
    description: str = "",
    content_data: dict[str, Any] | None = None,
    framework: str = "react",
    theme: str = "default",
) -> dict[str, Any]:
    """Claude.ai HTML artifact olusturur.

    Args:
        artifact_type: html | svg | json | mermaid
        description: Artifact'in amaci ve icerigi
        content_data: JSON verisi veya tablo icerigi
        framework: react | vanilla | tailwind
        theme: default | dark | light

    Returns:
        {"artifact_id", "html", "type", "bundle"}
    """
    prompt = textwrap.dedent(f"""
        You are an expert frontend developer. Create a self-contained {artifact_type} artifact.
        Framework: {framework}. Theme: {theme}.

        REQUIREMENTS:
        - Single-file output; all CSS/JS inlined.
        - Use modern design; avoid "AI slop" (no excessive purple gradients, all-center layouts).
        - Responsive, accessible, semantic HTML.

        DESCRIPTION: {description}

        DATA: {json.dumps(content_data, ensure_ascii=False, default=str) if content_data else "N/A"}

        Return ONLY the raw {artifact_type} code (no markdown fences).
    """)
    code = await _llm_generate(prompt, temperature=0.5, max_tokens=8192)
    artifact_id = f"art-{_slugify(description)}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return {
        "artifact_id": artifact_id,
        "type": artifact_type,
        "framework": framework,
        "html": code if artifact_type == "html" else None,
        "svg": code if artifact_type == "svg" else None,
        "json": content_data if artifact_type == "json" else None,
        "bundle": code,
    }


# ---------------------------------------------------------------------------
# 2. brand_guidelines
# ---------------------------------------------------------------------------

async def brand_guidelines(
    brand_name: str = "",
    industry: str = "",
    tone: str = "professional",
    deliverables: list[str] | None = None,
    existing_colors: list[str] | None = None,
) -> dict[str, Any]:
    """Marka rehberi (brand guidelines) olusturur.

    Args:
        brand_name: Marka / sirket adi
        industry: Sektor (tech, fashion, food, vb.)
        tone: Ton (professional, playful, luxury, friendly)
        deliverables: colors | typography | logo_usage | voice | imagery
        existing_colors: Mevcut hex renkler (varsa)

    Returns:
        {"brand_name", "palette", "typography", "voice", "guidelines_md"}
    """
    deliverables = deliverables or ["colors", "typography", "voice"]
    prompt = textwrap.dedent(f"""
        You are a senior brand designer. Create a concise brand guidelines document.

        BRAND: {brand_name}
        INDUSTRY: {industry}
        TONE: {tone}
        DELIVERABLES: {', '.join(deliverables)}
        EXISTING COLORS: {', '.join(existing_colors) if existing_colors else 'None'}

        Output a JSON object with keys: palette (list of {{name, hex, usage}}),
        typography ({{heading_font, body_font, sizes}}), voice ({{adjectives, examples}}),
        and a short guidelines_md string.
    """)
    raw = await _llm_generate(prompt, temperature=0.6, max_tokens=4096)
    # LLM JSON ciktisini ayiklamaya calis
    try:
        data = json.loads(raw)
    except Exception:
        data = {"guidelines_md": raw}
    data.setdefault("brand_name", brand_name)
    data.setdefault("palette", [])
    data.setdefault("typography", {})
    data.setdefault("voice", {})
    return data


# ---------------------------------------------------------------------------
# 3. canvas_design
# ---------------------------------------------------------------------------

async def canvas_design(
    design_prompt: str = "",
    output_format: str = "png",
    dimensions: tuple[int, int] = (1024, 1024),
    style_preset: str = "modern_minimalist",
) -> dict[str, Any]:
    """Canvas / gorsel tasarimi uretir.

    Args:
        design_prompt: Gorsel tasarim aciklamasi
        output_format: png | pdf | svg
        dimensions: (width, height)
        style_preset: modern_minimalist | brutalist | organic | tech

    Returns:
        {"prompt_enhanced", "image_path", "format", "dimensions"}
    """
    philosophy_prompt = textwrap.dedent(f"""
        Create a visual design philosophy (1-2 word movement name + 4-6 paragraphs)
        for this request: "{design_prompt}". Style: {style_preset}.
        Emphasize meticulous craftsmanship, master-level execution, deep expertise.
        Minimal text, visual expression through form, space, color, composition.
    """)
    philosophy = await _llm_generate(philosophy_prompt, temperature=0.8, max_tokens=2048)

    image_prompt = textwrap.dedent(f"""
        Based on the following design philosophy, generate a detailed image generation prompt:

        {philosophy}

        The final visual should be a {dimensions[0]}x{dimensions[1]} {output_format}
        in {style_preset} style. No text paragraphs; pure visual design.
    """)
    enhanced = await _llm_generate(image_prompt, temperature=0.7, max_tokens=2048)

    # Proje icinde generate_image varsa kullan
    image_path = ""
    try:
        import importlib
        mod = importlib.import_module("turkish_jarvis.tools.image")
        if hasattr(mod, "generate_image"):
            safe_path = f"/mnt/agents/output/project/data/canvas_{_slugify(design_prompt)}.png"
            image_path = await mod.generate_image(  # type: ignore[operator]
                description=enhanced,
                output_file=safe_path,
                ratio="1:1",
            )
    except Exception:
        image_path = f"[PROMPT_READY] {enhanced[:200]}..."

    return {
        "prompt_enhanced": enhanced,
        "philosophy": philosophy,
        "image_path": image_path,
        "format": output_format,
        "dimensions": dimensions,
    }


# ---------------------------------------------------------------------------
# 4. changelog_generator
# ---------------------------------------------------------------------------

async def changelog_generator(
    repo_path: str = ".",
    since: str = "",
    until: str = "",
    version: str = "",
    style: str = "keepachangelog",
) -> dict[str, Any]:
    """Git commit'lerinden changelog uretir.

    Args:
        repo_path: Git repo yolu
        since: Baslangic tarihi / tag (ornegin 'v1.0.0' / '2024-01-01')
        until: Bitis tarihi / tag
        version: Surum numarasi
        style: keepachangelog | conventional | slack

    Returns:
        {"changelog_md", "categories", "commit_count"}
    """
    # Git log calistir
    cmd_parts = ["git", "-C", repo_path, "log", "--pretty=format:%h|%s|%b|END"]
    if since:
        cmd_parts += [f"{since}..{until}" if until else f"{since}..HEAD"]
    proc = await asyncio.create_subprocess_exec(
        *cmd_parts,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    raw_log = stdout.decode("utf-8", errors="ignore")

    commits = [c for c in raw_log.split("|END") if c.strip()]
    if not commits:
        return {"changelog_md": "No commits found.", "categories": {}, "commit_count": 0}

    prompt = textwrap.dedent(f"""
        You are a technical writer. Convert these git commits into a user-facing changelog.
        Version: {version or 'Unreleased'}
        Style: {style}

        COMMITS:
        {'\n'.join(commits[:100])}

        RULES:
        1. Categorize: Added, Changed, Fixed, Deprecated, Removed, Security.
        2. Translate technical commits into customer-friendly language.
        3. Exclude internal-only commits (refactor, test, ci).
        4. Use emojis per category.
        5. Output raw markdown (no code fences).
    """)
    changelog_md = await _llm_generate(prompt, temperature=0.4, max_tokens=4096)

    # Kategorileri ayikla
    categories: dict[str, list[str]] = {}
    for line in changelog_md.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            cat = line.strip("# ").strip().lower()
            categories.setdefault(cat, [])
        elif line.startswith("- ") and categories:
            list(categories.values())[-1].append(line.strip("- ").strip())

    return {
        "changelog_md": changelog_md,
        "categories": categories,
        "commit_count": len(commits),
        "version": version,
    }


# ---------------------------------------------------------------------------
# 5. content_research_writer
# ---------------------------------------------------------------------------

async def content_research_writer(
    topic: str = "",
    content_type: str = "blog",
    target_audience: str = "general",
    word_count: int = 800,
    sources: list[str] | None = None,
) -> dict[str, Any]:
    """Icerik arastirma + yazma.

    Args:
        topic: Yazilacak konu
        content_type: blog | linkedin | tweet_thread | newsletter | whitepaper
        target_audience: Hedef kitle
        word_count: Hedef kelime sayisi
        sources: Manuel kaynak URL'leri (varsa)

    Returns:
        {"title", "outline", "draft", "sources_used"}
    """
    # 1. Arastirma
    search_results = await _web_search(topic, count=5)
    source_snippets: list[str] = []
    for r in search_results[:3]:
        snippet = r.get("snippet", "")
        if snippet:
            source_snippets.append(f"- {r.get('title', '')}: {snippet}")

    # Manuel kaynaklar
    if sources:
        for url in sources[:3]:
            try:
                page = await _browser_visit(url)
                source_snippets.append(f"- {url}: {page[:500]}")
            except Exception:
                source_snippets.append(f"- {url}: [fetch failed]")

    # 2. Outline
    outline_prompt = textwrap.dedent(f"""
        Create a detailed outline for a {content_type} about "{topic}".
        Audience: {target_audience}. Target length: ~{word_count} words.

        RESEARCH SNIPPETS:
        {'\n'.join(source_snippets)}

        Return a JSON list of sections: [{{"heading", "key_points", "estimated_words"}}].
    """)
    outline_raw = await _llm_generate(outline_prompt, temperature=0.6, max_tokens=2048)
    try:
        outline = json.loads(outline_raw)
    except Exception:
        outline = [{"heading": "Draft", "key_points": outline_raw, "estimated_words": word_count}]

    # 3. Draft
    draft_prompt = textwrap.dedent(f"""
        Write the full {content_type} based on this outline:

        {json.dumps(outline, ensure_ascii=False, indent=2)}

        Topic: {topic}. Audience: {target_audience}. Approx {word_count} words.
        Use natural, engaging Turkish if the topic is Turkey-related; otherwise English.
        Cite sources inline where applicable.
    """)
    draft = await _llm_generate(draft_prompt, temperature=0.7, max_tokens=8192)

    # 4. Baslik
    title_prompt = f"Create a catchy title (max 8 words) for this {content_type}: {topic}"
    title = (await _llm_generate(title_prompt, temperature=0.8, max_tokens=128)).strip().strip('"')

    return {
        "title": title,
        "outline": outline,
        "draft": draft,
        "sources_used": [r.get("link", "#") for r in search_results],
        "content_type": content_type,
    }


# ---------------------------------------------------------------------------
# 6. document_skills
# ---------------------------------------------------------------------------

async def document_skills(
    action: str = "summarize",
    file_path: str = "",
    query: str = "",
    output_format: str = "markdown",
) -> dict[str, Any]:
    """Dokuman isleme: ozetleme, analiz, cevirme, format donusumu.

    Args:
        action: summarize | analyze | translate | convert | extract_qa
        file_path: Islenecek dosya yolu
        query: Spesifik soru / talimat
        output_format: markdown | json | html | text

    Returns:
        {"result", "action", "format", "word_count"}
    """
    path = Path(file_path)
    if not path.exists():
        return {"result": f"File not found: {file_path}", "action": action, "format": output_format, "word_count": 0}

    content = path.read_text(encoding="utf-8", errors="ignore")
    wc = len(content.split())

    if action == "summarize":
        prompt = f"Summarize the following document in {output_format}.\n\n{content[:12000]}"
    elif action == "analyze":
        prompt = f"Analyze the following document. Focus on: {query}\n\n{content[:12000]}"
    elif action == "translate":
        prompt = f"Translate the following document to {query}. Keep formatting:\n\n{content[:12000]}"
    elif action == "convert":
        prompt = f"Convert the following content to {output_format}. Preserve structure:\n\n{content[:12000]}"
    elif action == "extract_qa":
        prompt = textwrap.dedent(f"""
            Extract question-answer pairs from this document.
            Format: JSON list of {{"question", "answer", "page"}}.

            {content[:12000]}
        """)
    else:
        prompt = f"{query}\n\n{content[:12000]}"

    result = await _llm_generate(prompt, temperature=0.5, max_tokens=8192)
    return {"result": result, "action": action, "format": output_format, "word_count": wc}


# ---------------------------------------------------------------------------
# 7. file_organizer
# ---------------------------------------------------------------------------

async def file_organizer(
    source_dir: str = "",
    strategy: str = "by_type",
    dry_run: bool = True,
    patterns: list[str] | None = None,
) -> dict[str, Any]:
    """Dosya organize etme.

    Args:
        source_dir: Kaynak dizin
        strategy: by_type | by_date | by_name | by_project
        dry_run: True ise sadece plani doner, hicbir dosya tasinmaz
        patterns: Icine dahil edilecek glob desenleri (ornegin ['*.pdf', '*.jpg'])

    Returns:
        {"plan", "operations", "duplicates_found", "space_saved_mb"}
    """
    src = Path(source_dir).expanduser()
    if not src.exists():
        return {"plan": "Source directory not found.", "operations": [], "duplicates_found": 0, "space_saved_mb": 0.0}

    files = []
    patterns = patterns or ["*"]
    for pat in patterns:
        files.extend(src.rglob(pat))
    files = [f for f in files if f.is_file()]

    # Basit kategorizasyon
    by_category: dict[str, list[Path]] = {}
    for f in files:
        ext = f.suffix.lower()
        if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".heic"}:
            cat = "Images"
        elif ext in {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv"}:
            cat = "Videos"
        elif ext in {".pdf", ".doc", ".docx", ".txt", ".md", ".odt", ".rtf"}:
            cat = "Documents"
        elif ext in {".zip", ".tar", ".gz", ".bz2", ".7z", ".rar"}:
            cat = "Archives"
        elif ext in {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"}:
            cat = "Audio"
        elif ext in {".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm"}:
            cat = "Installers"
        else:
            cat = "Other"
        by_category.setdefault(cat, []).append(f)

    # Duplicate detection (basit: ayni boyut + ilk 4KB hash)
    import hashlib
    size_map: dict[int, list[Path]] = {}
    for f in files:
        try:
            size_map.setdefault(f.stat().st_size, []).append(f)
        except Exception:
            continue

    duplicates: list[tuple[Path, Path]] = []
    for size, candidates in size_map.items():
        if len(candidates) < 2:
            continue
        hash_map: dict[str, Path] = {}
        for c in candidates:
            try:
                with c.open("rb") as fh:
                    h = hashlib.blake2b(fh.read(4096), digest_size=16).hexdigest()
                if h in hash_map:
                    duplicates.append((hash_map[h], c))
                else:
                    hash_map[h] = c
            except Exception:
                continue

    operations: list[dict[str, str]] = []
    space_saved = 0.0
    for cat, cat_files in by_category.items():
        if strategy == "by_type":
            target = src / cat
        elif strategy == "by_date":
            # Tarihe gore yil/ay
            target = src / "ByDate"
        else:
            target = src / "Organized"
        for f in cat_files:
            if strategy == "by_date":
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    target = src / "ByDate" / str(mtime.year) / f"{mtime.month:02d}"
                except Exception:
                    target = src / "Organized"
            rel_src = f.relative_to(src)
            rel_dst = target / f.name
            operations.append({"op": "move", "src": str(rel_src), "dst": str(rel_dst.relative_to(src))})

    for orig, dup in duplicates:
        try:
            space_saved += dup.stat().st_size / (1024 * 1024)
        except Exception:
            pass
        operations.append({"op": "remove_duplicate", "src": str(dup.relative_to(src)), "ref": str(orig.relative_to(src))})

    # LLM ile plan ozeti
    plan_prompt = textwrap.dedent(f"""
        Summarize this file organization plan in 3-5 bullet points (Turkish):
        Strategy: {strategy}
        Total files: {len(files)}
        Categories: {list(by_category.keys())}
        Duplicates found: {len(duplicates)}
        Space saved (MB): {space_saved:.2f}
    """)
    plan = await _llm_generate(plan_prompt, temperature=0.4, max_tokens=512)

    # Dry-run disinda uygula
    if not dry_run:
        for op in operations:
            try:
                if op["op"] == "move":
                    dst_abs = src / op["dst"]
                    dst_abs.parent.mkdir(parents=True, exist_ok=True)
                    (src / op["src"]).rename(dst_abs)
                elif op["op"] == "remove_duplicate":
                    (src / op["src"]).unlink()
            except Exception:
                continue

    return {
        "plan": plan,
        "operations": operations,
        "duplicates_found": len(duplicates),
        "space_saved_mb": round(space_saved, 2),
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# 8. image_enhancer
# ---------------------------------------------------------------------------

async def image_enhancer(
    image_path: str = "",
    enhancement: str = "upscale",
    target_resolution: str = "2x",
    output_path: str = "",
    use_case: str = "general",
) -> dict[str, Any]:
    """Gorsel prompt gelistirme / iyilestirme.

    Args:
        image_path: Kaynak gorsel yolu
        enhancement: upscale | sharpen | denoise | compress_optimize | prompt_enhance
        target_resolution: 2x | 4x | original
        output_path: Cikis yolu (bos ise auto)
        use_case: general | social_media | presentation | print

    Returns:
        {"enhanced_prompt", "suggested_params", "output_path", "recommendations"}
    """
    from PIL import Image

    path = Path(image_path)
    if not path.exists():
        return {"enhanced_prompt": "", "suggested_params": {}, "output_path": "", "recommendations": ["File not found"]}

    try:
        img = Image.open(path)
        orig_w, orig_h = img.size
        fmt = img.format or "UNKNOWN"
    except Exception as e:
        return {"enhanced_prompt": "", "suggested_params": {}, "output_path": "", "recommendations": [str(e)]}

    if not output_path:
        stem = path.stem
        suffix = path.suffix
        output_path = str(path.with_name(f"{stem}_enhanced{suffix}"))

    prompt = textwrap.dedent(f"""
        You are an image optimization expert. Analyze this image and provide:
        1. An enhanced generation/prompt description
        2. Recommended processing parameters
        3. Platform-specific tips

        IMAGE INFO:
        - Dimensions: {orig_w}x{orig_h}
        - Format: {fmt}
        - Enhancement: {enhancement}
        - Target resolution: {target_resolution}
        - Use case: {use_case}

        Return JSON:
        {{
          "enhanced_prompt": "...",
          "suggested_params": {{"sharpen": true, "denoise": 0.5, ...}},
          "recommendations": ["..."]
        }}
    """)
    raw = await _llm_generate(prompt, temperature=0.5, max_tokens=2048)
    try:
        data = json.loads(raw)
    except Exception:
        data = {"enhanced_prompt": raw, "suggested_params": {}, "recommendations": []}

    # Basit Pillow islemleri (upscale, sharpen)
    try:
        if enhancement == "upscale":
            scale = 2 if target_resolution == "2x" else 4
            new_size = (orig_w * scale, orig_h * scale)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        elif enhancement == "sharpen":
            from PIL import ImageFilter
            img = img.filter(ImageFilter.SHARPEN)
        elif enhancement == "denoise":
            from PIL import ImageFilter
            img = img.filter(ImageFilter.SMOOTH_MORE)
        img.save(output_path)
    except Exception as e:
        data.setdefault("recommendations", []).append(f"Pillow processing error: {e}")

    data["output_path"] = output_path
    data["original_dimensions"] = (orig_w, orig_h)
    return data


# ---------------------------------------------------------------------------
# 9. internal_comms
# ---------------------------------------------------------------------------

async def internal_comms(
    comm_type: str = "status_report",
    audience: str = "team",
    data_points: list[str] | None = None,
    tone: str = "professional",
    length: str = "medium",
) -> dict[str, Any]:
    """Iletisim sablonlari uretir.

    Args:
        comm_type: status_report | newsletter | incident_report | faq | 3p_update | project_update | leadership_update
        audience: team | company | leadership | external
        data_points: Icerikte kullanilacak ana noktalar
        tone: professional | casual | urgent | celebratory
        length: short | medium | long

    Returns:
        {"subject", "body", "comm_type", "tone", "length"}
    """
    data_points = data_points or []
    length_map = {"short": "150-250 words", "medium": "300-500 words", "long": "600-900 words"}
    target_len = length_map.get(length, "300-500 words")

    templates = {
        "3p_update": (
            "3P Update – Progress, Plans, Problems",
            "Structure: 1) What we accomplished, 2) What we plan next, 3) Blockers/problems."
        ),
        "status_report": (
            "Weekly Status Report",
            "Structure: Summary, Completed, In Progress, Blockers, Next Week."
        ),
        "incident_report": (
            "Incident Report",
            "Structure: Summary, Timeline, Root Cause, Impact, Resolution, Prevention."
        ),
        "newsletter": (
            "Company Newsletter",
            "Structure: Welcome, Highlights, Team News, Upcoming, CTA."
        ),
        "faq": (
            "FAQ Document",
            "Structure: Q&A pairs with concise answers."
        ),
        "project_update": (
            "Project Update",
            "Structure: Status, Milestones, Risks, Resources, Next Steps."
        ),
        "leadership_update": (
            "Leadership Update",
            "Structure: Executive Summary, KPIs, Strategic Items, Decisions Needed."
        ),
    }

    subject_hint, structure_hint = templates.get(comm_type, ("Internal Communication", "Freeform."))

    prompt = textwrap.dedent(f"""
        You are an internal communications expert.
        Write a {length} {comm_type} for a {audience} audience.
        Tone: {tone}. Target length: {target_len}.

        STRUCTURE GUIDE: {structure_hint}

        DATA POINTS:
        {'\n- '.join(data_points)}

        Output JSON:
        {{
          "subject": "...",
          "body": "..."
        }}
    """)
    raw = await _llm_generate(prompt, temperature=0.6, max_tokens=4096)
    try:
        out = json.loads(raw)
    except Exception:
        out = {"subject": subject_hint, "body": raw}

    return {
        "subject": out.get("subject", subject_hint),
        "body": out.get("body", raw),
        "comm_type": comm_type,
        "audience": audience,
        "tone": tone,
        "length": length,
    }


# ---------------------------------------------------------------------------
# 10. invoice_organizer
# ---------------------------------------------------------------------------

async def invoice_organizer(
    source_dir: str = "",
    rename_format: str = "{date} {vendor} - Invoice - {description}",
    organize_by: str = "vendor",
    output_csv: str = "",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Fatura organize etme.

    Args:
        source_dir: Kaynak dizin
        rename_format: Yeniden adlandirma sablonu
        organize_by: vendor | date | category | tax_status
        output_csv: CSV cikis yolu
        dry_run: True ise plan doner

    Returns:
        {"operations", "csv_path", "summary", "total_amount_estimated"}
    """
    src = Path(source_dir).expanduser()
    if not src.exists():
        return {"operations": [], "csv_path": "", "summary": "Directory not found.", "total_amount_estimated": 0.0}

    files = [f for f in src.iterdir() if f.is_file() and f.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".gif", ".bmp", ".webp"}]

    operations: list[dict[str, Any]] = []
    csv_rows: list[dict[str, str]] = []
    total_est = 0.0

    for f in files:
        # LLM ile fatura bilgisi cikarma (stub: dosya adindan tahmin)
        fname = f.stem
        # Tarih tahmini
        date_match = re.search(r"(20\d{2})[-_]?(\d{2})[-_]?(\d{2})", fname)
        date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}" if date_match else datetime.now().strftime("%Y-%m-%d")

        # Vendor tahmini
        vendor = fname.split()[0] if " " in fname else "Unknown"
        description = " ".join(fname.split()[1:]) if " " in fname else "Invoice"

        new_name = rename_format.format(date=date_str, vendor=vendor, description=description)
        safe_name = re.sub(r'[\\/:*?"<>|]', "-", new_name) + f.suffix

        if organize_by == "vendor":
            dst_folder = src / _slugify(vendor)
        elif organize_by == "date":
            dst_folder = src / date_str[:4] / date_str[5:7]
        elif organize_by == "category":
            dst_folder = src / "Invoices"
        else:
            dst_folder = src / "Organized"

        rel_dst = dst_folder.relative_to(src) / safe_name if str(dst_folder).startswith(str(src)) else Path("Organized") / safe_name
        operations.append({"src": f.name, "dst": str(rel_dst), "date": date_str, "vendor": vendor, "description": description})
        csv_rows.append({"original": f.name, "new_name": safe_name, "date": date_str, "vendor": vendor, "description": description, "amount": "TBD"})

    # CSV yaz
    if output_csv:
        csv_path = Path(output_csv)
    else:
        csv_path = src / "invoices_summary.csv"
    try:
        import csv as csv_mod
        with csv_path.open("w", newline="", encoding="utf-8") as cf:
            if csv_rows:
                writer = csv_mod.DictWriter(cf, fieldnames=csv_rows[0].keys())
                writer.writeheader()
                writer.writerows(csv_rows)
    except Exception as e:
        csv_path = Path(str(e))

    if not dry_run:
        for op in operations:
            try:
                dst_abs = src / op["dst"]
                dst_abs.parent.mkdir(parents=True, exist_ok=True)
                (src / op["src"]).rename(dst_abs)
            except Exception:
                continue

    summary = f"Organized {len(files)} invoices by {organize_by}. CSV: {csv_path}"
    return {
        "operations": operations,
        "csv_path": str(csv_path),
        "summary": summary,
        "total_amount_estimated": total_est,
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# 11. lead_research_assistant
# ---------------------------------------------------------------------------

async def lead_research_assistant(
    company_name: str = "",
    domain: str = "",
    linkedin_url: str = "",
    depth: str = "basic",
) -> dict[str, Any]:
    """Lead / sirket arastirmasi.

    Args:
        company_name: Hedef sirket adi
        domain: Web sitesi domaini (ornegin example.com)
        linkedin_url: LinkedIn sayfasi
        depth: basic | standard | deep

    Returns:
        {"company_name", "summary", "key_contacts", "tech_stack", "news", "sources"}
    """
    queries = [company_name]
    if domain:
        queries.append(domain)
    if linkedin_url:
        queries.append(linkedin_url)

    all_snippets: list[str] = []
    sources: list[str] = []

    for q in queries:
        results = await _web_search(q, count=5)
        for r in results:
            snippet = r.get("snippet", "")
            if snippet:
                all_snippets.append(f"- {r.get('title', '')}: {snippet}")
            link = r.get("link", "")
            if link and link not in sources:
                sources.append(link)

    # Web sitesi ziyareti (varsa)
    site_content = ""
    if domain and depth in ("standard", "deep"):
        try:
            site_content = await _browser_visit(f"https://{domain}")
            site_content = site_content[:3000]
        except Exception:
            site_content = ""

    prompt = textwrap.dedent(f"""
        You are a B2B sales researcher. Analyze the following data about {company_name}
        and produce a structured lead research report.

        DEPTH: {depth}

        WEB SNIPPETS:
        {'\n'.join(all_snippets[:30])}

        WEBSITE CONTENT:
        {site_content}

        Return JSON:
        {{
          "summary": "2-3 sentence company overview",
          "industry": "...",
          "key_contacts": [{{"name", "title", "source"}}],
          "tech_stack": ["..."],
          "recent_news": ["..."],
          "opportunities": ["..."],
          "risks": ["..."]
        }}
    """)
    raw = await _llm_generate(prompt, temperature=0.5, max_tokens=4096)
    try:
        data = json.loads(raw)
    except Exception:
        data = {"summary": raw, "industry": "", "key_contacts": [], "tech_stack": [], "recent_news": [], "opportunities": [], "risks": []}

    data["company_name"] = company_name
    data["sources"] = sources[:10]
    return data


# ---------------------------------------------------------------------------
# 12. meeting_insights_analyzer
# ---------------------------------------------------------------------------

async def meeting_insights_analyzer(
    transcript_text: str = "",
    transcript_path: str = "",
    focus_areas: list[str] | None = None,
    speakers: list[str] | None = None,
) -> dict[str, Any]:
    """Toplanti transcript analizi.

    Args:
        transcript_text: Direkt transcript metni
        transcript_path: Transcript dosya yolu (.txt, .md, .vtt, .srt)
        focus_areas: conflict_avoidance | filler_words | speaking_ratio | listening | decision_making
        speakers: Konusmaci isimleri (biliniyorsa)

    Returns:
        {"insights", "speaking_ratio", "action_items", "sentiment", "summary"}
    """
    focus_areas = focus_areas or ["speaking_ratio", "action_items"]
    text = transcript_text
    if not text and transcript_path:
        p = Path(transcript_path)
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="ignore")

    if not text:
        return {"insights": [], "speaking_ratio": {}, "action_items": [], "sentiment": "neutral", "summary": "No transcript provided."}

    # VTT / SRT temizligi
    text = re.sub(r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}", "", text)
    text = re.sub(r"<[^>]+>", "", text)

    prompt = textwrap.dedent(f"""
        You are an executive communication coach. Analyze this meeting transcript.

        SPEAKERS: {', '.join(speakers) if speakers else 'Unknown'}
        FOCUS AREAS: {', '.join(focus_areas)}

        TRANSCRIPT:
        {text[:12000]}

        Return JSON:
        {{
          "summary": "Brief meeting summary",
          "speaking_ratio": {{"speaker_name": "percentage"}},
          "insights": [{{"type", "description", "example_quote", "severity"}}],
          "action_items": [{{"task", "owner", "deadline"}}],
          "sentiment": "positive|neutral|negative",
          "recommendations": ["..."]
        }}
    """)
    raw = await _llm_generate(prompt, temperature=0.4, max_tokens=4096)
    try:
        data = json.loads(raw)
    except Exception:
        data = {"summary": raw[:500], "speaking_ratio": {}, "insights": [], "action_items": [], "sentiment": "neutral", "recommendations": []}

    return data


# ---------------------------------------------------------------------------
# 13. tailored_resume_generator
# ---------------------------------------------------------------------------

async def tailored_resume_generator(
    job_description: str = "",
    candidate_background: str = "",
    existing_resume_path: str = "",
    output_format: str = "markdown",
    language: str = "en",
) -> dict[str, Any]:
    """Ozellestirilmis CV / ozgecmis uretir.

    Args:
        job_description: Is ilani metni
        candidate_background: Adayin kisa ozgecmisi
        existing_resume_path: Mevcut CV dosya yolu
        output_format: markdown | json | html
        language: tr | en

    Returns:
        {"tailored_resume", "matched_keywords", "gaps", "ats_score", "suggestions"}
    """
    existing_resume = ""
    if existing_resume_path:
        p = Path(existing_resume_path)
        if p.exists():
            existing_resume = p.read_text(encoding="utf-8", errors="ignore")

    lang_note = "Turkish" if language == "tr" else "English"

    prompt = textwrap.dedent(f"""
        You are an expert career coach and ATS optimizer.
        Create a tailored resume for the following job.
        Language: {lang_note}

        JOB DESCRIPTION:
        {job_description[:4000]}

        CANDIDATE BACKGROUND:
        {candidate_background[:4000]}

        EXISTING RESUME:
        {existing_resume[:4000] if existing_resume else 'N/A'}

        Return JSON:
        {{
          "tailored_resume": "Full resume text in {output_format} format",
          "matched_keywords": ["keyword1", "keyword2"],
          "missing_keywords": ["gap1"],
          "ats_score": 85,
          "suggestions": ["..."]
        }}
    """)
    raw = await _llm_generate(prompt, temperature=0.6, max_tokens=8192)
    try:
        data = json.loads(raw)
    except Exception:
        data = {
            "tailored_resume": raw,
            "matched_keywords": [],
            "missing_keywords": [],
            "ats_score": 0,
            "suggestions": ["Parse error: review raw output."],
        }

    return data


# ---------------------------------------------------------------------------
# 14. theme_factory
# ---------------------------------------------------------------------------

async def theme_factory(
    artifact_type: str = "slides",
    theme_name: str = "",
    custom_description: str = "",
    apply_to_content: str = "",
) -> dict[str, Any]:
    """Tema / UI rengi ve tipografi olusturur.

    Args:
        artifact_type: slides | html | doc | report
        theme_name: Hazir tema adi veya bos
        custom_description: Ozel tema aciklamasi
        apply_to_content: Uygulanacak icerik (markdown / html)

    Returns:
        {"theme", "styled_content", "css", "palette"}
    """
    presets = {
        "ocean_depths": {"colors": ["#0A2540", "#00A4B4", "#F6F9FC"], "fonts": ["Montserrat", "Open Sans"]},
        "sunset_boulevard": {"colors": ["#FF6B6B", "#FFD93D", "#6BCB77", "#4D96FF"], "fonts": ["Poppins", "Lora"]},
        "forest_canopy": {"colors": ["#2D5016", "#8FBC8F", "#F5F5DC"], "fonts": ["Merriweather", "Roboto"]},
        "modern_minimalist": {"colors": ["#1A1A1A", "#FFFFFF", "#E5E5E5", "#FF4500"], "fonts": ["Inter", "Inter"]},
        "golden_hour": {"colors": ["#D4A017", "#8B4513", "#FFF8DC"], "fonts": ["Playfair Display", "Source Sans Pro"]},
        "arctic_frost": {"colors": ["#1E3A5F", "#A8D0E6", "#F0F8FF"], "fonts": ["Raleway", "Nunito"]},
        "desert_rose": {"colors": ["#C9A9A6", "#8B5A5A", "#F5F5F5"], "fonts": ["Cormorant Garamond", "Lato"]},
        "tech_innovation": {"colors": ["#0D1117", "#58A6FF", "#238636", "#F78166"], "fonts": ["JetBrains Mono", "SF Pro"]},
        "botanical_garden": {"colors": ["#2E7D32", "#A5D6A7", "#FFFDE7"], "fonts": ["Crimson Text", "Work Sans"]},
        "midnight_galaxy": {"colors": ["#0B0C15", "#7B61FF", "#FF6B9D", "#00D9FF"], "fonts": ["Space Grotesk", "Manrope"]},
    }

    selected = {}
    if theme_name and theme_name.lower().replace(" ", "_") in presets:
        selected = presets[theme_name.lower().replace(" ", "_")]
    elif custom_description:
        # LLM ile ozel tema
        theme_prompt = textwrap.dedent(f"""
            Create a professional theme based on: "{custom_description}".
            Return JSON: {{"name", "colors": [hex1, hex2, hex3, ...], "fonts": [heading, body]}}
        """)
        raw = await _llm_generate(theme_prompt, temperature=0.7, max_tokens=512)
        try:
            selected = json.loads(raw)
        except Exception:
            selected = {"name": "Custom", "colors": ["#333333", "#F5F5F5", "#FF5722"], "fonts": ["Inter", "Inter"]}
    else:
        selected = presets.get("modern_minimalist", {})

    palette = selected.get("colors", ["#333", "#FFF"])
    fonts = selected.get("fonts", ["Inter", "Inter"])

    # CSS uret
    css = textwrap.dedent(f"""
        /* Theme: {selected.get('name', theme_name or 'Custom')} */
        :root {{
            --color-primary: {palette[0]};
            --color-secondary: {palette[1] if len(palette) > 1 else palette[0]};
            --color-accent: {palette[2] if len(palette) > 2 else '#FF5722'};
            --font-heading: '{fonts[0]}', sans-serif;
            --font-body: '{fonts[1]}', sans-serif;
        }}
        body {{ font-family: var(--font-body); color: var(--color-primary); background: {palette[-1] if len(palette) > 3 else '#FFFFFF'}; }}
        h1, h2, h3 {{ font-family: var(--font-heading); color: var(--color-primary); }}
        a {{ color: var(--color-accent); }}
    """)

    styled = apply_to_content
    if apply_to_content:
        style_prompt = textwrap.dedent(f"""
            Apply this theme to the following content.
            Colors: {palette}
            Fonts: {fonts}
            Output format: {artifact_type}

            CONTENT:
            {apply_to_content[:6000]}

            Return the styled version.
        """)
        styled = await _llm_generate(style_prompt, temperature=0.5, max_tokens=8192)

    return {
        "theme": selected,
        "styled_content": styled,
        "css": css,
        "palette": palette,
        "fonts": fonts,
    }


# ---------------------------------------------------------------------------
# 15. twitter_algorithm_optimizer
# ---------------------------------------------------------------------------

async def twitter_algorithm_optimizer(
    draft_text: str = "",
    goal: str = "engagement",
    audience: str = "general",
    thread_mode: bool = False,
) -> dict[str, Any]:
    """Sosyal medya (X/Twitter) icerigi optimize eder.

    Args:
        draft_text: Taslak icerik
        goal: engagement | reach | conversions | community
        audience: Hedef kitle
        thread_mode: True ise tweet thread olarak optimize eder

    Returns:
        {"optimized_text", "hashtags", "best_posting_time", "engagement_prediction", "variations"}
    """
    prompt = textwrap.dedent(f"""
        You are a social media growth expert specializing in the X/Twitter algorithm.
        Optimize this content for maximum {goal}.

        DRAFT:
        {draft_text}

        AUDIENCE: {audience}
        MODE: {'Thread' if thread_mode else 'Single Tweet'}

        Return JSON:
        {{
          "optimized_text": "...",
          "hashtags": ["#tag1", "#tag2"],
          "best_posting_time": "Weekday 9-11am EST",
          "engagement_prediction": "high|medium|low + reason",
          "variations": ["alt version 1", "alt version 2"],
          "tips": ["..."]
        }}
    """)
    raw = await _llm_generate(prompt, temperature=0.7, max_tokens=4096)
    try:
        data = json.loads(raw)
    except Exception:
        data = {
            "optimized_text": raw,
            "hashtags": [],
            "best_posting_time": "",
            "engagement_prediction": "unknown",
            "variations": [],
            "tips": [],
        }

    return data


# ---------------------------------------------------------------------------
# 16. video_downloader
# ---------------------------------------------------------------------------

async def video_downloader(
    url: str = "",
    quality: str = "best",
    format: str = "mp4",
    audio_only: bool = False,
    output_dir: str = "/mnt/agents/output/project/data/downloads",
) -> dict[str, Any]:
    """Video indirme ve cozumleme.

    Args:
        url: Video URL'si (YouTube, Vimeo, vb.)
        quality: best | 1080p | 720p | 480p | 360p | worst
        format: mp4 | webm | mkv
        audio_only: True ise sadece ses (mp3)
        output_dir: Cikis dizini

    Returns:
        {"file_path", "metadata", "success", "error"}
    """
    out = Path(output_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    metadata: dict[str, Any] = {"url": url, "requested_quality": quality, "format": format}

    # 1. yt-dlp deneyelim
    try:
        import yt_dlp  # type: ignore[import]
        ydl_opts: dict[str, Any] = {
            "outtmpl": str(out / "%(title)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
        }
        if audio_only:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]
        else:
            if quality == "best":
                ydl_opts["format"] = f"bestvideo[ext={format}]+bestaudio/best[ext={format}]/best"
            elif quality == "worst":
                ydl_opts["format"] = f"worstvideo[ext={format}]+worstaudio/best[ext={format}]/worst"
            else:
                height = quality.replace("p", "")
                ydl_opts["format"] = f"bestvideo[height<={height}][ext={format}]+bestaudio/best[height<={height}]/best"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded = ydl.prepare_filename(info)
            metadata.update({
                "title": info.get("title", ""),
                "duration": info.get("duration", 0),
                "uploader": info.get("uploader", ""),
                "view_count": info.get("view_count", 0),
            })
            return {"file_path": downloaded, "metadata": metadata, "success": True, "error": ""}
    except Exception as e:
        metadata["yt_dlp_error"] = str(e)

    # 2. youtube-dl fallback
    try:
        from youtube_dl import YoutubeDL  # type: ignore[import]
        ydl_opts2: dict[str, Any] = {"outtmpl": str(out / "%(title)s.%(ext)s"), "quiet": True}
        if audio_only:
            ydl_opts2["format"] = "bestaudio"
            ydl_opts2["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]
        else:
            ydl_opts2["format"] = "best"
        with YoutubeDL(ydl_opts2) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded = ydl.prepare_filename(info)
            return {"file_path": downloaded, "metadata": metadata, "success": True, "error": ""}
    except Exception as e:
        metadata["youtube_dl_error"] = str(e)

    # 3. pytube fallback
    try:
        from pytube import YouTube  # type: ignore[import]
        yt = YouTube(url)
        if audio_only:
            stream = yt.streams.filter(only_audio=True).first()
        else:
            stream = yt.streams.filter(file_extension=format, progressive=True).first()
            if not stream:
                stream = yt.streams.get_highest_resolution()
        if stream:
            fname = stream.download(output_path=str(out))
            metadata.update({
                "title": yt.title,
                "duration": yt.length,
                "uploader": yt.author,
            })
            return {"file_path": fname, "metadata": metadata, "success": True, "error": ""}
    except Exception as e:
        metadata["pytube_error"] = str(e)

    # 4. Manual / stub fallback
    stub_path = out / f"video_stub_{_slugify(url)}.txt"
    stub_path.write_text(f"URL: {url}\nRequested: {quality} {format} audio_only={audio_only}\n", encoding="utf-8")
    return {
        "file_path": str(stub_path),
        "metadata": metadata,
        "success": False,
        "error": "All downloader backends failed. Install yt-dlp, youtube-dl, or pytube.",
    }


# ---------------------------------------------------------------------------
# 17. skill_catalog (bonus meta-skill)
# ---------------------------------------------------------------------------

async def skill_catalog() -> dict[str, str]:
    """Mevcut claude skill implementasyonlarinin listesini doner."""
    return {
        "artifacts_builder": "AI artifact olusturma (JSON, HTML, SVG)",
        "brand_guidelines": "Marka rehberi olusturma",
        "canvas_design": "Canvas / sema tasarimi",
        "changelog_generator": "Changelog uretimi",
        "content_research_writer": "Icerik arastirma + yazma",
        "document_skills": "Dokuman isleme",
        "file_organizer": "Dosya organize etme",
        "image_enhancer": "Gorsel prompt gelistirme",
        "internal_comms": "Iletisim sablonlari",
        "invoice_organizer": "Fatura organize etme",
        "lead_research_assistant": "Lead arastirma",
        "meeting_insights_analyzer": "Toplanti analizi",
        "tailored_resume_generator": "Ozellestirilmis CV",
        "theme_factory": "Tema / UI olusturma",
        "twitter_algorithm_optimizer": "Sosyal medya optimize",
        "video_downloader": "Video indirme / cozumleme",
    }
