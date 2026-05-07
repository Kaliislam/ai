"""Bilgi kazıma — Wikipedia, arXiv, GitHub, web arama, otomatik RAG indeksleme."""

import asyncio
import json
import logging
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from xml.etree import ElementTree as ET

import httpx

logger = logging.getLogger("jarvis.knowledge_miner")


@dataclass
class KnowledgeChunk:
    """Kazınan bilgi parçası."""

    content: str
    source: str
    url: str
    title: str
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    relevance_score: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "title": self.title,
            "fetched_at": self.fetched_at.isoformat(),
            "relevance_score": self.relevance_score,
            "metadata": self.metadata,
        }


@dataclass
class MiningResult:
    """Konu madenciliği sonucu."""

    topic: str
    chunks: list[KnowledgeChunk]
    summary: str
    total_sources: int
    total_chars: int
    mined_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UpdateReport:
    """Bilgi güncelleme raporu."""

    topics_processed: int = 0
    new_chunks: int = 0
    updated_chunks: int = 0
    removed_chunks: int = 0
    errors: list[str] = field(default_factory=list)
    completed_at: datetime = field(default_factory=datetime.utcnow)


class KnowledgeMiner:
    """Dışsal kaynaklardan otomatik bilgi toplama ve RAG'e indeksleme."""

    def __init__(
        self,
        rag_pipeline: Optional[Any] = None,
        llm_client: Optional[Any] = None,
    ):
        self.rag = rag_pipeline
        self.llm = llm_client
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        self.knowledge_base_dir = Path("./data/knowledge_base")
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)

        # arXiv Atom namespace
        self._arxiv_ns = {"atom": "http://www.w3.org/2005/Atom"}

    # ------------------------------------------------------------------
    # Wikipedia
    # ------------------------------------------------------------------
    async def search_wikipedia(
        self,
        query: str,
        lang: str = "tr",
        max_results: int = 3,
    ) -> list[KnowledgeChunk]:
        """Wikipedia'dan madde arama ve özet çıkarma."""
        chunks: list[KnowledgeChunk] = []
        base_url = f"https://{lang}.wikipedia.org/w/api.php"

        try:
            # 1) Arama
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": max_results,
                "format": "json",
                "utf8": 1,
            }
            resp = await self.client.get(base_url, params=search_params)
            resp.raise_for_status()
            data = resp.json()

            search_results = data.get("query", {}).get("search", [])
            if not search_results:
                logger.info("Wikipedia'da sonuç bulunamadı: %s", query)
                return chunks

            # 2) Her madde için içerik çek
            for item in search_results:
                page_id = item.get("pageid")
                title = item.get("title", "")
                snippet = item.get("snippet", "")

                content_params = {
                    "action": "parse",
                    "pageid": page_id,
                    "prop": "text",
                    "format": "json",
                    "utf8": 1,
                }
                content_resp = await self.client.get(base_url, params=content_params)
                content_resp.raise_for_status()
                content_data = content_resp.json()

                html_text = (
                    content_data.get("parse", {}).get("text", {}).get("*", "")
                )
                # HTML tag temizleme
                clean_text = self._strip_html(html_text)
                # snippet + clean_text birleştir
                full_text = f"{title}\n\n{self._strip_html(snippet)}\n\n{clean_text}"

                chunk = KnowledgeChunk(
                    content=full_text[:8000],
                    source="wikipedia",
                    url=f"https://{lang}.wikipedia.org/?curid={page_id}",
                    title=title,
                    metadata={
                        "lang": lang,
                        "page_id": page_id,
                        "query": query,
                    },
                )
                chunks.append(chunk)

            logger.info("Wikipedia: %d chunk bulundu (%s)", len(chunks), query)

        except Exception as exc:
            logger.error("Wikipedia arama hatası: %s", exc)

        return chunks

    # ------------------------------------------------------------------
    # arXiv
    # ------------------------------------------------------------------
    async def search_arxiv(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[KnowledgeChunk]:
        """arXiv'den akademik makale arama."""
        chunks: list[KnowledgeChunk] = []
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            root = ET.fromstring(resp.text.encode("utf-8"))

            # Atom namespace handling
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entries = root.findall("atom:entry", ns)

            for entry in entries:
                title_el = entry.find("atom:title", ns)
                summary_el = entry.find("atom:summary", ns)
                id_el = entry.find("atom:id", ns)
                published_el = entry.find("atom:published", ns)

                title = (
                    self._clean_whitespace(title_el.text)
                    if title_el is not None and title_el.text
                    else "Başlıksız"
                )
                summary = (
                    self._clean_whitespace(summary_el.text)
                    if summary_el is not None and summary_el.text
                    else ""
                )
                arxiv_id = id_el.text if id_el is not None else ""
                published = (
                    published_el.text if published_el is not None else ""
                )

                # Yazarları topla
                authors = []
                for author in entry.findall("atom:author", ns):
                    name_el = author.find("atom:name", ns)
                    if name_el is not None and name_el.text:
                        authors.append(name_el.text)

                content = (
                    f"Başlık: {title}\n"
                    f"Yazarlar: {', '.join(authors)}\n"
                    f"Yayın Tarihi: {published}\n"
                    f"Özet:\n{summary}"
                )

                chunk = KnowledgeChunk(
                    content=content[:8000],
                    source="arxiv",
                    url=arxiv_id,
                    title=title,
                    metadata={
                        "authors": authors,
                        "published": published,
                        "query": query,
                    },
                )
                chunks.append(chunk)

            logger.info("arXiv: %d chunk bulundu (%s)", len(chunks), query)

        except Exception as exc:
            logger.error("arXiv arama hatası: %s", exc)

        return chunks

    # ------------------------------------------------------------------
    # GitHub
    # ------------------------------------------------------------------
    async def search_github(
        self,
        query: str,
        max_results: int = 3,
    ) -> list[KnowledgeChunk]:
        """GitHub'dan repo arama ve README çıkarma."""
        chunks: list[KnowledgeChunk] = []
        search_url = "https://api.github.com/search/repositories"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TurkishJarvis-KnowledgeMiner/1.0",
        }
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results,
        }

        try:
            resp = await self.client.get(
                search_url, params=params, headers=headers
            )
            if resp.status_code == 403:
                logger.warning("GitHub API rate limit aşıldı.")
                return chunks
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])

            for repo in items:
                owner = repo.get("owner", {}).get("login", "")
                repo_name = repo.get("name", "")
                full_name = f"{owner}/{repo_name}"
                stars = repo.get("stargazers_count", 0)
                description = repo.get("description") or ""
                default_branch = repo.get("default_branch", "main")

                # README dene
                readme_text = await self._fetch_github_readme(
                    owner, repo_name, default_branch
                )

                content = (
                    f"Repo: {full_name}\n"
                    f"Yıldız: {stars}\n"
                    f"Açıklama: {description}\n\n"
                    f"README:\n{readme_text}"
                )

                chunk = KnowledgeChunk(
                    content=content[:8000],
                    source="github",
                    url=repo.get("html_url", ""),
                    title=full_name,
                    metadata={
                        "stars": stars,
                        "language": repo.get("language", ""),
                        "default_branch": default_branch,
                        "query": query,
                    },
                )
                chunks.append(chunk)

            logger.info("GitHub: %d chunk bulundu (%s)", len(chunks), query)

        except Exception as exc:
            logger.error("GitHub arama hatası: %s", exc)

        return chunks

    async def _fetch_github_readme(
        self, owner: str, repo: str, branch: str = "main"
    ) -> str:
        """GitHub reposundan raw README al."""
        variants = ["README.md", "readme.md", "Readme.md", "README.rst"]
        for readme_name in variants:
            for br in [branch, "main", "master"]:
                raw_url = (
                    f"https://raw.githubusercontent.com/{owner}/{repo}/{br}/{readme_name}"
                )
                try:
                    r = await self.client.get(raw_url)
                    if r.status_code == 200:
                        return r.text[:6000]
                except Exception:
                    continue
        return ""

    # ------------------------------------------------------------------
    # DuckDuckGo Web Arama
    # ------------------------------------------------------------------
    async def web_search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[KnowledgeChunk]:
        """DuckDuckGo'dan web arama."""
        chunks: list[KnowledgeChunk] = []

        try:
            # Önce duckduckgo-search kütüphanesini dene
            chunks = await self._web_search_ddgs(query, max_results)
        except Exception:
            # Fallback: HTML scraping
            chunks = await self._web_search_scrape(query, max_results)

        return chunks

    async def _web_search_ddgs(
        self, query: str, max_results: int
    ) -> list[KnowledgeChunk]:
        """duckduckgo-search kütüphanesi ile arama."""
        import importlib.util

        if importlib.util.find_spec("duckduckgo_search") is None:
            raise ImportError("duckduckgo_search not installed")

        from duckduckgo_search import DDGS  # type: ignore

        chunks: list[KnowledgeChunk] = []
        loop = asyncio.get_event_loop()

        def _search():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))

        results = await loop.run_in_executor(None, _search)

        for res in results:
            chunk = KnowledgeChunk(
                content=f"{res.get('title', '')}\n\n{res.get('body', '')}",
                source="web",
                url=res.get("href", ""),
                title=res.get("title", "Web Sonucu"),
                metadata={"query": query},
            )
            chunks.append(chunk)

        logger.info("DuckDuckGo (DDGS): %d chunk bulundu (%s)", len(chunks), query)
        return chunks

    async def _web_search_scrape(
        self, query: str, max_results: int
    ) -> list[KnowledgeChunk]:
        """DuckDuckGo HTML scraping fallback."""
        chunks: list[KnowledgeChunk] = []
        url = "https://html.duckduckgo.com/html/"
        params = {"q": query, "kl": "tr-tr"}

        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            text = resp.text

            # Basit regex parsing
            results = re.findall(
                r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                text,
                re.DOTALL,
            )

            for i, (href, title_html) in enumerate(results[:max_results]):
                title = self._strip_html(title_html)
                # Snippet çıkar
                snippet_match = re.search(
                    rf'<a[^>]*href="{re.escape(href)}".*?</a>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                    text,
                    re.DOTALL,
                )
                snippet = ""
                if snippet_match:
                    snippet = self._strip_html(snippet_match.group(1))

                chunk = KnowledgeChunk(
                    content=f"{title}\n\n{snippet}",
                    source="web",
                    url=href,
                    title=title,
                    metadata={"query": query, "scrape": True},
                )
                chunks.append(chunk)

            logger.info(
                "DuckDuckGo (scrape): %d chunk bulundu (%s)", len(chunks), query
            )

        except Exception as exc:
            logger.error("DuckDuckGo scrape hatası: %s", exc)

        return chunks

    # ------------------------------------------------------------------
    # Derin Madencilik
    # ------------------------------------------------------------------
    async def mine_topic(
        self,
        topic: str,
        depth: int = 3,
    ) -> MiningResult:
        """Bir konu hakkında derinlemesine araştırma yap."""
        all_chunks: list[KnowledgeChunk] = []

        # Paralel arama
        tasks = [
            self.search_wikipedia(topic, lang="tr", max_results=depth),
            self.search_wikipedia(topic, lang="en", max_results=depth),
            self.search_arxiv(topic, max_results=depth),
            self.search_github(topic, max_results=max(1, depth - 1)),
            self.web_search(topic, max_results=depth + 2),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, Exception):
                logger.error("mine_topic alt-görev hatası: %s", res)
                continue
            all_chunks.extend(res)

        # LLM ile özet (opsiyonel)
        summary = ""
        if self.llm and all_chunks:
            summary = await self._generate_summary(topic, all_chunks)

        # Dosyaya kaydet
        await self._save_mining_result(topic, all_chunks, summary)

        total_chars = sum(len(c.content) for c in all_chunks)

        return MiningResult(
            topic=topic,
            chunks=all_chunks,
            summary=summary,
            total_sources=len({c.source for c in all_chunks}),
            total_chars=total_chars,
        )

    async def _generate_summary(
        self, topic: str, chunks: list[KnowledgeChunk]
    ) -> str:
        """LLM ile araştırma özeti üret."""
        if not self.llm:
            return ""

        # İlk 3 chunk'u özetle
        context = "\n\n---\n\n".join(
            f"[{c.source}] {c.title}\n{c.content[:1500]}"
            for c in chunks[:3]
        )

        prompt = (
            f"Aşağıdaki kaynaklara dayanarak '{topic}' konusu hakkında kısa, "
            f"bilgilendirici bir özet (Türkçe) yaz:\n\n{context}\n\nÖzet:"
        )

        try:
            # LLM client sync/async olabilir
            if asyncio.iscoroutinefunction(self.llm.generate):
                return await self.llm.generate(prompt)  # type: ignore
            else:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.llm.generate, prompt)
        except Exception as exc:
            logger.error("Özet üretme hatası: %s", exc)
            return ""

    async def _save_mining_result(
        self,
        topic: str,
        chunks: list[KnowledgeChunk],
        summary: str,
    ) -> None:
        """Madencilik sonucunu JSON olarak kaydet."""
        safe_topic = re.sub(r'[^\w\-]+', '_', topic.lower())[:60]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filepath = self.knowledge_base_dir / f"{safe_topic}_{timestamp}.json"

        payload = {
            "topic": topic,
            "summary": summary,
            "mined_at": datetime.utcnow().isoformat(),
            "chunks": [c.to_dict() for c in chunks],
        }

        try:
            filepath.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info("Madencilik sonucu kaydedildi: %s", filepath)
        except Exception as exc:
            logger.error("Kaydetme hatası: %s", exc)

    # ------------------------------------------------------------------
    # RAG İndeksleme
    # ------------------------------------------------------------------
    async def index_to_rag(self, chunks: list[KnowledgeChunk]) -> bool:
        """Toplanan bilgileri ChromaDB'ye indeksle."""
        if not self.rag:
            logger.warning("RAG pipeline bağlı değil, indeksleme atlanıyor.")
            return False

        success = True
        for chunk in chunks:
            try:
                # RAG pipeline arayüzüne göre esnek çağrı
                if asyncio.iscoroutinefunction(self.rag.add_document):
                    await self.rag.add_document(  # type: ignore
                        content=chunk.content,
                        metadata={
                            "source": chunk.source,
                            "url": chunk.url,
                            "title": chunk.title,
                            "fetched_at": chunk.fetched_at.isoformat(),
                        },
                    )
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None,
                        lambda: self.rag.add_document(
                            content=chunk.content,
                            metadata={
                                "source": chunk.source,
                                "url": chunk.url,
                                "title": chunk.title,
                                "fetched_at": chunk.fetched_at.isoformat(),
                            },
                        ),
                    )
            except Exception as exc:
                logger.error("RAG indeksleme hatası (%s): %s", chunk.title, exc)
                success = False

        logger.info("RAG'e %d chunk indekslendi.", len(chunks))
        return success

    # ------------------------------------------------------------------
    # Periyodik Güncelleme
    # ------------------------------------------------------------------
    async def update_knowledge_base(
        self,
        topics: list[str],
        force: bool = False,
    ) -> UpdateReport:
        """Periyodik bilgi güncelleme."""
        report = UpdateReport()

        for topic in topics:
            try:
                # Eski kayıtları bul ve pasifleştir (opsiyonel)
                if force:
                    await self._deprecate_topic(topic)

                result = await self.mine_topic(topic)
                report.new_chunks += len(result.chunks)

                # RAG'e indeksle
                if self.rag and result.chunks:
                    indexed = await self.index_to_rag(result.chunks)
                    if not indexed:
                        report.errors.append(
                            f"RAG indeksleme başarısız: {topic}"
                        )

                report.topics_processed += 1

            except Exception as exc:
                err_msg = f"{topic}: {exc}"
                report.errors.append(err_msg)
                logger.error("Güncelleme hatası: %s", err_msg)

        report.completed_at = datetime.utcnow()
        await self._save_report(report)
        return report

    async def _deprecate_topic(self, topic: str) -> None:
        """Eski topic kayıtlarını pasifleştir."""
        safe_topic = re.sub(r'[^\w\-]+', '_', topic.lower())[:60]
        for filepath in self.knowledge_base_dir.glob(f"{safe_topic}_*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                data["deprecated"] = True
                filepath.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                continue

    async def _save_report(self, report: UpdateReport) -> None:
        """Güncelleme raporunu kaydet."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filepath = self.knowledge_base_dir / f"report_{timestamp}.json"
        try:
            filepath.write_text(
                json.dumps(
                    {
                        "topics_processed": report.topics_processed,
                        "new_chunks": report.new_chunks,
                        "updated_chunks": report.updated_chunks,
                        "removed_chunks": report.removed_chunks,
                        "errors": report.errors,
                        "completed_at": report.completed_at.isoformat(),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.error("Rapor kaydetme hatası: %s", exc)

    # ------------------------------------------------------------------
    # Yardımcılar
    # ------------------------------------------------------------------
    @staticmethod
    def _strip_html(raw_html: str) -> str:
        """HTML tag'lerini temizle."""
        clean = re.sub(r"<[^>]+>", " ", raw_html)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    @staticmethod
    def _clean_whitespace(text: str) -> str:
        """Fazla boşlukları temizle."""
        return re.sub(r"\s+", " ", text).strip()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    async def close(self) -> None:
        """HTTP client'i kapat."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
