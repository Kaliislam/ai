"""Tehdit istihbaratı — Hacker haberleri, CERT, CISA, AlienVault entegrasyonu."""

import asyncio
import csv
import hashlib
import html
import io
import json
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

import feedparser
import httpx


@dataclass
class ThreatArticle:
    title: str
    source: str               # The Hacker News, BleepingComputer, etc.
    url: str
    published: datetime
    summary: str
    tags: List[str]           # ransomware, apt, vulnerability, breach
    severity: str             # critical, high, medium, low
    affected: List[str]       # Etkilenen ürünler/şirketler
    iocs: List[str]           # Indicators of Compromise (IP, domain, hash)
    raw: str = ""             # Raw RSS entry

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "published": self.published.isoformat() if self.published else None,
            "summary": self.summary,
            "tags": self.tags,
            "severity": self.severity,
            "affected": self.affected,
            "iocs": self.iocs,
        }

    def to_markdown(self) -> str:
        tag_str = ", ".join(self.tags) if self.tags else "-"
        aff_str = ", ".join(self.affected) if self.affected else "-"
        ioc_str = ", ".join(self.iocs[:5]) if self.iocs else "-"
        pub = self.published.strftime("%Y-%m-%d %H:%M") if self.published else "Bilinmiyor"
        return (
            f"## {self.title}\n\n"
            f"- **Kaynak:** {self.source}\n"
            f"- **Tarih:** {pub}\n"
            f"- **Ciddiyet:** {self.severity.upper()}\n"
            f"- **Etiketler:** {tag_str}\n"
            f"- **Etkilenen:** {aff_str}\n"
            f"- **IOC'ler:** {ioc_str}\n"
            f"- **URL:** {self.url}\n\n"
            f"{self.summary}\n"
        )


class ThreatIntelligence:
    """Güvenlik haberleri ve tehdit istihbaratı toplayıcı."""

    FEEDS: Dict[str, str] = {
        "hackernews": "https://feeds.feedburner.com/TheHackersNews",
        "bleepingcomputer": "https://www.bleepingcomputer.com/feed/",
        "darkreading": "https://www.darkreading.com/rss.xml",
        "krebs": "https://krebsonsecurity.com/feed/",
        "threatpost": "https://threatpost.com/feed/",
        "securityweek": "https://www.securityweek.com/feed/",
        "infosecurity": "https://www.infosecurity-magazine.com/rss/news/",
        "cert_cc": "https://www.kb.cert.org/vuls/feed",
        "cisa": "https://www.cisa.gov/uscert/ncas/current-activity.xml",
    }

    _SEVERITY_KEYWORDS: Dict[str, List[str]] = {
        "critical": [
            "critical", "zero-day", "0-day", "remote code execution", "rce",
            "wormable", "exploit in the wild", "active exploitation",
            "privilege escalation", "full control", "arbitrary code",
        ],
        "high": [
            "high", "important", "ransomware", "apt", "lateral movement",
            "supply chain", "sophisticated", "nation-state", "espionage",
            "data breach", "million records", "credential stuffing",
        ],
        "medium": [
            "medium", "moderate", "denial of service", "dos", "xss",
            "information disclosure", "spoofing", "tampering", "csrf",
        ],
        "low": [
            "low", "minor", "informational", "best practice",
            "recommendation", "advisory",
        ],
    }

    _TAG_KEYWORDS: Dict[str, List[str]] = {
        "ransomware": ["ransomware", "ransom", "lockbit", "blackcat", "revil"],
        "apt": ["apt", "nation-state", "espionage", "advanced persistent"],
        "vulnerability": ["vulnerability", "cve", "exploit", "patch", "0-day"],
        "breach": ["breach", "leak", "data theft", "compromised", "stolen"],
        "malware": ["malware", "trojan", "backdoor", "rootkit", "spyware"],
        "phishing": ["phishing", "social engineering", "spear phishing"],
        "ddos": ["ddos", "denial of service"],
        "supply_chain": ["supply chain", "third party", "vendor"],
        "xss": ["xss", "cross-site scripting"],
        "sql_injection": ["sql injection", "sqli"],
    }

    def __init__(
        self,
        alienvault_api_key: Optional[str] = None,
        virustotal_api_key: Optional[str] = None,
        proxy: Optional[str] = None,
    ):
        self.av_key = alienvault_api_key
        self.vt_key = virustotal_api_key
        headers = {
            "User-Agent": (
                "TurkishJarvis-ThreatIntel/1.0 "
                "(https://github.com/turkishjarvis/threat-intel)"
            ),
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        }
        proxy_map = {"all://": proxy} if proxy else None
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10, read=45, write=10, pool=10),
            headers=headers,
            proxies=proxy_map,
            follow_redirects=True,
            http2=True,
        )
        self.articles: List[ThreatArticle] = []
        self._last_fetch: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_iocs(text: str) -> List[str]:
        """Metin içinden IOC örnekleri çıkarır (IP, domain, hash)."""
        iocs: List[str] = []
        if not text:
            return iocs
        # IPv4
        ipv4_re = re.compile(
            r"\b((?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
            r"\.(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
            r"\.(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
            r"\.(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d))\b"
        )
        # Domain (basit)
        domain_re = re.compile(
            r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)"
            r"+(?:[a-zA-Z]{2,})\b"
        )
        # MD5 / SHA1 / SHA256
        hash_re = re.compile(r"\b([a-fA-F0-9]{32,64})\b")

        # IP filtrele: 0.0.0.0, 127.0.0.1, 192.168.x.x gibi private IP'leri atla
        found_ips = set(ipv4_re.findall(text))
        private_prefixes = (
            "127.", "10.", "192.168.", "172.16.", "172.17.", "172.18.",
            "172.19.", "172.20.", "172.21.", "172.22.", "172.23.",
            "172.24.", "172.25.", "172.26.", "172.27.", "172.28.",
            "172.29.", "172.30.", "172.31.", "169.254.", "0.0.0.0",
            "255.255.255.", "224.", "239.",
        )
        for ip in found_ips:
            if not ip.startswith(private_prefixes):
                iocs.append(ip)

        for d in set(domain_re.findall(text)):
            dlower = d.lower()
            if "github.com" not in dlower and "feedburner" not in dlower:
                iocs.append(d)

        for h in set(hash_re.findall(text)):
            if len(h) in (32, 40, 64):
                iocs.append(h)

        return list(set(iocs))

    @staticmethod
    def _extract_affected(text: str) -> List[str]:
        """Metinden muhtemelen etkilenen ürün/şirket isimlerini çıkarır."""
        if not text:
            return []
        products = []
        # Windows, Microsoft, Cisco, VMware, Oracle, Apple, Linux, Android, iOS
        prod_keywords = [
            "Windows", "Microsoft", "Cisco", "VMware", "Oracle", "Apple",
            "Linux", "Android", "iOS", "Google", "Mozilla", "Adobe",
            "Fortinet", "Palo Alto", "SonicWall", "F5", "Juniper",
            "SAP", "IBM", "Red Hat", "Ubuntu", "Debian", "CentOS",
            "Chrome", "Firefox", "Edge", "Safari", "WordPress",
            "Apache", "nginx", "MySQL", "PostgreSQL", "OpenSSL",
            "GitHub", "GitLab", "Slack", "Zoom", "TeamViewer",
        ]
        lowered = text.lower()
        for p in prod_keywords:
            if p.lower() in lowered:
                products.append(p)
        return list(set(products))

    def _classify(self, text: str) -> Tuple[str, List[str]]:
        """Verilen metne göre severity + tag belirler."""
        low = text.lower()
        severity = "low"
        for sev, keywords in self._SEVERITY_KEYWORDS.items():
            if any(k in low for k in keywords):
                if severity == "low":
                    severity = sev
                elif sev == "critical":
                    severity = sev
                elif sev == "high" and severity in ("medium", "low"):
                    severity = sev
                elif sev == "medium" and severity == "low":
                    severity = sev

        tags: List[str] = []
        for tag, keywords in self._TAG_KEYWORDS.items():
            if any(k in low for k in keywords):
                tags.append(tag)
        if not tags:
            tags = ["general"]
        return severity, tags

    @staticmethod
    def _parse_rss_date(entry: Any) -> datetime:
        """feedparser entry'den datetime çıkarır."""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
        if hasattr(entry, "created_parsed") and entry.created_parsed:
            return datetime(*entry.created_parsed[:6])
        return datetime.utcnow()

    # ------------------------------------------------------------------
    # RSS Fetching
    # ------------------------------------------------------------------

    async def _fetch_single_feed(self, name: str, url: str) -> List[ThreatArticle]:
        """Tek bir RSS feed'ini çeker ve ThreatArticle listesi döner."""
        articles: List[ThreatArticle] = []
        try:
            resp = await self.client.get(url, timeout=25.0)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:20]:
                title = entry.get("title", "Başlık Yok")
                link = entry.get("link", "")
                summary_raw = entry.get("summary", entry.get("description", ""))
                summary = html.unescape(re.sub(r"<[^>]+>", " ", summary_raw))
                published = self._parse_rss_date(entry)
                severity, tags = self._classify(title + " " + summary)
                iocs = self._extract_iocs(title + " " + summary)
                affected = self._extract_affected(title + " " + summary)
                raw = str(dict(entry))
                articles.append(
                    ThreatArticle(
                        title=title,
                        source=name,
                        url=link,
                        published=published,
                        summary=summary[:800],
                        tags=tags,
                        severity=severity,
                        affected=affected,
                        iocs=iocs,
                        raw=raw,
                    )
                )
        except httpx.HTTPStatusError as exc:
            print(f"[ThreatIntel] HTTP hatası ({name}): {exc.response.status_code}", file=sys.stderr)
        except httpx.RequestError as exc:
            print(f"[ThreatIntel] Ağ hatası ({name}): {exc}", file=sys.stderr)
        except Exception as exc:
            print(f"[ThreatIntel] Genel hata ({name}): {exc}", file=sys.stderr)
        return articles

    async def fetch_all_feeds(self, since_hours: int = 24) -> List[ThreatArticle]:
        """Tüm RSS feed'lerini çeker."""
        self.articles.clear()
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        tasks = [
            self._fetch_single_feed(name, url)
            for name, url in self.FEEDS.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, list):
                for art in res:
                    if art.published >= cutoff:
                        self.articles.append(art)
        # Tarihe göre sırala
        self.articles.sort(key=lambda a: a.published, reverse=True)
        self._last_fetch = datetime.utcnow()
        return self.articles

    async def fetch_cisa_alerts(self, since_hours: int = 168) -> List[ThreatArticle]:
        """CISA/US-CERT uyarılarını döner (zaten fetch_all_feeds içinde)."""
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        return [a for a in self.articles if a.source == "cisa" and a.published >= cutoff]

    # ------------------------------------------------------------------
    # AlienVault OTX (Free API)
    # ------------------------------------------------------------------

    async def fetch_alienvault_pulses(
        self, limit: int = 10, search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """AlienVault OTX pulses (ücretsiz API)."""
        results: List[Dict[str, Any]] = []
        headers = {"X-OTX-API-KEY": self.av_key} if self.av_key else {}
        url = "https://otx.alienvault.com/api/v1/pulses/subscribed"
        params: Dict[str, Any] = {"limit": limit}
        if search:
            params["q"] = search
        try:
            resp = await self.client.get(url, headers=headers, params=params, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            for pulse in data.get("results", [])[:limit]:
                iocs: List[str] = []
                indicators = pulse.get("indicators", [])
                for ind in indicators[:50]:
                    val = ind.get("indicator", "")
                    if val:
                        iocs.append(val)
                results.append({
                    "id": pulse.get("id"),
                    "name": pulse.get("name"),
                    "description": pulse.get("description", "")[:500],
                    "tags": pulse.get("tags", []),
                    "author": pulse.get("author", {}).get("username"),
                    "created": pulse.get("created"),
                    "modified": pulse.get("modified"),
                    "tlp": pulse.get("TLP"),
                    "iocs": iocs,
                    "references": pulse.get("references", []),
                    "malware_families": pulse.get("malware_families", []),
                })
        except httpx.HTTPStatusError as exc:
            print(f"[ThreatIntel] AlienVault HTTP hatası: {exc.response.status_code}", file=sys.stderr)
        except Exception as exc:
            print(f"[ThreatIntel] AlienVault hatası: {exc}", file=sys.stderr)
        return results

    async def fetch_alienvault_pulse_details(self, pulse_id: str) -> Dict[str, Any]:
        """Tek bir OTX pulse detayını getirir."""
        headers = {"X-OTX-API-KEY": self.av_key} if self.av_key else {}
        url = f"https://otx.alienvault.com/api/v1/pulses/{pulse_id}"
        try:
            resp = await self.client.get(url, headers=headers, timeout=30.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            print(f"[ThreatIntel] AlienVault pulse detay hatası: {exc}", file=sys.stderr)
            return {}

    # ------------------------------------------------------------------
    # Abuse.ch
    # ------------------------------------------------------------------

    async def fetch_abuse_ch(self) -> Dict[str, Any]:
        """Abuse.ch verileri (malware URL'leri, hash'ler)."""
        data: Dict[str, Any] = {"urlhaus": [], "malware_bazaar": [], "threatfox": []}
        try:
            # URLhaus CSV
            urlhaus_url = "https://urlhaus.abuse.ch/downloads/csv_recent/"
            resp = await self.client.get(urlhaus_url, timeout=30.0)
            if resp.status_code == 200:
                csv_text = resp.text
                lines = csv_text.splitlines()
                reader = csv.DictReader(lines)
                for row in list(reader)[:200]:
                    data["urlhaus"].append({
                        "id": row.get("id"),
                        "dateadded": row.get("dateadded"),
                        "url": row.get("url"),
                        "url_status": row.get("url_status"),
                        "threat": row.get("threat"),
                        "tags": row.get("tags", "").split(",") if row.get("tags") else [],
                        "urlhaus_link": row.get("urlhaus_link"),
                        "reporter": row.get("reporter"),
                    })
        except Exception as exc:
            print(f"[ThreatIntel] Abuse.ch URLhaus hatası: {exc}", file=sys.stderr)

        try:
            # MalwareBazaar recent
            mb_url = "https://bazaar.abuse.ch/export/csv/recent/"
            resp = await self.client.get(mb_url, timeout=30.0)
            if resp.status_code == 200:
                csv_text = resp.text
                lines = csv_text.splitlines()
                reader = csv.DictReader(lines)
                for row in list(reader)[:200]:
                    data["malware_bazaar"].append({
                        "sha256_hash": row.get("sha256_hash"),
                        "first_seen": row.get("first_seen_utc"),
                        "tags": row.get("tags", "").split(",") if row.get("tags") else [],
                        "file_type": row.get("file_type_guess"),
                        "signature": row.get("signature"),
                    })
        except Exception as exc:
            print(f"[ThreatIntel] Abuse.ch MalwareBazaar hatası: {exc}", file=sys.stderr)

        try:
            # ThreatFox IOC list (recent)
            tf_url = "https://threatfox.abuse.ch/export/csv/recent/"
            resp = await self.client.get(tf_url, timeout=30.0)
            if resp.status_code == 200:
                csv_text = resp.text
                lines = csv_text.splitlines()
                reader = csv.DictReader(lines)
                for row in list(reader)[:200]:
                    data["threatfox"].append({
                        "ioc": row.get("ioc"),
                        "ioc_type": row.get("ioc_type"),
                        "threat_type": row.get("threat_type"),
                        "malware": row.get("malware"),
                        "first_seen": row.get("first_seen_utc"),
                        "tags": row.get("tags", "").split(",") if row.get("tags") else [],
                    })
        except Exception as exc:
            print(f"[ThreatIntel] Abuse.ch ThreatFox hatası: {exc}", file=sys.stderr)

        return data

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_by_tag(self, tag: str) -> List[ThreatArticle]:
        """Etikete göre filtrele: ransomware, apt, xss, breach."""
        tag_lower = tag.lower()
        return [a for a in self.articles if tag_lower in a.tags]

    def filter_by_severity(self, severity: str) -> List[ThreatArticle]:
        """Ciddiyete göre filtrele."""
        sev_lower = severity.lower()
        return [a for a in self.articles if a.severity == sev_lower]

    def filter_by_keyword(self, keyword: str) -> List[ThreatArticle]:
        """Anahtar kelimeye göre filtrele."""
        kw_lower = keyword.lower()
        return [
            a for a in self.articles
            if kw_lower in a.title.lower() or kw_lower in a.summary.lower()
        ]

    def filter_by_date(self, start: datetime, end: datetime) -> List[ThreatArticle]:
        """Tarih aralığına göre filtrele."""
        return [a for a in self.articles if start <= a.published <= end]

    def get_critical_alerts(self) -> List[ThreatArticle]:
        """Sadece critical seviyedeki haberleri döner."""
        return self.filter_by_severity("critical")

    # ------------------------------------------------------------------
    # Daily Brief
    # ------------------------------------------------------------------

    async def generate_daily_brief(self, top_n: int = 10) -> str:
        """Günlük tehdit özeti (Markdown formatında)."""
        if not self.articles or (
            self._last_fetch and (datetime.utcnow() - self._last_fetch) > timedelta(hours=2)
        ):
            await self.fetch_all_feeds(since_hours=24)

        lines: List[str] = [
            "# 🛡️ Günlük Tehdit Özeti",
            "",
            f"**Tarih:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Toplam Haber:** {len(self.articles)}",
            "",
            "---",
            "",
        ]

        critical = self.filter_by_severity("critical")
        high = self.filter_by_severity("high")
        ransomware = self.filter_by_tag("ransomware")
        apt = self.filter_by_tag("apt")
        vulns = self.filter_by_tag("vulnerability")

        lines.append("## 📊 Özet İstatistikler")
        lines.append("")
        lines.append(f"- **Critical:** {len(critical)}")
        lines.append(f"- **High:** {len(high)}")
        lines.append(f"- **Ransomware:** {len(ransomware)}")
        lines.append(f"- **APT:** {len(apt)}")
        lines.append(f"- **Vulnerability:** {len(vulns)}")
        lines.append("")
        lines.append("---")
        lines.append("")

        if critical:
            lines.append("## 🔴 Critical Uyarılar")
            lines.append("")
            for art in critical[:5]:
                lines.append(art.to_markdown())
            lines.append("")

        lines.append("## 📰 Son Haberler")
        lines.append("")
        for art in self.articles[:top_n]:
            lines.append(art.to_markdown())

        all_iocs: List[str] = []
        for art in self.articles[:top_n]:
            all_iocs.extend(art.iocs)
        if all_iocs:
            unique_iocs = sorted(set(all_iocs))[:30]
            lines.append("## 🔍 Tespit Edilen IOC'ler")
            lines.append("")
            for ioc in unique_iocs:
                lines.append(f"- `{ioc}`")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*Bu rapor otomatik olarak oluşturulmuştur.*")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_json(self, filepath: str, articles: Optional[List[ThreatArticle]] = None) -> None:
        """Makale listesini JSON olarak dışa aktarır."""
        target = articles if articles is not None else self.articles
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump([a.to_dict() for a in target], fh, ensure_ascii=False, indent=2)

    def export_markdown(self, filepath: str, articles: Optional[List[ThreatArticle]] = None) -> None:
        """Makale listesini Markdown olarak dışa aktarır."""
        target = articles if articles is not None else self.articles
        with open(filepath, "w", encoding="utf-8") as fh:
            for art in target:
                fh.write(art.to_markdown())
                fh.write("\n---\n\n")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
