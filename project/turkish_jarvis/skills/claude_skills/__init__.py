"""turkish_jarvis.skills.claude_skills paketi.

ComposioHQ/awesome-claude-skills reposundaki skill'leri parse edip
TurkishJARVIS skill formatina donusturur ve native implementasyonlar
sunar.
"""

from __future__ import annotations

from turkish_jarvis.skills.claude_skills.claude_skill_parser import (
    discover_skills,
    fetch_skill_from_github,
    parse_claude_skill_dir,
)
from turkish_jarvis.skills.claude_skills.implementations import (
    artifacts_builder,
    brand_guidelines,
    canvas_design,
    changelog_generator,
    content_research_writer,
    document_skills,
    file_organizer,
    image_enhancer,
    internal_comms,
    invoice_organizer,
    lead_research_assistant,
    meeting_insights_analyzer,
    tailored_resume_generator,
    theme_factory,
    twitter_algorithm_optimizer,
    video_downloader,
    skill_catalog,
)
from turkish_jarvis.skills.claude_skills.skill_adapter import (
    ClaudeSkillAdapter,
    adapt_claude_skill,
)

__all__ = [
    # Parser
    "discover_skills",
    "fetch_skill_from_github",
    "parse_claude_skill_dir",
    # Adapter
    "adapt_claude_skill",
    "ClaudeSkillAdapter",
    # Implementations
    "artifacts_builder",
    "brand_guidelines",
    "canvas_design",
    "changelog_generator",
    "content_research_writer",
    "document_skills",
    "file_organizer",
    "image_enhancer",
    "internal_comms",
    "invoice_organizer",
    "lead_research_assistant",
    "meeting_insights_analyzer",
    "tailored_resume_generator",
    "theme_factory",
    "twitter_algorithm_optimizer",
    "video_downloader",
    "skill_catalog",
]
