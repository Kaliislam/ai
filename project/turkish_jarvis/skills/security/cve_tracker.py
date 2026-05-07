"""CVE izleme — NIST NVD, MITRE, CIRCL, exploit-db entegrasyonu."""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Callable, Any

import httpx

logger = logging.getLogger("jarvis.cve")


@dataclass
class CVEEntry:
    """Tekil CVE kaydı."""

    cve_id: str                         # CVE-2025-1234
    published: str                      # 2025-01-15
    severity: str                       # CRITICAL / HIGH / MEDIUM / LOW / NONE
    cvss_score: float                   # 9.8
    description: str                    # Açıklama
    affected_products: List[str]        # ["Apache 2.4.49", "nginx 1.21"]
    references: List[str]             # URL listesi
    exploit_available: bool             # exploit-db'de exploit var mı
    mitigations: List[str]              # Çözüm önerileri
    cwe_ids: List[str]                  # CWE-79, CWE-89
    exploit_db_ids: List[str] = field(default_factory=list)
    epss_score: Optional[float] = None  # EPSS olasılık skoru

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def summary(self) -> str:
        return (
            f"[{self.severity}] {self.cve_id} | CVSS:{self.cvss_score} | "
            f"Exploit:{self.exploit_available} | {self.published}"
        )


class CVETacker:
    """CVE veritabanını izleyen ve raporlayan sistem."""

    NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    CIRCL_API = "https://cve.circl.lu/api/cve"
    MITRE_API = "https://cveawg.mitre.org/api/cve"
    EPSS_API = "https://api.first.org/data/v1/epss"

    EXPLOITDB_URL = "https://www.exploit-db.com/exploits/"
    EXPLOITDB_GITLAB_RAW = (
        "https://gitlab.com/exploit-database/exploitdb/-/raw/main/"
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit_seconds: float = 6.0,
        known_cves_file: Optional[str] = None,
    ):
        self.api_key = api_key
        self.rate_limit = rate_limit_seconds
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; TurkishJarvis-CVE-Tracker/1.0)"
                ),
                "Accept": "application/json",
            },
        )
        self.known_cves: set = set()
        self.known_cves_file = known_cves_file
        if known_cves_file:
            self._load_known_cves()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_known_cves(self) -> None:
        try:
            with open(self.known_cves_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                self.known_cves = set(data.get("known_cves", []))
        except FileNotFoundError:
            logger.info("Known-CVE dosyası bulunamadı; boş set ile başlanıyor.")
        except json.JSONDecodeError as exc:
            logger.warning("Known-CVE dosyası bozuktu: %s", exc)

    def _save_known_cves(self) -> None:
        if not self.known_cves_file:
            return
        payload = {
            "updated": datetime.utcnow().isoformat() + "Z",
            "known_cves": sorted(self.known_cves),
        }
        with open(self.known_cves_file, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # NVD helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _severity_from_cvss(score: float) -> str:
        if score >= 9.0:
            return "CRITICAL"
        if score >= 7.0:
            return "HIGH"
        if score >= 4.0:
            return "MEDIUM"
        if score > 0.0:
            return "LOW"
        return "NONE"

    def _parse_nvd_item(self, item: Dict[str, Any]) -> Optional[CVEEntry]:
        """NVD API 'vulnerabilities' listesinden tek CVEEntry üret."""
        cve = item.get("cve", {})
        cve_id = cve.get("id", "")
        if not cve_id:
            return None

        descriptions = cve.get("descriptions", [])
        desc = ""
        for d in descriptions:
            if d.get("lang", "") == "en":
                desc = d.get("value", "")
                break
        if not desc and descriptions:
            desc = descriptions[0].get("value", "")

        published = cve.get("published", "")[:10]

        # CVSS v3.1 öncelikli, yoksa v2
        metrics = cve.get("metrics", {})
        cvss_data = metrics.get("cvssMetricV31", metrics.get("cvssMetricV30", []))
        if not cvss_data:
            cvss_data = metrics.get("cvssMetricV2", [])

        cvss_score = 0.0
        severity = "NONE"
        if cvss_data:
            main = cvss_data[0]
            cvss_score = main.get("cvssData", {}).get("baseScore", 0.0)
            severity = main.get("cvssData", {}).get("baseSeverity", "")
            if not severity:
                severity = self._severity_from_cvss(cvss_score)

        references = [
            ref.get("url", "")
            for ref in cve.get("references", [])
            if ref.get("url")
        ]

        # CWE
        weaknesses = cve.get("weaknesses", [])
        cwe_ids: List[str] = []
        for w in weaknesses:
            for d in w.get("description", []):
                val = d.get("value", "")
                if val.startswith("CWE-"):
                    cwe_ids.append(val)

        # Affected products (NVD configurations üzerinden basit çözümleme)
        affected: List[str] = []
        configurations = cve.get("configurations", [])
        for conf in configurations:
            for node in conf.get("nodes", []):
                for cpe in node.get("cpeMatch", []):
                    criteria = cpe.get("criteria", "")
                    if criteria:
                        # cpe:2.3:a:vendor:product:version... -> vendor product version
                        parts = criteria.split(":")
                        if len(parts) >= 5:
                            vendor = parts[3]
                            product = parts[4]
                            version = parts[5] if len(parts) > 5 else "*"
                            affected.append(f"{vendor} {product} {version}")

        # Mitigations (tagged references)
        mitigations: List[str] = [
            ref.get("url", "")
            for ref in cve.get("references", [])
            if "Workaround" in ref.get("tags", [])
            or "Mitigation" in ref.get("tags", [])
            or "Vendor Advisory" in ref.get("tags", [])
        ]

        return CVEEntry(
            cve_id=cve_id,
            published=published,
            severity=severity,
            cvss_score=cvss_score,
            description=desc,
            affected_products=list(set(affected)),
            references=references,
            exploit_available=False,  # sonradan doldurulacak
            mitigations=mitigations,
            cwe_ids=list(set(cwe_ids)),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def get_recent_cves(
        self, days: int = 7, severity: Optional[str] = None, limit: int = 100
    ) -> List[CVEEntry]:
        """Son N gündeki CVE'leri NVD'den getir."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        pub_start = start_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        pub_end = end_date.strftime("%Y-%m-%dT%H:%M:%S.000")

        params: Dict[str, Any] = {
            "pubStartDate": pub_start,
            "pubEndDate": pub_end,
            "resultsPerPage": limit,
        }
        if self.api_key:
            params["apiKey"] = self.api_key

        logger.info("NVD recent CVEs: %s -> %s", pub_start[:10], pub_end[:10])
        try:
            resp = await self.client.get(self.NVD_API, params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("NVD HTTP hatası: %s", exc)
            return []
        except httpx.RequestError as exc:
            logger.error("NVD istek hatası: %s", exc)
            return []

        items = data.get("vulnerabilities", [])
        results: List[CVEEntry] = []
        for item in items:
            entry = self._parse_nvd_item(item)
            if entry:
                if severity and entry.severity != severity.upper():
                    continue
                results.append(entry)

        await asyncio.sleep(self.rate_limit)
        return results

    async def get_cve_details(self, cve_id: str) -> Optional[CVEEntry]:
        """Belirli bir CVE'nin detaylarını getir (NVD öncelikli, CIRCL yedek)."""
        # 1) NVD
        params: Dict[str, Any] = {"cveId": cve_id}
        if self.api_key:
            params["apiKey"] = self.api_key
        try:
            resp = await self.client.get(self.NVD_API, params=params)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("vulnerabilities", [])
            if items:
                entry = self._parse_nvd_item(items[0])
                if entry:
                    entry.exploit_available = await self.check_exploit_db(cve_id)
                    entry.epss_score = await self.get_epss_score(cve_id)
                    return entry
        except Exception as exc:
            logger.warning("NVD detay hatası (%s): %s", cve_id, exc)

        await asyncio.sleep(self.rate_limit)

        # 2) CIRCL fallback
        try:
            resp = await self.client.get(f"{self.CIRCL_API}/{cve_id}")
            resp.raise_for_status()
            data = resp.json()
            entry = self._parse_circl_item(data)
            if entry:
                entry.exploit_available = await self.check_exploit_db(cve_id)
                entry.epss_score = await self.get_epss_score(cve_id)
                return entry
        except Exception as exc:
            logger.warning("CIRCL detay hatası (%s): %s", cve_id, exc)

        return None

    async def search_by_product(
        self, product: str, limit: int = 40
    ) -> List[CVEEntry]:
        """Ürün adına göre CVE ara (NVD keyword search)."""
        params: Dict[str, Any] = {
            "keywordSearch": product,
            "resultsPerPage": limit,
        }
        if self.api_key:
            params["apiKey"] = self.api_key
        try:
            resp = await self.client.get(self.NVD_API, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("NVD ürün arama hatası: %s", exc)
            return []

        items = data.get("vulnerabilities", [])
        results: List[CVEEntry] = []
        for item in items:
            entry = self._parse_nvd_item(item)
            if entry:
                entry.exploit_available = await self.check_exploit_db(entry.cve_id)
                results.append(entry)
        await asyncio.sleep(self.rate_limit)
        return results

    # ------------------------------------------------------------------
    # CIRCL parser
    # ------------------------------------------------------------------
    def _parse_circl_item(self, data: Dict[str, Any]) -> Optional[CVEEntry]:
        cve_id = data.get("id", "")
        if not cve_id:
            return None
        summary = data.get("summary", "")
        published = data.get("Published", "")[:10]
        cvss = data.get("cvss", 0.0) or data.get("cvss3", 0.0)
        severity = self._severity_from_cvss(cvss)
        refs = data.get("references", [])
        cwe = data.get("cwe", "")
        cwe_ids = [cwe] if cwe else []
        return CVEEntry(
            cve_id=cve_id,
            published=published,
            severity=severity,
            cvss_score=cvss,
            description=summary,
            affected_products=[],
            references=refs,
            exploit_available=False,
            mitigations=[],
            cwe_ids=cwe_ids,
        )

    # ------------------------------------------------------------------
    # Exploit-DB
    # ------------------------------------------------------------------
    async def check_exploit_db(self, cve_id: str) -> bool:
        """Exploit-DB'de exploit var mı kontrol et."""
        # GitLab raw üzerinden hızlı grep: exploitdb/files_exploits.csv
        csv_url = (
            self.EXPLOITDB_GITLAB_RAW
            + "files_exploits.csv"
        )
        try:
            resp = await self.client.get(csv_url)
            resp.raise_for_status()
            text = resp.text
            return cve_id in text
        except Exception:
            pass

        # HTML search fallback
        search_url = "https://www.exploit-db.com/search"
        try:
            resp = await self.client.get(
                search_url, params={"cve": cve_id}, headers={"Accept": "text/html"}
            )
            return resp.status_code == 200 and "No results" not in resp.text
        except Exception:
            return False

    async def get_exploit_details(self, edb_id: str) -> Dict[str, Any]:
        """Exploit detaylarını getir (raw text)."""
        raw_url = (
            self.EXPLOITDB_GITLAB_RAW
            + f"exploits/{edb_id}.txt"
        )
        try:
            resp = await self.client.get(raw_url)
            if resp.status_code == 404:
                # alternatif: python, ruby, c, pl uzantıları dene
                for ext in ("py", "rb", "c", "pl", "sh", "cpp"):
                    alt = (
                        self.EXPLOITDB_GITLAB_RAW
                        + f"exploits/{edb_id}.{ext}"
                    )
                    r2 = await self.client.get(alt)
                    if r2.status_code == 200:
                        return {
                            "edb_id": edb_id,
                            "source": alt,
                            "code": r2.text,
                            "language": ext,
                        }
            else:
                resp.raise_for_status()
                return {
                    "edb_id": edb_id,
                    "source": raw_url,
                    "code": resp.text,
                    "language": "txt",
                }
        except Exception as exc:
            logger.warning("Exploit detay hatası (%s): %s", edb_id, exc)
        return {"edb_id": edb_id, "source": "", "code": "", "language": ""}

    # ------------------------------------------------------------------
    # EPSS
    # ------------------------------------------------------------------
    async def get_epss_score(self, cve_id: str) -> Optional[float]:
        """EPSS (Exploit Prediction Scoring System) skoru getir."""
        try:
            resp = await self.client.get(
                self.EPSS_API, params={"cve": cve_id}
            )
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("data", []):
                if item.get("cve") == cve_id:
                    return float(item.get("epss", 0.0))
        except Exception as exc:
            logger.debug("EPSS hatası (%s): %s", cve_id, exc)
        return None

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------
    async def generate_report(
        self, cves: List[CVEEntry], fmt: str = "markdown"
    ) -> str:
        """CVE raporu oluştur. fmt: markdown | json | html | text."""
        if fmt == "json":
            return json.dumps(
                [c.to_dict() for c in cves], indent=2, ensure_ascii=False
            )

        if fmt == "text":
            lines = ["=== CVE RAPORU ===", f"Tarih: {datetime.utcnow().isoformat()}Z"]
            for c in cves:
                lines.append("-" * 50)
                lines.append(f"ID      : {c.cve_id}")
                lines.append(f"Skor    : {c.cvss_score} ({c.severity})")
                lines.append(f"Tarih   : {c.published}")
                lines.append(f"Exploit : {'VAR' if c.exploit_available else 'YOK'}")
                lines.append(f"EPSS    : {c.epss_score or 'N/A'}")
                lines.append(f"Açıklama: {c.description[:200]}...")
                lines.append(f"Ürünler : {', '.join(c.affected_products[:5])}")
            return "\n".join(lines)

        if fmt == "html":
            rows = ""
            for c in cves:
                sev_color = {
                    "CRITICAL": "#dc3545",
                    "HIGH": "#fd7e14",
                    "MEDIUM": "#ffc107",
                    "LOW": "#198754",
                    "NONE": "#6c757d",
                }.get(c.severity, "#6c757d")
                rows += (
                    f"<tr style='border-bottom:1px solid #dee2e6'>"
                    f"<td><strong>{c.cve_id}</strong></td>"
                    f"<td><span style='color:{sev_color}'>{c.severity}</span></td>"
                    f"<td>{c.cvss_score}</td>"
                    f"<td>{c.published}</td>"
                    f"<td>{'Yes' if c.exploit_available else 'No'}</td>"
                    f"<td>{(c.description[:120] + '...') if len(c.description) > 120 else c.description}</td>"
                    f"</tr>"
                )
            return (
                "<html><head><meta charset='utf-8'>"
                "<title>CVE Raporu</title>"
                "<style>table{border-collapse:collapse;width:100%}"
                "th,td{padding:8px;text-align:left}"
                "th{background:#343a40;color:#fff}</style></head><body>"
                f"<h2>CVE Raporu — {datetime.utcnow().isoformat()[:10]}</h2>"
                f"<table><tr><th>CVE</th><th>Severity</th><th>CVSS</th>"
                f"<th>Published</th><th>Exploit</th><th>Description</th></tr>"
                f"{rows}</table></body></html>"
            )

        # default markdown
        lines = [
            "# CVE Güvenlik Raporu",
            f"**Tarih:** {datetime.utcnow().isoformat()[:19]}Z",
            f"**Toplam:** {len(cves)} kayıt",
            "",
            "| CVE | Severity | CVSS | Tarih | Exploit | Açıklama |",
            "|-----|----------|------|-------|---------|----------|",
        ]
        for c in cves:
            desc = c.description[:90] + "..." if len(c.description) > 90 else c.description
            exploit = "✅ VAR" if c.exploit_available else "❌ Yok"
            lines.append(
                f"| {c.cve_id} | {c.severity} | {c.cvss_score} | {c.published} "
                f"| {exploit} | {desc} |"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Continuous monitoring
    # ------------------------------------------------------------------
    async def monitor_continuous(
        self,
        callback: Callable[[List[CVEEntry]], Any],
        interval_hours: int = 6,
        severity_filter: Optional[str] = None,
        min_cvss: float = 0.0,
    ) -> None:
        """Sürekli izleme döngüsü."""
        interval_seconds = interval_hours * 3600
        logger.info("Sürekli izleme başladı (aralık: %s saat)", interval_hours)
        while True:
            try:
                cves = await self.get_recent_cves(
                    days=1, severity=severity_filter
                )
                # Filtrele
                filtered = [
                    c for c in cves
                    if c.cvss_score >= min_cvss and c.cve_id not in self.known_cves
                ]
                if filtered:
                    logger.info("%s yeni CVE bulundu.", len(filtered))
                    # Exploit kontrolü
                    for c in filtered:
                        c.exploit_available = await self.check_exploit_db(c.cve_id)
                        self.known_cves.add(c.cve_id)
                    self._save_known_cves()
                    try:
                        await callback(filtered)
                    except Exception as exc:
                        logger.error("Callback hatası: %s", exc)
                else:
                    logger.info("Yeni CVE yok.")
            except Exception as exc:
                logger.error("İzleme döngüsü hatası: %s", exc)
            logger.info("Sonraki kontrol: %s saniye sonra", interval_seconds)
            await asyncio.sleep(interval_seconds)

    async def close(self) -> None:
        await self.client.aclose()

    # ------------------------------------------------------------------
    # Sync convenience wrappers
    # ------------------------------------------------------------------
    def run_sync(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def get_recent_cves_sync(self, days: int = 7, severity: Optional[str] = None, limit: int = 100) -> List[CVEEntry]:
        return self.run_sync(self.get_recent_cves(days, severity, limit))

    def get_cve_details_sync(self, cve_id: str) -> Optional[CVEEntry]:
        return self.run_sync(self.get_cve_details(cve_id))

    def search_by_product_sync(self, product: str, limit: int = 40) -> List[CVEEntry]:
        return self.run_sync(self.search_by_product(product, limit))


# ------------------------------------------------------------------
# CLI / Demo
# ------------------------------------------------------------------
async def _demo():
    logging.basicConfig(level=logging.INFO)
    tracker = CVETacker()
    print("=== Son 3 günlük CVE'ler (NVD) ===")
    cves = await tracker.get_recent_cves(days=3, limit=10)
    for c in cves:
        print(c.summary())

    if cves:
        first = cves[0].cve_id
        print(f"\n=== {first} detayları ===")
        detail = await tracker.get_cve_details(first)
        if detail:
            print(detail.to_json(indent=2))

    await tracker.close()


if __name__ == "__main__":
    asyncio.run(_demo())
