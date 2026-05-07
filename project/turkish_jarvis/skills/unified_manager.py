"""Unified Skill Manager — Tüm repolardan skill parse, load, ve yönetim."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import aiohttp
import yaml

from turkish_jarvis.tools.registry import ToolRegistry

logger = logging.getLogger("jarvis.skills.unified")

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class SkillDefinition:
    """Bir skill'in tam tanımı — metadata + içerik + runtime bilgisi."""

    name: str
    description: str
    source_repo: str
    source_path: str
    raw_url: str
    content: str
    frontmatter: dict[str, Any] = field(default_factory=dict)
    body: str = ""
    category: str = "general"
    version: str = "1.0.0"
    loaded_at: str | None = None
    installed: bool = False

    @property
    def unique_id(self) -> str:
        """Skill için benzersiz ID (repo + path hash)."""
        key = f"{self.source_repo}:{self.source_path}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    @property
    def schema(self) -> dict[str, Any]:
        """OpenAI function-calling uyumlu schema."""
        return {
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": f"Task description for {self.name} skill",
                    },
                },
                "required": ["task"],
            },
        }


@dataclass
class DiscoveryReport:
    """Tüm repolardan skill keşfi sonuçları."""

    repos_scanned: int = 0
    total_skills_found: int = 0
    new_skills: int = 0
    already_loaded: int = 0
    errors: list[str] = field(default_factory=list)
    skills_by_repo: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "repos_scanned": self.repos_scanned,
            "total_skills_found": self.total_skills_found,
            "new_skills": self.new_skills,
            "already_loaded": self.already_loaded,
            "errors": self.errors,
            "skills_by_repo": self.skills_by_repo,
        }


@dataclass
class RefreshReport:
    """Bir repo refresh sonuçları."""

    repo: str = ""
    skills_added: int = 0
    skills_removed: int = 0
    skills_updated: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo": self.repo,
            "skills_added": self.skills_added,
            "skills_removed": self.skills_removed,
            "skills_updated": self.skills_updated,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# SKILL.md Parser
# ---------------------------------------------------------------------------


def parse_skill_md(content: str, repo_name: str, path: str, raw_url: str) -> SkillDefinition | None:
    """SKILL.md içeriğini parse et, SkillDefinition üret.

    SKILL.md formatı:
    ---
    name: skill-name
    description: A clear description...
    ---
    # Markdown body...
    """
    # YAML frontmatter extraction
    frontmatter: dict[str, Any] = {}
    body = content

    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if fm_match:
        try:
            frontmatter = yaml.safe_load(fm_match.group(1)) or {}
            body = content[fm_match.end() :]
        except yaml.YAMLError as exc:
            logger.warning("YAML parse error in %s/%s: %s", repo_name, path, exc)
            # Continue with empty frontmatter

    name = frontmatter.get("name", "").strip()
    if not name:
        # Path'ten name türet: agent-coder/SKILL.md -> agent-coder
        name = Path(path).parent.name
        if name in ("", "."):
            name = Path(path).stem

    description = frontmatter.get("description", "").strip()
    if not description:
        # İlk heading veya ilk paragrafı al
        heading_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if heading_match:
            description = heading_match.group(1).strip()
        else:
            # İlk 200 karakter
            description = body[:200].strip().replace("\n", " ")

    version = str(frontmatter.get("version", "1.0.0"))
    category = str(frontmatter.get("category", "general"))
    if category == "general" and "/" in path:
        category = path.split("/")[0]

    return SkillDefinition(
        name=name,
        description=description,
        source_repo=repo_name,
        source_path=path,
        raw_url=raw_url,
        content=content,
        frontmatter=frontmatter,
        body=body.strip(),
        category=category,
        version=version,
    )


# ---------------------------------------------------------------------------
# GitHub API Helpers
# ---------------------------------------------------------------------------


class GitHubAPI:
    """GitHub API async client — ücretsiz, rate-limited."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token
        self.session: aiohttp.ClientSession | None = None

    async def _get(self, url: str) -> Any:
        """GET request with optional auth."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TurkishJARVIS-UnifiedSkillManager/1.0",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        if self.session is None:
            self.session = aiohttp.ClientSession()

        async with self.session.get(url, headers=headers) as resp:
            if resp.status == 403:
                text = await resp.text()
                if "rate limit" in text.lower():
                    logger.warning("GitHub API rate limit exceeded: %s", text)
                raise aiohttp.ClientResponseError(
                    request_info=resp.request_info,
                    history=resp.history,
                    status=resp.status,
                    message=f"Rate limited: {text}",
                )
            if resp.status != 200:
                text = await resp.text()
                raise aiohttp.ClientResponseError(
                    request_info=resp.request_info,
                    history=resp.history,
                    status=resp.status,
                    message=text,
                )
            return await resp.json()

    async def get_tree(self, owner: str, repo: str, branch: str = "main") -> list[dict[str, Any]]:
        """Repo'nun recursive git tree'sini al."""
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        try:
            data = await self._get(url)
            return data.get("tree", [])
        except Exception as exc:
            # Retry with 'master' branch
            if branch == "main":
                url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1"
                data = await self._get(url)
                return data.get("tree", [])
            raise exc

    async def get_file(self, raw_url: str) -> str:
        """Raw file içeriğini al."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        async with self.session.get(raw_url) as resp:
            if resp.status != 200:
                raise aiohttp.ClientResponseError(
                    request_info=resp.request_info,
                    history=resp.history,
                    status=resp.status,
                    message=f"Failed to fetch {raw_url}",
                )
            return await resp.text()

    async def get_readme(self, owner: str, repo: str, branch: str = "main") -> str:
        """README.md içeriğini al."""
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
        try:
            return await self.get_file(raw_url)
        except Exception:
            # Retry with master
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
            return await self.get_file(raw_url)

    async def close(self) -> None:
        if self.session:
            await self.session.close()
            self.session = None


# ---------------------------------------------------------------------------
# README Parser (for index repos)
# ---------------------------------------------------------------------------


def extract_skills_from_readme(readme: str) -> list[dict[str, str]]:
    """README'den skill link'lerini çıkar.

    Format: **owner/repo** - Description...
    Veya: - **owner/repo** - Description
    """
    skills: list[dict[str, str]] = []

    # Pattern: **owner/repo** - description
    pattern1 = re.compile(
        r"\*\*([^\s/]+/[^\s*]+)\*\*\s*[-–—]\s*(.+?)(?=\n|$)",
        re.MULTILINE,
    )
    for match in pattern1.finditer(readme):
        repo = match.group(1).strip()
        desc = match.group(2).strip()
        # Clean markdown links in description
        desc = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", desc)
        skills.append({"repo": repo, "description": desc})

    # Pattern: - owner/repo - description (in skills sections)
    pattern2 = re.compile(
        r"^\s*[-*]\s+([^\s/]+/[^\s/]+)\s*[-–—]\s*(.+?)(?=\n|$)",
        re.MULTILINE,
    )
    for match in pattern2.finditer(readme):
        repo = match.group(1).strip()
        # Strip surrounding ** that may have been captured
        repo = re.sub(r"^\*+|\*+$", "", repo).strip()
        desc = match.group(2).strip()
        # Skip if already matched
        if any(s["repo"] == repo for s in skills):
            continue
        desc = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", desc)
        skills.append({"repo": repo, "description": desc})

    return skills


# ---------------------------------------------------------------------------
# Unified Skill Manager
# ---------------------------------------------------------------------------


class UnifiedSkillManager:
    """Bütün skill repolarını tek bir noktadan yönetir."""

    REPOS: dict[str, str] = {
        "heilcheng_awesome": "https://github.com/heilcheng/awesome-agent-skills",
        "volt_agent": "https://github.com/VoltAgent/awesome-agent-skills",
        "ruflo": "https://github.com/ruvnet/ruflo",
        "composio_claude": "https://github.com/ComposioHQ/awesome-claude-skills",
    }

    # Repo metadata: owner, repo, branch, type
    REPO_META: dict[str, dict[str, str]] = {
        "heilcheng_awesome": {
            "owner": "heilcheng",
            "repo": "awesome-agent-skills",
            "branch": "main",
            "type": "index",  # README-based index
        },
        "volt_agent": {
            "owner": "VoltAgent",
            "repo": "awesome-agent-skills",
            "branch": "main",
            "type": "index",
        },
        "ruflo": {
            "owner": "ruvnet",
            "repo": "ruflo",
            "branch": "main",
            "type": "skills",  # Direct SKILL.md files
            "skill_paths": [".agents/skills", ".claude/skills"],
        },
        "composio_claude": {
            "owner": "ComposioHQ",
            "repo": "awesome-claude-skills",
            "branch": "master",
            "type": "skills",
            "skill_paths": ["composio-skills"],
        },
    }

    def __init__(self, skill_registry: ToolRegistry, project_dir: str = ".") -> None:
        self.registry = skill_registry
        self.project_dir = Path(project_dir)
        self.skill_store = self.project_dir / "data" / "skill_store"
        self.skill_store.mkdir(parents=True, exist_ok=True)

        # In-memory skill cache: {skill_id: SkillDefinition}
        self._skills: dict[str, SkillDefinition] = {}
        # Track which skills came from which repo
        self._repo_skills: dict[str, set[str]] = {k: set() for k in self.REPOS}

        # GitHub API client
        self._github = GitHubAPI()

        # Load local cache
        self._load_local_cache()

    # ------------------------------------------------------------------
    # Local Cache
    # ------------------------------------------------------------------

    def _cache_path(self, repo_name: str) -> Path:
        return self.skill_store / f"{repo_name}_cache.json"

    def _load_local_cache(self) -> None:
        """Disk'ten önceden yüklenmiş skill'leri geri yükle."""
        for repo_name in self.REPOS:
            cache_file = self._cache_path(repo_name)
            if not cache_file.exists():
                continue
            try:
                with cache_file.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                for item in data:
                    skill = SkillDefinition(
                        name=item["name"],
                        description=item.get("description", ""),
                        source_repo=item["source_repo"],
                        source_path=item["source_path"],
                        raw_url=item["raw_url"],
                        content=item["content"],
                        frontmatter=item.get("frontmatter", {}),
                        body=item.get("body", ""),
                        category=item.get("category", "general"),
                        version=item.get("version", "1.0.0"),
                        loaded_at=item.get("loaded_at"),
                        installed=item.get("installed", False),
                    )
                    self._skills[skill.unique_id] = skill
                    self._repo_skills[repo_name].add(skill.unique_id)
            except Exception as exc:
                logger.warning("Cache load error for %s: %s", repo_name, exc)

    def _save_local_cache(self, repo_name: str) -> None:
        """Repo'nun skill'lerini disk'e yaz."""
        cache_file = self._cache_path(repo_name)
        data = []
        for sid in self._repo_skills.get(repo_name, set()):
            skill = self._skills.get(sid)
            if skill is None:
                continue
            data.append(
                {
                    "name": skill.name,
                    "description": skill.description,
                    "source_repo": skill.source_repo,
                    "source_path": skill.source_path,
                    "raw_url": skill.raw_url,
                    "content": skill.content,
                    "frontmatter": skill.frontmatter,
                    "body": skill.body,
                    "category": skill.category,
                    "version": skill.version,
                    "loaded_at": skill.loaded_at,
                    "installed": skill.installed,
                }
            )
        with cache_file.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    async def discover_all(self) -> DiscoveryReport:
        """Tüm repolardan skill keşfet.

        GitHub API ile repo dizinlerini listeler,
        SKILL.md dosyalarını bulur, özet çıkarır.
        """
        report = DiscoveryReport()
        report.repos_scanned = len(self.REPOS)

        for repo_name, meta in self.REPO_META.items():
            try:
                if meta["type"] == "index":
                    count = await self._discover_index_repo(repo_name, meta, report)
                    logger.info("%s: %d skills discovered (index)", repo_name, count)
                else:
                    count = await self._discover_skills_repo(repo_name, meta, report)
                    logger.info("%s: %d skills discovered (direct)", repo_name, count)
            except Exception as exc:
                err_msg = f"{repo_name}: {exc}"
                logger.error("Discovery error: %s", err_msg)
                report.errors.append(err_msg)

        return report

    async def _discover_index_repo(
        self, repo_name: str, meta: dict[str, str], report: DiscoveryReport
    ) -> int:
        """README tabanlı index repo'dan skill keşfet."""
        readme = await self._github.get_readme(meta["owner"], meta["repo"], meta["branch"])
        skills = extract_skills_from_readme(readme)

        found = []
        for sk in skills:
            repo_ref = sk["repo"]
            # Create a lightweight SkillDefinition for index entries
            skill = SkillDefinition(
                name=repo_ref.replace("/", "-"),
                description=sk["description"],
                source_repo=repo_name,
                source_path=f"index/{repo_ref}",
                raw_url=f"https://github.com/{repo_ref}",
                content=sk["description"],
                frontmatter={"repo": repo_ref},
                body=sk["description"],
                category="index",
            )
            sid = skill.unique_id
            if sid in self._skills:
                report.already_loaded += 1
            else:
                report.new_skills += 1
                self._skills[sid] = skill
                self._repo_skills[repo_name].add(sid)
            found.append(skill.name)

        report.total_skills_found += len(found)
        report.skills_by_repo[repo_name] = found
        return len(found)

    async def _discover_skills_repo(
        self, repo_name: str, meta: dict[str, str], report: DiscoveryReport
    ) -> int:
        """Doğrudan SKILL.md içeren repo'dan skill keşfet."""
        tree = await self._github.get_tree(meta["owner"], meta["repo"], meta["branch"])

        skill_paths = meta.get("skill_paths", [])
        skill_files: list[tuple[str, str]] = []  # (path, raw_url)

        for item in tree:
            path = item.get("path", "")
            if not path.endswith("SKILL.md"):
                continue
            # Filter by skill_paths if specified
            if skill_paths and not any(path.startswith(sp) for sp in skill_paths):
                continue
            raw_url = (
                f"https://raw.githubusercontent.com/"
                f"{meta['owner']}/{meta['repo']}/{meta['branch']}/{path}"
            )
            skill_files.append((path, raw_url))

        # Fetch and parse each SKILL.md (with concurrency limit)
        found = []
        semaphore = asyncio.Semaphore(10)

        async def _fetch_one(path: str, raw_url: str) -> SkillDefinition | None:
            async with semaphore:
                try:
                    content = await self._github.get_file(raw_url)
                    skill = parse_skill_md(content, repo_name, path, raw_url)
                    return skill
                except Exception as exc:
                    logger.warning("Fetch error %s: %s", path, exc)
                    return None

        results = await asyncio.gather(
            *[_fetch_one(p, u) for p, u in skill_files]
        )

        for skill in results:
            if skill is None:
                continue
            sid = skill.unique_id
            if sid in self._skills:
                report.already_loaded += 1
            else:
                report.new_skills += 1
                self._skills[sid] = skill
                self._repo_skills[repo_name].add(sid)
            found.append(skill.name)

        report.total_skills_found += len(found)
        report.skills_by_repo[repo_name] = found
        return len(found)

    # ------------------------------------------------------------------
    # Load / Install
    # ------------------------------------------------------------------

    async def load_repo_skills(self, repo_name: str) -> list[SkillDefinition]:
        """Belirli bir repodan skill'leri yükle.

        Repo'nun skill dizinini tarar, SKILL.md parse eder,
        Python fonksiyonuna dönüştürür, Registry'ye ekler.
        """
        if repo_name not in self.REPOS:
            raise ValueError(f"Unknown repo: {repo_name}")

        meta = self.REPO_META[repo_name]
        loaded: list[SkillDefinition] = []

        if meta["type"] == "index":
            # Index repos: skill'leri keşfet ama registry'ye ekleme
            # (external repo'lar olduğu için)
            report = DiscoveryReport()
            await self._discover_index_repo(repo_name, meta, report)
            # Return discovered (not installed) skills
            for sid in self._repo_skills.get(repo_name, set()):
                loaded.append(self._skills[sid])
        else:
            # Direct skills: fetch, parse, register
            report = DiscoveryReport()
            await self._discover_skills_repo(repo_name, meta, report)

            for sid in self._repo_skills.get(repo_name, set()):
                skill = self._skills[sid]
                if not skill.installed:
                    self._register_skill_as_tool(skill)
                    skill.installed = True
                    from datetime import datetime, timezone
                    skill.loaded_at = datetime.now(timezone.utc).isoformat()
                loaded.append(skill)

        self._save_local_cache(repo_name)
        return loaded

    def _register_skill_as_tool(self, skill: SkillDefinition) -> None:
        """Bir skill'i ToolRegistry'ye async tool olarak kaydet."""
        # Create an async wrapper function for the skill
        skill_body = skill.body
        skill_name = skill.name
        skill_desc = skill.description

        async def _skill_executor(task: str) -> dict[str, Any]:
            """Execute the skill with the given task."""
            # This wrapper returns skill metadata + instructions
            # Actual execution is LLM-driven using the skill body
            return {
                "skill": skill_name,
                "description": skill_desc,
                "instructions": skill_body,
                "task": task,
                "frontmatter": skill.frontmatter,
            }

        # Make the wrapper identifiable
        _skill_executor.__name__ = f"skill_{skill_name.replace('-', '_')}"
        _skill_executor.__doc__ = skill_desc

        schema = {
            "description": f"[{skill.source_repo}] {skill_desc}",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": f"Task to execute with {skill_name} skill",
                    },
                },
                "required": ["task"],
            },
        }

        try:
            self.registry.register(skill_name, _skill_executor, schema)
            logger.info("Registered skill as tool: %s", skill_name)
        except ValueError:
            # Already registered — update not supported, skip
            logger.debug("Skill already registered: %s", skill_name)

    async def install_skill(self, repo_name: str, skill_path: str) -> bool:
        """Belirli bir skill'i yükle.

        Args:
            repo_name: Repo key (e.g. 'composio_claude').
            skill_path: SKILL.md path within repo (e.g. 'file-organizer/SKILL.md').

        Returns:
            True if successfully installed.
        """
        if repo_name not in self.REPO_META:
            return False

        meta = self.REPO_META[repo_name]
        raw_url = (
            f"https://raw.githubusercontent.com/"
            f"{meta['owner']}/{meta['repo']}/{meta['branch']}/{skill_path}"
        )

        try:
            content = await self._github.get_file(raw_url)
            skill = parse_skill_md(content, repo_name, skill_path, raw_url)
            if skill is None:
                return False

            sid = skill.unique_id
            self._skills[sid] = skill
            self._repo_skills[repo_name].add(sid)

            if not skill.installed:
                self._register_skill_as_tool(skill)
                skill.installed = True
                from datetime import datetime, timezone
                skill.loaded_at = datetime.now(timezone.utc).isoformat()

            self._save_local_cache(repo_name)
            return True
        except Exception as exc:
            logger.error("Install skill error %s/%s: %s", repo_name, skill_path, exc)
            return False

    async def uninstall_skill(self, skill_name: str) -> bool:
        """Skill'i kaldır.

        Not: ToolRegistry'den unregister desteklenmez, sadece
        local cache'ten ve loaded flag'ten kaldırılır.
        """
        for sid, skill in list(self._skills.items()):
            if skill.name == skill_name:
                skill.installed = False
                skill.loaded_at = None
                self._repo_skills[skill.source_repo].discard(sid)
                self._save_local_cache(skill.source_repo)
                logger.info("Uninstalled skill: %s", skill_name)
                return True
        return False

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def list_available_repos(self) -> list[dict[str, str]]:
        """Hangi repolar destekleniyor?"""
        result = []
        for key, url in self.REPOS.items():
            meta = self.REPO_META[key]
            result.append(
                {
                    "key": key,
                    "url": url,
                    "type": meta["type"],
                    "branch": meta["branch"],
                    "loaded_skills": len(self._repo_skills.get(key, set())),
                }
            )
        return result

    def list_loaded_skills(self) -> list[dict[str, Any]]:
        """Yüklenen skill'leri listele (repo bazlı gruplama)."""
        result = []
        for repo_name in self.REPOS:
            skills = []
            for sid in self._repo_skills.get(repo_name, set()):
                skill = self._skills.get(sid)
                if skill is None:
                    continue
                skills.append(
                    {
                        "name": skill.name,
                        "description": skill.description,
                        "category": skill.category,
                        "version": skill.version,
                        "installed": skill.installed,
                        "source_path": skill.source_path,
                    }
                )
            result.append(
                {
                    "repo": repo_name,
                    "repo_url": self.REPOS[repo_name],
                    "skill_count": len(skills),
                    "skills": skills,
                }
            )
        return result

    def get_skill_source(self, skill_name: str) -> str:
        """Skill hangi repodan geldi?"""
        for sid, skill in self._skills.items():
            if skill.name == skill_name:
                return skill.source_repo
        return ""

    def get_skill(self, skill_name: str) -> SkillDefinition | None:
        """SkillDefinition'a doğrudan erişim."""
        for sid, skill in self._skills.items():
            if skill.name == skill_name:
                return skill
        return None

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    async def refresh_repo(self, repo_name: str) -> RefreshReport:
        """Bir repoyu yeniden tarar, yeni skill'leri yükler.

        Mevcut skill'lerin content hash'ini karşılaştırır,
        güncellenmiş skill'leri tespit eder.
        """
        report = RefreshReport(repo=repo_name)

        if repo_name not in self.REPO_META:
            report.errors.append(f"Unknown repo: {repo_name}")
            return report

        # Backup current skills for this repo
        old_sids = set(self._repo_skills.get(repo_name, set()))
        old_hashes: dict[str, str] = {}
        for sid in old_sids:
            skill = self._skills.get(sid)
            if skill:
                old_hashes[sid] = hashlib.sha256(skill.content.encode()).hexdigest()

        # Re-discover
        report_disc = DiscoveryReport()
        meta = self.REPO_META[repo_name]
        try:
            if meta["type"] == "index":
                await self._discover_index_repo(repo_name, meta, report_disc)
            else:
                await self._discover_skills_repo(repo_name, meta, report_disc)
        except Exception as exc:
            report.errors.append(str(exc))
            return report

        # Compare
        new_sids = self._repo_skills.get(repo_name, set())
        report.skills_added = len(new_sids - old_sids)
        report.skills_removed = len(old_sids - new_sids)

        for sid in new_sids & old_sids:
            skill = self._skills.get(sid)
            if skill is None:
                continue
            new_hash = hashlib.sha256(skill.content.encode()).hexdigest()
            if old_hashes.get(sid) != new_hash:
                report.skills_updated += 1
                # Re-register if installed
                if skill.installed:
                    self._register_skill_as_tool(skill)

        self._save_local_cache(repo_name)
        return report

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Resources temizle."""
        await self._github.close()

    def __del__(self) -> None:
        """Destructor — cleanup session if still open."""
        if self._github.session is not None:
            try:
                asyncio.get_running_loop().create_task(self._github.close())
            except RuntimeError:
                pass

    # ------------------------------------------------------------------
    # Advanced: Dynamic skill execution
    # ------------------------------------------------------------------

    async def execute_skill(self, skill_name: str, task: str) -> dict[str, Any]:
        """Yüklenmiş bir skill'i çalıştır.

        Registry üzerinden tool execution yapar.
        """
        try:
            return await self.registry.execute(skill_name, {"task": task})
        except KeyError:
            return {"error": f"Skill '{skill_name}' not found or not installed."}
        except Exception as exc:
            return {"error": f"Skill execution failed: {exc}"}
