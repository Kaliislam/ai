"""Bug Bounty raporlari — HackerOne, Bugcrowd, Intigriti entegrasyonu."""

import asyncio
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urljoin, quote

import httpx
from bs4 import BeautifulSoup


@dataclass
class BBRport:
    """Tekil bug bounty raporunu temsil eden veri sinifi."""

    title: str
    platform: str       # HackerOne / Bugcrowd / Intigriti / YesWeHack
    severity: str       # Critical / High / Medium / Low / Informational
    bounty: Optional[float]  # Odeme miktari ($)
    reporter: str       # Arastirmaci adi
    company: str        # Hedef sirket
    vulnerability_type: str  # XSS, SQLi, IDOR, RCE, etc.
    technique: str      # Kullanilan teknik
    writeup_url: str    # Rapor URL
    disclosed: bool     # Public mi
    cvss_score: Optional[float]
    disclosed_at: Optional[str] = None
    program_handle: Optional[str] = None
    state: str = "resolved"  # triaged / resolved / not applicable

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def bounty_str(self) -> str:
        if self.bounty is None:
            return "N/A"
        return f"${self.bounty:,.2f}"


class BugBountyTracker:
    """Bug bounty raporlarini izleyen ve analiz eden sistem.

    HackerOne Hacktivity sayfasi (public HTML scraping) uzerinden
    disclosed raporlari ceker. Bugcrowd CrowdStream ve Intigriti
    public programlari uzerinden ek veri toplar.
    """

    HACKERONE_API = "https://api.hackerone.com/v1"
    HACKERONE_HACKTIVITY = "https://hackerone.com/hacktivity"
    BUGCROWD_URL = "https://bugcrowd.com"
    BUGCROWD_CROWDSTREAM = "https://bugcrowd.com/crowdstream"
    INTIGRITI_PROGRAMS = "https://app.intigriti.com/programs"
    YESWEHACK_PROGRAMS = "https://api.yeswehack.com/programs"

    # CVSS 3.1 seviye esikleri
    CVSS_CRITICAL = 9.0
    CVSS_HIGH = 7.0
    CVSS_MEDIUM = 4.0

    def __init__(self, h1_api_key: Optional[str] = None,
                 h1_api_username: Optional[str] = None):
        self.h1_api_key = h1_api_key
        self.h1_api_username = h1_api_username
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
            },
        )
        self._reports_cache: List[BBRport] = []
        self._cache_ts: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _severity_from_cvss(self, cvss: Optional[float]) -> str:
        if cvss is None:
            return "Medium"
        if cvss >= self.CVSS_CRITICAL:
            return "Critical"
        if cvss >= self.CVSS_HIGH:
            return "High"
        if cvss >= self.CVSS_MEDIUM:
            return "Medium"
        return "Low"

    def _cvss_from_severity(self, severity: str) -> Optional[float]:
        mapping = {
            "critical": 9.5,
            "high": 8.0,
            "medium": 5.5,
            "low": 3.0,
            "informational": 0.0,
        }
        return mapping.get(severity.lower())

    def _extract_vuln_type(self, title: str) -> str:
        patterns = {
            "xss": [r"xss", r"cross.?site.?script", r"reflected.?xss", r"stored.?xss", r"dom.?xss"],
            "sqli": [r"sql.?inject", r"sqli", r"sql.?injection"],
            "idor": [r"idor", r"insecure\s+direct\s+object"],
            "rce": [r"rce", r"remote\s+code\s+exec", r"command\s+inject"],
            "ssrf": [r"ssrf", r"server.?side\s+request"],
            "lfi": [r"lfi", r"local\s+file\s+inclusion", r"path\s+traversal"],
            "csrf": [r"csrf", r"cross.?site.?request"],
            "xxe": [r"xxe", r"xml\s+external\s+entity"],
            "open_redirect": [r"open\s+redirect", r"url\s+redirect"],
            "information_disclosure": [r"information\s+disclosure", r"info\s+leak", r"sensitive\s+data\s+exposure"],
            "auth_bypass": [r"auth\s+bypass", r"authentication\s+bypass", r"login\s+bypass"],
            "privilege_escalation": [r"privilege\s+escalation", r"priv\s+esc", r"vertical\s+escalation"],
            "race_condition": [r"race\s+condition", r"toctou"],
            "graphql_injection": [r"graphql", r"graph.?ql"],
            "nosql_injection": [r"nosql", r"mongodb\s+inject"],
            "ssti": [r"ssti", r"server.?side\s+template\s+inject"],
            "clickjacking": [r"clickjack", r"ui\s+redress"],
        }
        title_lower = title.lower()
        for vuln_type, regexes in patterns.items():
            for pat in regexes:
                if re.search(pat, title_lower):
                    return vuln_type.upper().replace("_", " ")
        return "Unknown"

    def _extract_bounty(self, text: str) -> Optional[float]:
        if not text:
            return None
        # "$1,250.00" veya "$1250" veya "1,250 USD"
        match = re.search(r"[\$€£]?\s*([0-9,]+(?:\.[0-9]+)?)\s*(?:USD|EUR|GBP)?", text)
        if match:
            raw = match.group(1).replace(",", "")
            try:
                return float(raw)
            except ValueError:
                return None
        return None

    # ------------------------------------------------------------------
    # HackerOne — public disclosed scraping
    # ------------------------------------------------------------------

    async def get_hackerone_disclosed(self, limit: int = 20) -> List[BBRport]:
        """HackerOne public disclosed raporlarini Hacktivity sayfasindan ceker.

        Hacktivity endpoint: https://hackerone.com/hacktivity?querystring=
        Public olarak erisilebilir; API key gerektirmez.
        """
        reports: List[BBRport] = []
        page = 1
        per_page = 25

        while len(reports) < limit:
            url = (
                f"{self.HACKERONE_HACKTIVITY}?"
                f"querystring=&"
                f"filter=type%3Adisclosed&"
                f"page={page}&"
                f"size={per_page}"
            )
            try:
                resp = await self.client.get(url)
                if resp.status_code != 200:
                    break
                soup = BeautifulSoup(resp.text, "html.parser")
                # Hacktivity sayfasinda rapor kartlari
                cards = soup.find_all("article", class_=re.compile("hacktivity-item"))
                if not cards:
                    # Yedek: genel article / div yapisi
                    cards = soup.find_all("article")
                if not cards:
                    break

                for card in cards:
                    if len(reports) >= limit:
                        break
                    report = self._parse_h1_card(card)
                    if report:
                        reports.append(report)

                # Pagination kontrolu
                next_btn = soup.find("a", text=re.compile(r"next|older", re.I))
                if not next_btn and len(cards) < per_page:
                    break
                page += 1
                await asyncio.sleep(0.5)
            except Exception:
                break

        return reports[:limit]

    def _parse_h1_card(self, card: BeautifulSoup) -> Optional[BBRport]:
        try:
            title_tag = card.find("h4") or card.find("h3") or card.find("a")
            if not title_tag:
                return None
            title = title_tag.get_text(strip=True)

            # Reporter
            reporter = "unknown"
            reporter_tag = card.find("a", href=re.compile(r"/"))
            if reporter_tag:
                reporter = reporter_tag.get_text(strip=True)

            # Company / program
            company = "unknown"
            company_tag = card.find("span", class_=re.compile("program"))
            if company_tag:
                company = company_tag.get_text(strip=True)

            # Bounty
            bounty_text = ""
            bounty_tag = card.find("span", class_=re.compile("bounty|reward|amount"))
            if bounty_tag:
                bounty_text = bounty_tag.get_text(strip=True)
            bounty = self._extract_bounty(bounty_text)

            # Severity
            severity = "Medium"
            sev_tag = card.find("span", class_=re.compile("severity|priority"))
            if sev_tag:
                sev_text = sev_tag.get_text(strip=True).lower()
                for level in ["critical", "high", "medium", "low", "informational"]:
                    if level in sev_text:
                        severity = level.capitalize()
                        break

            # URL
            writeup_url = ""
            link_tag = card.find("a", href=True)
            if link_tag:
                href = link_tag["href"]
                writeup_url = urljoin("https://hackerone.com", href)

            vuln_type = self._extract_vuln_type(title)
            cvss = self._cvss_from_severity(severity)

            return BBRport(
                title=title,
                platform="HackerOne",
                severity=severity,
                bounty=bounty,
                reporter=reporter,
                company=company,
                vulnerability_type=vuln_type,
                technique="",
                writeup_url=writeup_url,
                disclosed=True,
                cvss_score=cvss,
                disclosed_at=None,
                program_handle=None,
                state="resolved",
            )
        except Exception:
            return None

    # ------------------------------------------------------------------
    # HackerOne — authenticated API (opsiyonel)
    # ------------------------------------------------------------------

    async def get_hackerone_api_reports(self, limit: int = 20) -> List[BBRport]:
        """HackerOne API v1 uzerinden raporlari ceker.

        API key icin https://api.hackerone.com/v1/docs ile kayit olunur.
        Ucretsiz tier mevcuttur.
        """
        if not self.h1_api_key or not self.h1_api_username:
            return []

        reports: List[BBRport] = []
        auth = httpx.BasicAuth(self.h1_api_username, self.h1_api_key)
        url = f"{self.HACKERONE_API}/reports"
        params = {"filter[state][]": "resolved", "page[size]": min(limit, 100)}

        try:
            resp = await self.client.get(url, auth=auth, params=params)
            if resp.status_code != 200:
                return []
            data = resp.json()
            for item in data.get("data", []):
                attr = item.get("attributes", {})
                title = attr.get("title", "Untitled")
                severity_text = attr.get("severity", {}).get("rating", "medium")
                severity = severity_text.capitalize()
                bounty = attr.get("bounty_amount", None)
                if bounty:
                    bounty = float(bounty)
                reporter_name = attr.get("reporter", {}).get("username", "unknown")
                program = attr.get("team", {}).get("handle", "unknown")
                state = attr.get("state", "resolved")
                disclosed = attr.get("disclosed", False)
                cvss = attr.get("cvss3_score", None)
                if cvss:
                    cvss = float(cvss)
                vuln_type = self._extract_vuln_type(title)

                report = BBRport(
                    title=title,
                    platform="HackerOne",
                    severity=severity,
                    bounty=bounty,
                    reporter=reporter_name,
                    company=program,
                    vulnerability_type=vuln_type,
                    technique="",
                    writeup_url=f"https://hackerone.com/reports/{item.get('id', '')}",
                    disclosed=disclosed,
                    cvss_score=cvss,
                    disclosed_at=attr.get("disclosed_at"),
                    program_handle=program,
                    state=state,
                )
                reports.append(report)
        except Exception:
            pass

        return reports[:limit]

    # ------------------------------------------------------------------
    # Bugcrowd — crowdstream scraping
    # ------------------------------------------------------------------

    async def get_bugcrowd_submissions(self, limit: int = 20) -> List[BBRport]:
        """Bugcrowd CrowdStream sayfasindan public submissionlari ceker.

        https://bugcrowd.com/crowdstream — public stream sayfasi.
        """
        reports: List[BBRport] = []
        try:
            resp = await self.client.get(self.BUGCROWD_CROWDSTREAM)
            if resp.status_code != 200:
                return reports
            soup = BeautifulSoup(resp.text, "html.parser")
            # CrowdStream ogesi: activity-item / stream-item siniflari
            items = soup.find_all("div", class_=re.compile("activity-item|stream-item|submission"))
            if not items:
                items = soup.find_all("article")
            if not items:
                items = soup.find_all("li", class_=re.compile("activity"))

            for item in items[:limit]:
                report = self._parse_bugcrowd_item(item)
                if report:
                    reports.append(report)
        except Exception:
            pass

        return reports[:limit]

    def _parse_bugcrowd_item(self, item: BeautifulSoup) -> Optional[BBRport]:
        try:
            title_tag = item.find("h4") or item.find("h3") or item.find("a")
            title = title_tag.get_text(strip=True) if title_tag else "Untitled"

            # Reporter
            reporter = "unknown"
            reporter_tag = item.find("a", href=re.compile(r"/researchers"))
            if reporter_tag:
                reporter = reporter_tag.get_text(strip=True)

            # Program / company
            company = "unknown"
            program_tag = item.find("a", href=re.compile(r"/programs"))
            if program_tag:
                company = program_tag.get_text(strip=True)

            # Bounty
            bounty = None
            bounty_tag = item.find("span", class_=re.compile("bounty|reward"))
            if bounty_tag:
                bounty = self._extract_bounty(bounty_tag.get_text(strip=True))

            # Severity
            severity = "Medium"
            sev_tag = item.find("span", class_=re.compile("severity|priority"))
            if sev_tag:
                sev_text = sev_tag.get_text(strip=True).lower()
                for level in ["critical", "high", "medium", "low", "informational"]:
                    if level in sev_text:
                        severity = level.capitalize()
                        break

            # URL
            writeup_url = ""
            link = item.find("a", href=True)
            if link:
                writeup_url = urljoin(self.BUGCROWD_URL, link["href"])

            vuln_type = self._extract_vuln_type(title)
            cvss = self._cvss_from_severity(severity)

            return BBRport(
                title=title,
                platform="Bugcrowd",
                severity=severity,
                bounty=bounty,
                reporter=reporter,
                company=company,
                vulnerability_type=vuln_type,
                technique="",
                writeup_url=writeup_url,
                disclosed=True,
                cvss_score=cvss,
            )
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Intigriti — public programs
    # ------------------------------------------------------------------

    async def get_intigriti_programs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Intigriti public program listesini ceker."""
        programs: List[Dict[str, Any]] = []
        try:
            resp = await self.client.get(self.INTIGRITI_PROGRAMS)
            if resp.status_code != 200:
                return programs
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all("div", class_=re.compile("program-card|program-item"))
            for card in cards[:limit]:
                name_tag = card.find("h3") or card.find("h2") or card.find("a")
                name = name_tag.get_text(strip=True) if name_tag else "Unknown"
                handle = ""
                link = card.find("a", href=True)
                if link:
                    handle = link["href"].strip("/").split("/")[-1]
                programs.append({
                    "name": name,
                    "handle": handle,
                    "url": urljoin("https://app.intigriti.com", link["href"]) if link else "",
                    "platform": "Intigriti",
                })
        except Exception:
            pass
        return programs

    # ------------------------------------------------------------------
    # YesWeHack — public programs
    # ------------------------------------------------------------------

    async def get_yeswehack_programs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """YesWeHack public program listesini ceker."""
        programs: List[Dict[str, Any]] = []
        try:
            resp = await self.client.get(self.YESWEHACK_PROGRAMS)
            if resp.status_code != 200:
                return programs
            data = resp.json()
            for item in data.get("items", [])[:limit]:
                programs.append({
                    "name": item.get("title", "Unknown"),
                    "handle": item.get("slug", ""),
                    "url": f"https://yeswehack.com/programs/{item.get('slug', '')}",
                    "platform": "YesWeHack",
                    "business_type": item.get("business_type", ""),
                })
        except Exception:
            pass
        return programs

    # ------------------------------------------------------------------
    # Search & filter
    # ------------------------------------------------------------------

    async def search_by_vuln_type(self, vuln_type: str, limit: int = 10) -> List[BBRport]:
        """Belirli zafiyet tipine gore ara.

        XSS, SQLi, IDOR, RCE, SSRF, LFI, CSRF, XXE, etc.
        Once cache'den arar; cache bos ise HackerOne'dan ceker.
        """
        if not self._reports_cache or self._cache_expired():
            self._reports_cache = await self.get_hackerone_discluded(limit=50)
            self._cache_ts = datetime.now()

        vuln_type_lower = vuln_type.lower()
        filtered = [
            r for r in self._reports_cache
            if vuln_type_lower in r.vulnerability_type.lower()
            or vuln_type_lower in r.title.lower()
        ]
        return filtered[:limit]

    def _cache_expired(self, ttl_seconds: int = 300) -> bool:
        if self._cache_ts is None:
            return True
        delta = datetime.now() - self._cache_ts
        return delta.total_seconds() > ttl_seconds

    async def get_hackerone_discluded(self, limit: int = 20) -> List[BBRport]:
        """Alias: disclosed + API raporlarini birlestirir."""
        disclosed = await self.get_hackerone_disclosed(limit=limit)
        if self.h1_api_key:
            api_reports = await self.get_hackerone_api_reports(limit=limit)
            # Birlestir ve duplicate'leri kaldir
            seen = set()
            merged = []
            for r in disclosed + api_reports:
                key = (r.title, r.reporter, r.company)
                if key not in seen:
                    seen.add(key)
                    merged.append(r)
            return merged[:limit]
        return disclosed

    # ------------------------------------------------------------------
    # Top earners & statistics
    # ------------------------------------------------------------------

    async def get_top_earners(self, limit: int = 10) -> List[Dict[str, Any]]:
        """En cok kazanan arastirmacilari bulur.

        HackerOne Hacktivity verisinden bounty toplamlari hesaplanir.
        """
        reports = await self.get_hackerone_disclosed(limit=100)
        earnings: Dict[str, Dict[str, Any]] = {}
        for r in reports:
            if r.bounty is None:
                continue
            name = r.reporter
            if name not in earnings:
                earnings[name] = {"reporter": name, "total_bounty": 0.0, "reports": 0, "companies": set()}
            earnings[name]["total_bounty"] += r.bounty
            earnings[name]["reports"] += 1
            earnings[name]["companies"].add(r.company)

        for e in earnings.values():
            e["companies"] = list(e["companies"])
            e["avg_bounty"] = e["total_bounty"] / max(e["reports"], 1)

        sorted_earners = sorted(earnings.values(), key=lambda x: x["total_bounty"], reverse=True)
        return sorted_earners[:limit]

    async def get_platform_stats(self) -> Dict[str, Any]:
        """Platform genel istatistikleri."""
        h1_reports = await self.get_hackerone_disclosed(limit=50)
        bc_reports = await self.get_bugcrowd_submissions(limit=50)
        all_reports = h1_reports + bc_reports

        total_bounty = sum(r.bounty for r in all_reports if r.bounty)
        severity_counts: Dict[str, int] = {}
        vuln_counts: Dict[str, int] = {}
        for r in all_reports:
            severity_counts[r.severity] = severity_counts.get(r.severity, 0) + 1
            vuln_counts[r.vulnerability_type] = vuln_counts.get(r.vulnerability_type, 0) + 1

        return {
            "total_reports": len(all_reports),
            "total_bounty": total_bounty,
            "avg_bounty": total_bounty / max(len([r for r in all_reports if r.bounty]), 1),
            "severity_distribution": severity_counts,
            "vulnerability_distribution": vuln_counts,
            "platforms": {"HackerOne": len(h1_reports), "Bugcrowd": len(bc_reports)},
        }

    # ------------------------------------------------------------------
    # Technique analysis
    # ------------------------------------------------------------------

    async def analyze_technique(self, report: BBRport) -> Dict[str, Any]:
        """Rapordaki tekniği analiz et.

        Basit icerik tabanli analiz; payload, bypass, chain, tool kullanimi
        ipuclarini cikarir.
        """
        analysis: Dict[str, Any] = {
            "vulnerability_type": report.vulnerability_type,
            "severity": report.severity,
            "cvss_score": report.cvss_score,
            "likely_techniques": [],
            "tools_mentioned": [],
            "bypass_patterns": [],
            "chain_complexity": "simple",
            "recommendation": "",
        }

        title_lower = report.title.lower()

        # Teknik belirleme
        techniques_map = {
            "reflected xss": ["payload reflection", "input validation bypass"],
            "stored xss": ["persistent payload", "filter evasion"],
            "dom xss": ["client-side injection", "sink manipulation"],
            "sql injection": ["union-based", "error-based", "blind (time-based)"],
            "idor": ["identifier manipulation", "mass assignment", "UUID enumeration"],
            "rce": ["command injection", "deserialization", "template injection"],
            "ssrf": ["internal service probing", "cloud metadata access"],
            "lfi": ["path traversal", "null byte injection", "wrapper abuse"],
            "xxe": ["xml parser abuse", "dtd exfiltration"],
            "csrf": ["token bypass", "double-submit cookie bypass"],
        }

        for vuln, techniques in techniques_map.items():
            if vuln in title_lower or vuln.replace(" ", "_") in report.vulnerability_type.lower():
                analysis["likely_techniques"] = techniques
                break

        # Tool ipuclari
        tools = ["burp suite", "sqlmap", "nmap", "ffuf", "gobuster", "dirbuster",
                 "postman", "curl", "wget", "python", "ruby", "js", "grep", "awk"]
        for tool in tools:
            if tool in title_lower:
                analysis["tools_mentioned"].append(tool)

        # Bypass / chain
        bypass_keywords = ["bypass", "filter bypass", "waf", "sandbox", "csp", "sop",
                           "cors", "oauth", "2fa", "mfa"]
        for kw in bypass_keywords:
            if kw in title_lower:
                analysis["bypass_patterns"].append(kw)

        if len(analysis["bypass_patterns"]) > 2:
            analysis["chain_complexity"] = "complex"
        elif len(analysis["bypass_patterns"]) > 0:
            analysis["chain_complexity"] = "moderate"

        # CVSS bazli tavsiye
        if report.cvss_score and report.cvss_score >= self.CVSS_CRITICAL:
            analysis["recommendation"] = (
                "Kritik seviye! Derhal duzeltme; yaygin etki analizi ve "
                "incident response proseduru baslatilmali."
            )
        elif report.cvss_score and report.cvss_score >= self.CVSS_HIGH:
            analysis["recommendation"] = (
                "Yuksek risk; kisa vadeli yama plani ve gecici onlemler (WAF kurali, "
                "input sanitization) uygulanmali."
            )
        else:
            analysis["recommendation"] = (
                "Standart duzeltme akisina alin; guvenlik testlerinde regresyon "
                "kontrolu yapilmali."
            )

        return analysis

    # ------------------------------------------------------------------
    # Learning material generation
    # ------------------------------------------------------------------

    async def generate_learning_material(self, reports: List[BBRport]) -> str:
        """Verilen raporlardan ogrenme materyali olusturur."""
        if not reports:
            return "Hic rapor bulunamadi."

        lines = [
            "# Bug Bounty Ogrenme Notlari",
            f"\nOlusturulma: {datetime.now().isoformat()}",
            f"Toplam rapor: {len(reports)}",
            "\n## Zafiyet Turleri Dagilimi\n",
        ]

        vuln_counts: Dict[str, int] = {}
        for r in reports:
            vuln_counts[r.vulnerability_type] = vuln_counts.get(r.vulnerability_type, 0) + 1

        for vuln, count in sorted(vuln_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{vuln}**: {count} rapor")

        lines.append("\n## Ornek Raporlar\n")
        for idx, r in enumerate(reports[:5], 1):
            lines.append(f"### {idx}. {r.title}")
            lines.append(f"- **Platform**: {r.platform}")
            lines.append(f"- **Sirket**: {r.company}")
            lines.append(f"- **Zafiyet**: {r.vulnerability_type}")
            lines.append(f"- **Severity**: {r.severity} (CVSS: {r.cvss_score})")
            lines.append(f"- **Odul**: {r.bounty_str}")
            lines.append(f"- **Arastirmaci**: {r.reporter}")
            lines.append(f"- **URL**: {r.writeup_url}")
            lines.append("")

        lines.append("\n## Teknik Ozetler\n")
        for r in reports[:5]:
            analysis = await self.analyze_technique(r)
            lines.append(f"### {r.title}")
            lines.append(f"- Muhtemel teknikler: {', '.join(analysis['likely_techniques']) or 'Belirsiz'}")
            lines.append(f"- Karmasiklik: {analysis['chain_complexity']}")
            lines.append(f"- Tavsiye: {analysis['recommendation']}")
            lines.append("")

        return "\n".join(lines)

    async def export_json(self, reports: List[BBRport], filepath: str) -> None:
        """Raporlari JSON olarak disari aktarir."""
        data = [r.to_dict() for r in reports]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def close(self) -> None:
        await self.client.aclose()


# ----------------------------------------------------------------------
# CLI / test arayuzu
# ----------------------------------------------------------------------

async def _demo() -> None:
    tracker = BugBountyTracker()
    print("=== HackerOne Disclosed Raporlar (ilk 5) ===")
    h1 = await tracker.get_hackerone_disclosed(limit=5)
    for r in h1:
        print(f"- {r.title} | {r.severity} | {r.bounty_str} | {r.company}")

    print("\n=== Bugcrowd Submissions (ilk 5) ===")
    bc = await tracker.get_bugcrowd_submissions(limit=5)
    for r in bc:
        print(f"- {r.title} | {r.severity} | {r.bounty_str} | {r.company}")

    print("\n=== Top Earners (ilk 5) ===")
    earners = await tracker.get_top_earners(limit=5)
    for e in earners:
        print(f"- {e['reporter']}: ${e['total_bounty']:,.2f} ({e['reports']} rapor)")

    print("\n=== Platform Istatistikleri ===")
    stats = await tracker.get_platform_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False, default=str))

    if h1:
        print("\n=== Teknik Analiz (ilk rapor) ===")
        analysis = await tracker.analyze_technique(h1[0])
        print(json.dumps(analysis, indent=2, ensure_ascii=False))

        print("\n=== Ogrenme Materyali (ilk 3 rapor) ===")
        material = await tracker.generate_learning_material(h1[:3])
        print(material[:1000] + "...")

    await tracker.close()


if __name__ == "__main__":
    asyncio.run(_demo())
