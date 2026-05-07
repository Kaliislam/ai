"""Academic & scientific search — 5 free APIs, no keys needed."""

import asyncio
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

import httpx


@dataclass
class AcademicResult:
    """Unified academic search result."""

    title: str
    url: str
    snippet: str
    source: str
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    score: float = 0.0
    published_at: Optional[str] = None
    pdf_url: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


class RateLimiter:
    """Per-domain rate limiter."""

    def __init__(self, default_delay: float = 1.0):
        self._last_request: Dict[str, float] = {}
        self._default_delay = default_delay
        self._lock = asyncio.Lock()

    async def acquire(self, domain: str, custom_delay: Optional[float] = None):
        async with self._lock:
            now = time.time()
            delay = custom_delay or self._default_delay
            last = self._last_request.get(domain, 0)
            wait = max(0, delay - (now - last))
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request[domain] = time.time()


class SemanticScholarAPI:
    """Semantic Scholar API — free, no key required (generous limits)."""

    API_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/json", "User-Agent": "TurkishJARVIS/1.0"},
        )
        self.limiter = RateLimiter(default_delay=1.0)

    async def search(self, query: str, max_results: int = 10) -> List[AcademicResult]:
        """Search papers via Semantic Scholar."""
        await self.limiter.acquire("semanticscholar.org", 1.0)
        fields = "title,authors,year,abstract,openAccessPdf,externalIds"
        params: Dict[str, Any] = {"query": query, "fields": fields, "limit": max_results}
        try:
            resp = await self.client.get(f"{self.API_URL}/paper/search", params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse(data, max_results)
        except Exception as e:
            return [AcademicResult(title="", url="", snippet=f"Semantic Scholar error: {e}", source="semanticscholar", score=0.0)]

    def _parse(self, data: Dict, max_results: int) -> List[AcademicResult]:
        results: List[AcademicResult] = []
        for item in data.get("data", [])[:max_results]:
            paper_id = item.get("paperId", "")
            authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
            pdf = item.get("openAccessPdf", {}).get("url") if item.get("openAccessPdf") else None
            year = item.get("year")
            results.append(
                AcademicResult(
                    title=item.get("title", ""),
                    url=f"https://www.semanticscholar.org/paper/{paper_id}",
                    snippet=item.get("abstract", "")[:500] if item.get("abstract") else "",
                    source="semanticscholar",
                    authors=authors,
                    year=int(year) if year else None,
                    doi=item.get("externalIds", {}).get("DOI"),
                    score=0.92,
                    pdf_url=pdf,
                    raw=item,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class CrossRefAPI:
    """CrossRef API — free, no key required (polite pool recommended)."""

    API_URL = "https://api.crossref.org/works"

    def __init__(self, mailto: Optional[str] = None):
        self.mailto = mailto or "jarvis@example.com"
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Accept": "application/json",
                "User-Agent": f"TurkishJARVIS/1.0 (mailto:{self.mailto})",
            },
        )
        self.limiter = RateLimiter(default_delay=1.0)

    async def search(self, query: str, max_results: int = 10) -> List[AcademicResult]:
        """Search works via CrossRef."""
        await self.limiter.acquire("crossref.org", 1.0)
        params: Dict[str, Any] = {"query": query, "rows": max_results, "sort": "relevance", "order": "desc"}
        try:
            resp = await self.client.get(self.API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse(data, max_results)
        except Exception as e:
            return [AcademicResult(title="", url="", snippet=f"CrossRef error: {e}", source="crossref", score=0.0)]

    def _parse(self, data: Dict, max_results: int) -> List[AcademicResult]:
        results: List[AcademicResult] = []
        for item in data.get("message", {}).get("items", [])[:max_results]:
            authors = []
            for a in item.get("author", []):
                name = f"{a.get('given', '')} {a.get('family', '')}".strip()
                if name:
                    authors.append(name)
            url = item.get("URL", "")
            if not url and item.get("DOI"):
                url = f"https://doi.org/{item['DOI']}"
            year = None
            date_parts = item.get("published-print", {}).get("date-parts", [[]])[0]
            if not date_parts:
                date_parts = item.get("published-online", {}).get("date-parts", [[]])[0]
            if date_parts:
                try:
                    year = int(date_parts[0])
                except (ValueError, IndexError):
                    pass
            results.append(
                AcademicResult(
                    title=item.get("title", [""])[0] if isinstance(item.get("title"), list) else item.get("title", ""),
                    url=url,
                    snippet=item.get("abstract", "")[:500] if item.get("abstract") else "",
                    source="crossref",
                    authors=authors,
                    year=year,
                    doi=item.get("DOI"),
                    score=0.85,
                    raw=item,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class CoreAPI:
    """CORE API — free tier, no key required for basic search."""

    API_URL = "https://api.core.ac.uk/v3/search/works"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Accept": "application/json",
                "User-Agent": "TurkishJARVIS/1.0",
            },
        )
        self.limiter = RateLimiter(default_delay=1.0)

    async def search(self, query: str, max_results: int = 10) -> List[AcademicResult]:
        """Search CORE repository."""
        await self.limiter.acquire("core.ac.uk", 1.0)
        params: Dict[str, Any] = {"q": query, "limit": max_results, "offset": 0}
        headers: Dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            resp = await self.client.get(self.API_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return self._parse(data, max_results)
        except Exception as e:
            return [AcademicResult(title="", url="", snippet=f"CORE error: {e}", source="core", score=0.0)]

    def _parse(self, data: Dict, max_results: int) -> List[AcademicResult]:
        results: List[AcademicResult] = []
        for item in data.get("results", [])[:max_results]:
            authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
            year = None
            pub_date = item.get("publishedDate") or item.get("yearPublished")
            if pub_date:
                m = re.search(r"(\d{4})", str(pub_date))
                if m:
                    year = int(m.group(1))
            pdf = None
            links = item.get("links", [])
            for link in links:
                if link.get("type") == "download" or "pdf" in link.get("url", "").lower():
                    pdf = link.get("url")
                    break
            results.append(
                AcademicResult(
                    title=item.get("title", ""),
                    url=item.get("links", [{}])[0].get("url", "") if item.get("links") else "",
                    snippet=item.get("abstract", "")[:500] if item.get("abstract") else "",
                    source="core",
                    authors=authors,
                    year=year,
                    doi=item.get("doi"),
                    score=0.83,
                    pdf_url=pdf,
                    raw=item,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class ArXivAPI:
    """arXiv API — completely free, always open."""

    API_URL = "http://export.arxiv.org/api/query"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/atom+xml", "User-Agent": "TurkishJARVIS/1.0"},
        )
        self.limiter = RateLimiter(default_delay=3.0)

    async def search(self, query: str, max_results: int = 10) -> List[AcademicResult]:
        """Search arXiv via Atom API."""
        await self.limiter.acquire("export.arxiv.org", 3.0)
        params: Dict[str, Any] = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        try:
            resp = await self.client.get(self.API_URL, params=params)
            resp.raise_for_status()
            return self._parse_atom(resp.text, max_results)
        except Exception as e:
            return [AcademicResult(title="", url="", snippet=f"arXiv error: {e}", source="arxiv", score=0.0)]

    def _parse_atom(self, xml_text: str, max_results: int) -> List[AcademicResult]:
        results: List[AcademicResult] = []
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        try:
            root = ET.fromstring(xml_text.encode("utf-8"))
        except ET.ParseError as e:
            return [AcademicResult(title="", url="", snippet=f"arXiv XML parse error: {e}", source="arxiv", score=0.0)]
        for entry in root.findall("atom:entry", ns)[:max_results]:
            title = entry.findtext("atom:title", "", ns)
            summary = entry.findtext("atom:summary", "", ns)
            id_url = entry.findtext("atom:id", "", ns)
            authors = [a.findtext("atom:name", "", ns) for a in entry.findall("atom:author", ns) if a.findtext("atom:name", "", ns)]
            pdf_link = None
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf" or link.get("type") == "application/pdf":
                    pdf_link = link.get("href")
                    break
            published = entry.findtext("atom:published", "", ns)
            year = None
            if published:
                m = re.search(r"(\d{4})", published)
                if m:
                    year = int(m.group(1))
            doi = None
            for cat in entry.findall("arxiv:doi", ns):
                doi = cat.text
            results.append(
                AcademicResult(
                    title=title.strip(),
                    url=id_url,
                    snippet=summary.strip()[:500],
                    source="arxiv",
                    authors=authors,
                    year=year,
                    doi=doi,
                    score=0.88,
                    pdf_url=pdf_link,
                    published_at=published,
                    raw={"id": id_url},
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class PubMedEUtils:
    """PubMed E-utilities — free, no key required."""

    ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/xml", "User-Agent": "TurkishJARVIS/1.0"},
        )
        self.limiter = RateLimiter(default_delay=0.4)

    async def search(self, query: str, max_results: int = 10) -> List[AcademicResult]:
        """Search PubMed via E-utilities."""
        await self.limiter.acquire("ncbi.nlm.nih.gov", 0.4)
        # Step 1: esearch to get IDs
        search_params: Dict[str, Any] = {"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"}
        if self.api_key:
            search_params["api_key"] = self.api_key
        try:
            resp = await self.client.get(self.ESEARCH, params=search_params)
            resp.raise_for_status()
            search_data = resp.json()
            ids = search_data.get("esearchresult", {}).get("idlist", [])
            if not ids:
                return []
            # Step 2: esummary for details
            summary_params: Dict[str, Any] = {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}
            if self.api_key:
                summary_params["api_key"] = self.api_key
            sum_resp = await self.client.get(self.ESUMMARY, params=summary_params)
            sum_resp.raise_for_status()
            sum_data = sum_resp.json()
            return self._parse(sum_data, ids)
        except Exception as e:
            return [AcademicResult(title="", url="", snippet=f"PubMed error: {e}", source="pubmed", score=0.0)]

    def _parse(self, data: Dict, ids: List[str]) -> List[AcademicResult]:
        results: List[AcademicResult] = []
        result_dict = data.get("result", {})
        for pmid in ids:
            item = result_dict.get(pmid, {})
            if not item:
                continue
            authors = []
            for a in item.get("authors", []):
                name = a.get("name", "")
                if name:
                    authors.append(name)
            year = None
            pubdate = item.get("pubdate", "")
            m = re.search(r"(\d{4})", pubdate)
            if m:
                year = int(m.group(1))
            doi = item.get("elocationid", "")
            if doi.startswith("doi: "):
                doi = doi[5:]
            results.append(
                AcademicResult(
                    title=item.get("title", ""),
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    snippet=item.get("abstracttext", "")[:500] if item.get("abstracttext") else "",
                    source="pubmed",
                    authors=authors,
                    year=year,
                    doi=doi or None,
                    score=0.87,
                    published_at=pubdate,
                    raw=item,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class AcademicSearchAggregator:
    """Run all academic sources and aggregate."""

    def __init__(self, crossref_mailto: Optional[str] = None, core_api_key: Optional[str] = None, pubmed_key: Optional[str] = None):
        self.semantic = SemanticScholarAPI()
        self.crossref = CrossRefAPI(mailto=crossref_mailto)
        self.core = CoreAPI(api_key=core_api_key)
        self.arxiv = ArXivAPI()
        self.pubmed = PubMedEUtils(api_key=pubmed_key)

    async def search_all(self, query: str, max_results: int = 10) -> Dict[str, List[AcademicResult]]:
        """Search all academic sources concurrently."""
        tasks = {
            "semanticscholar": asyncio.create_task(self.semantic.search(query, max_results)),
            "crossref": asyncio.create_task(self.crossref.search(query, max_results)),
            "core": asyncio.create_task(self.core.search(query, max_results)),
            "arxiv": asyncio.create_task(self.arxiv.search(query, max_results)),
            "pubmed": asyncio.create_task(self.pubmed.search(query, max_results)),
        }
        results: Dict[str, List[AcademicResult]] = {}
        for name, task in tasks.items():
            try:
                results[name] = await asyncio.wait_for(asyncio.shield(task), timeout=40.0)
            except asyncio.TimeoutError:
                results[name] = [AcademicResult(title="", url="", snippet="Timeout", source=name, score=0.0)]
            except Exception as e:
                results[name] = [AcademicResult(title="", url="", snippet=f"Error: {e}", source=name, score=0.0)]
        return results

    async def combined_search(self, query: str, max_results: int = 10) -> List[AcademicResult]:
        """Search all and merge/deduplicate by DOI/title."""
        raw = await self.search_all(query, max_results)
        merged: List[AcademicResult] = []
        for src, items in raw.items():
            for item in items:
                if item.title or item.doi:
                    merged.append(item)
        return self._deduplicate(merged, max_results)

    @staticmethod
    def _deduplicate(results: List[AcademicResult], max_results: int) -> List[AcademicResult]:
        seen: set = set()
        out: List[AcademicResult] = []
        for r in results:
            key = r.doi or f"{r.title.lower().strip()[:80]}"
            key = re.sub(r"\s+", " ", key)
            if key not in seen:
                seen.add(key)
                out.append(r)
                if len(out) >= max_results:
                    break
        return out

    async def close(self):
        await asyncio.gather(
            self.semantic.close(),
            self.crossref.close(),
            self.core.close(),
            self.arxiv.close(),
            self.pubmed.close(),
            return_exceptions=True,
        )


# ── Quick test helper ─────────────────────────────────────────────────────────
async def _demo():
    agg = AcademicSearchAggregator()
    try:
        results = await agg.search_all("machine learning", max_results=3)
        for src, items in results.items():
            print(f"\n=== {src} ===")
            for it in items[:2]:
                print(f"  {it.title[:60]} ({it.year}) | {it.url[:50]}")
    finally:
        await agg.close()


if __name__ == "__main__":
    asyncio.run(_demo())
