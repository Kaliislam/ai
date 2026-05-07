"""IOC (Indicator of Compromise) izleme modülü.

IP, domain, hash, URL gibi IOC'leri takip eder.
Kaynaklar: Abuse.ch, AlienVault OTX, VirusTotal (ücretsiz tier).
IOC'leri otomatik karantina listesine ekler.
"""

import csv
import hashlib
import ipaddress
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Set, Tuple

import httpx


class IOCType(str, Enum):
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    FILE_HASH = "file_hash"
    UNKNOWN = "unknown"


class IOCStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    WHITELISTED = "whitelisted"
    REMEDIATED = "remediated"
    PENDING = "pending"


@dataclass
class IOCRecord:
    value: str
    ioc_type: IOCType
    source: str                # abuse.ch, alienvault, virustotal, manual
    first_seen: datetime
    last_seen: datetime
    status: IOCStatus
    tags: List[str] = field(default_factory=list)
    malware_family: Optional[str] = None
    confidence: int = 50        # 0-100
    references: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "ioc_type": self.ioc_type.value,
            "source": self.source,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "status": self.status.value,
            "tags": self.tags,
            "malware_family": self.malware_family,
            "confidence": self.confidence,
            "references": self.references,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IOCRecord":
        return cls(
            value=data["value"],
            ioc_type=IOCType(data.get("ioc_type", "unknown")),
            source=data.get("source", "manual"),
            first_seen=datetime.fromisoformat(data["first_seen"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
            status=IOCStatus(data.get("status", "pending")),
            tags=data.get("tags", []),
            malware_family=data.get("malware_family"),
            confidence=data.get("confidence", 50),
            references=data.get("references", []),
            notes=data.get("notes", ""),
        )


class IOCValidator:
    """IOC değerlerini doğrulayan ve sınıflandıran yardımcı sınıf."""

    _IPV4_RE = re.compile(
        r"^(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}"
        r"(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)$"
    )
    _IPV6_RE = re.compile(
        r"^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
    )
    _DOMAIN_RE = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)"
        r"+[a-zA-Z]{2,}$"
    )
    _URL_RE = re.compile(
        r"^https?://(?:[\w-]+\.)+[\w-]+(?:[/?#][^\s]*)?$"
    )

    @classmethod
    def classify(cls, value: str) -> IOCType:
        v = value.strip()
        if cls._IPV4_RE.match(v) or cls._IPV6_RE.match(v):
            return IOCType.IP
        if cls._URL_RE.match(v):
            return IOCType.URL
        if cls._DOMAIN_RE.match(v):
            return IOCType.DOMAIN
        hlen = len(v)
        if hlen == 32:
            return IOCType.MD5
        if hlen == 40:
            return IOCType.SHA1
        if hlen == 64:
            return IOCType.SHA256
        if 32 <= hlen <= 64 and all(c in "0123456789abcdefABCDEF" for c in v):
            return IOCType.FILE_HASH
        return IOCType.UNKNOWN

    @classmethod
    def is_private_ip(cls, value: str) -> bool:
        try:
            ip = ipaddress.ip_address(value)
            return ip.is_private or ip.is_loopback or ip.is_reserved
        except ValueError:
            return False


class IOCTracker:
    """IOC kayıtlarını takip eden ana sınıf."""

    def __init__(
        self,
        db_path: str = "ioc_db.json",
        alienvault_api_key: Optional[str] = None,
        virustotal_api_key: Optional[str] = None,
        proxy: Optional[str] = None,
    ):
        self.db_path = Path(db_path)
        self.av_key = alienvault_api_key
        self.vt_key = virustotal_api_key
        self.records: Dict[str, IOCRecord] = {}
        self._load_db()

        headers = {
            "User-Agent": (
                "TurkishJarvis-IOCTracker/1.0 "
                "(https://github.com/turkishjarvis/ioc-tracker)"
            ),
        }
        proxy_map = {"all://": proxy} if proxy else None
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10, read=45, write=10, pool=10),
            headers=headers,
            proxies=proxy_map,
            follow_redirects=True,
        )

    # ------------------------------------------------------------------
    # DB Persistence
    # ------------------------------------------------------------------

    def _load_db(self) -> None:
        if self.db_path.exists():
            try:
                with self.db_path.open("r", encoding="utf-8") as fh:
                    raw = json.load(fh)
                for key, val in raw.items():
                    self.records[key] = IOCRecord.from_dict(val)
            except Exception as exc:
                print(f"[IOCTracker] DB yükleme hatası: {exc}", file=sys.stderr)

    def _save_db(self) -> None:
        try:
            with self.db_path.open("w", encoding="utf-8") as fh:
                json.dump(
                    {k: v.to_dict() for k, v in self.records.items()},
                    fh,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as exc:
            print(f"[IOCTracker] DB kaydetme hatası: {exc}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    def add(
        self,
        value: str,
        ioc_type: Optional[IOCType] = None,
        source: str = "manual",
        tags: Optional[List[str]] = None,
        malware_family: Optional[str] = None,
        confidence: int = 50,
        references: Optional[List[str]] = None,
        notes: str = "",
    ) -> IOCRecord:
        """Yeni IOC kaydı ekler veya mevcut olanı günceller."""
        val = value.strip()
        if not val:
            raise ValueError("IOC değeri boş olamaz.")
        itype = ioc_type or IOCValidator.classify(val)
        now = datetime.utcnow()
        key = hashlib.sha256(val.encode()).hexdigest()

        if key in self.records:
            rec = self.records[key]
            rec.last_seen = now
            if tags:
                rec.tags = list(set(rec.tags + tags))
            if references:
                rec.references = list(set(rec.references + references))
            if confidence > rec.confidence:
                rec.confidence = confidence
            if notes:
                rec.notes = f"{rec.notes}\n{notes}".strip()
            if malware_family and not rec.malware_family:
                rec.malware_family = malware_family
        else:
            rec = IOCRecord(
                value=val,
                ioc_type=itype,
                source=source,
                first_seen=now,
                last_seen=now,
                status=IOCStatus.ACTIVE,
                tags=tags or [],
                malware_family=malware_family,
                confidence=confidence,
                references=references or [],
                notes=notes,
            )
            self.records[key] = rec

        self._save_db()
        return rec

    def get(self, value: str) -> Optional[IOCRecord]:
        key = hashlib.sha256(value.strip().encode()).hexdigest()
        return self.records.get(key)

    def remove(self, value: str) -> bool:
        key = hashlib.sha256(value.strip().encode()).hexdigest()
        if key in self.records:
            del self.records[key]
            self._save_db()
            return True
        return False

    def update_status(self, value: str, status: IOCStatus) -> bool:
        rec = self.get(value)
        if rec:
            rec.status = status
            rec.last_seen = datetime.utcnow()
            self._save_db()
            return True
        return False

    def whitelist(self, value: str) -> bool:
        return self.update_status(value, IOCStatus.WHITELISTED)

    def quarantine(self, value: str) -> bool:
        return self.update_status(value, IOCStatus.INACTIVE)

    def remediate(self, value: str) -> bool:
        return self.update_status(value, IOCStatus.REMEDIATED)

    # ------------------------------------------------------------------
    # Bulk Operations
    # ------------------------------------------------------------------

    def bulk_add(self, values: List[str], source: str = "bulk", **kwargs: Any) -> List[IOCRecord]:
        """Toplu IOC ekleme."""
        results: List[IOCRecord] = []
        for val in values:
            try:
                results.append(self.add(val, source=source, **kwargs))
            except Exception as exc:
                print(f"[IOCTracker] Bulk ekleme hatası ({val}): {exc}", file=sys.stderr)
        self._save_db()
        return results

    def bulk_import_csv(self, filepath: str) -> int:
        """CSV dosyasından IOC import eder.

        Beklenen kolonlar: value, type(isteğe bağlı), source(isteğe bağlı), tags(isteğe bağlı)
        """
        added = 0
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {filepath}")
        with path.open("r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                val = row.get("value", "").strip()
                if not val:
                    continue
                itype = None
                if row.get("type"):
                    try:
                        itype = IOCType(row["type"])
                    except ValueError:
                        itype = IOCValidator.classify(val)
                tags = [t.strip() for t in row.get("tags", "").split(",") if t.strip()]
                self.add(
                    value=val,
                    ioc_type=itype,
                    source=row.get("source", "csv_import"),
                    tags=tags,
                    notes=row.get("notes", ""),
                )
                added += 1
        self._save_db()
        return added

    def export_csv(self, filepath: str, status_filter: Optional[IOCStatus] = None) -> int:
        """IOC kayıtlarını CSV olarak dışa aktarır."""
        recs = list(self.records.values())
        if status_filter:
            recs = [r for r in recs if r.status == status_filter]
        with open(filepath, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["value", "type", "source", "status", "first_seen",
                             "last_seen", "confidence", "tags", "malware_family", "notes"])
            for r in recs:
                writer.writerow([
                    r.value, r.ioc_type.value, r.source, r.status.value,
                    r.first_seen.isoformat(), r.last_seen.isoformat(),
                    r.confidence, "|".join(r.tags), r.malware_family or "", r.notes,
                ])
        return len(recs)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def list_all(self) -> List[IOCRecord]:
        return list(self.records.values())

    def list_by_type(self, ioc_type: IOCType) -> List[IOCRecord]:
        return [r for r in self.records.values() if r.ioc_type == ioc_type]

    def list_by_status(self, status: IOCStatus) -> List[IOCRecord]:
        return [r for r in self.records.values() if r.status == status]

    def list_active(self) -> List[IOCRecord]:
        return self.list_by_status(IOCStatus.ACTIVE)

    def search(self, keyword: str) -> List[IOCRecord]:
        kw = keyword.lower()
        return [
            r for r in self.records.values()
            if kw in r.value.lower()
            or kw in (r.malware_family or "").lower()
            or any(kw in t.lower() for t in r.tags)
            or kw in r.notes.lower()
        ]

    def stale_records(self, days: int = 30) -> List[IOCRecord]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [r for r in self.records.values() if r.last_seen < cutoff]

    # ------------------------------------------------------------------
    # Abuse.ch Feeds
    # ------------------------------------------------------------------

    async def sync_abuse_ch(self) -> Dict[str, int]:
        """Abuse.ch URLhaus ve MalwareBazaar verilerini senkronize eder."""
        stats = {"urlhaus": 0, "malware_bazaar": 0, "threatfox": 0}

        # URLhaus
        try:
            url = "https://urlhaus.abuse.ch/downloads/csv_recent/"
            resp = await self.client.get(url, timeout=30.0)
            if resp.status_code == 200:
                lines = resp.text.splitlines()
                reader = csv.DictReader(lines)
                for row in reader:
                    val = row.get("url", "").strip()
                    if not val:
                        continue
                    tags = [t.strip() for t in row.get("tags", "").split(",") if t.strip()]
                    self.add(
                        value=val,
                        ioc_type=IOCType.URL,
                        source="abuse.ch/urlhaus",
                        tags=tags,
                        references=[row.get("urlhaus_link", "")],
                    )
                    stats["urlhaus"] += 1
        except Exception as exc:
            print(f"[IOCTracker] Abuse.ch URLhaus sync hatası: {exc}", file=sys.stderr)

        # MalwareBazaar
        try:
            url = "https://bazaar.abuse.ch/export/csv/recent/"
            resp = await self.client.get(url, timeout=30.0)
            if resp.status_code == 200:
                lines = resp.text.splitlines()
                reader = csv.DictReader(lines)
                for row in reader:
                    val = row.get("sha256_hash", "").strip()
                    if not val:
                        continue
                    tags = [t.strip() for t in row.get("tags", "").split(",") if t.strip()]
                    itype = IOCType.SHA256 if len(val) == 64 else IOCType.FILE_HASH
                    self.add(
                        value=val,
                        ioc_type=itype,
                        source="abuse.ch/bazaar",
                        tags=tags,
                        malware_family=row.get("signature"),
                    )
                    stats["malware_bazaar"] += 1
        except Exception as exc:
            print(f"[IOCTracker] Abuse.ch Bazaar sync hatası: {exc}", file=sys.stderr)

        # ThreatFox
        try:
            url = "https://threatfox.abuse.ch/export/csv/recent/"
            resp = await self.client.get(url, timeout=30.0)
            if resp.status_code == 200:
                lines = resp.text.splitlines()
                reader = csv.DictReader(lines)
                for row in reader:
                    val = row.get("ioc", "").strip()
                    if not val:
                        continue
                    ioc_type_str = row.get("ioc_type", "")
                    itype = IOCType.UNKNOWN
                    if ioc_type_str == "ip:port":
                        itype = IOCType.IP
                    elif ioc_type_str == "domain":
                        itype = IOCType.DOMAIN
                    elif ioc_type_str == "url":
                        itype = IOCType.URL
                    tags = [t.strip() for t in row.get("tags", "").split(",") if t.strip()]
                    self.add(
                        value=val,
                        ioc_type=itype,
                        source="abuse.ch/threatfox",
                        tags=tags,
                        malware_family=row.get("malware"),
                    )
                    stats["threatfox"] += 1
        except Exception as exc:
            print(f"[IOCTracker] Abuse.ch ThreatFox sync hatası: {exc}", file=sys.stderr)

        self._save_db()
        return stats

    # ------------------------------------------------------------------
    # AlienVault OTX Lookup
    # ------------------------------------------------------------------

    async def lookup_alienvault(self, value: str) -> Dict[str, Any]:
        """AlienVault OTX üzerinden IOC sorgusu."""
        if not self.av_key:
            return {"error": "AlienVault API anahtarı tanımlı değil."}
        itype = IOCValidator.classify(value)
        otx_type = "IPv4" if itype == IOCType.IP else "domain" if itype == IOCType.DOMAIN else "file"
        url = f"https://otx.alienvault.com/api/v1/indicators/{otx_type}/{value}/general"
        headers = {"X-OTX-API-KEY": self.av_key}
        try:
            resp = await self.client.get(url, headers=headers, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            pulse_info = data.get("pulse_info", {})
            pulses = pulse_info.get("pulses", [])
            return {
                "value": value,
                "type": itype.value,
                "pulses_count": pulse_info.get("count", 0),
                "pulses": [
                    {
                        "name": p.get("name"),
                        "tags": p.get("tags", []),
                        "author": p.get("author", {}).get("username"),
                    }
                    for p in pulses[:10]
                ],
                "reputation": data.get("reputation", {}),
                "whois": data.get("whois", {}),
            }
        except httpx.HTTPStatusError as exc:
            return {"error": f"HTTP {exc.response.status_code}"}
        except Exception as exc:
            return {"error": str(exc)}

    # ------------------------------------------------------------------
    # VirusTotal Lookup (Free tier)
    # ------------------------------------------------------------------

    async def lookup_virustotal(self, value: str) -> Dict[str, Any]:
        """VirusTotal ücretsiz API ile IOC sorgusu."""
        if not self.vt_key:
            return {"error": "VirusTotal API anahtarı tanımlı değil."}
        itype = IOCValidator.classify(value)
        base = "https://www.virustotal.com/api/v3"
        if itype in (IOCType.IP,):
            endpoint = f"{base}/ip_addresses/{value}"
        elif itype in (IOCType.DOMAIN,):
            endpoint = f"{base}/domains/{value}"
        elif itype in (IOCType.URL,):
            # URL için ID hash'i gerekli
            url_id = hashlib.sha256(value.encode()).hexdigest()
            endpoint = f"{base}/urls/{url_id}"
        elif itype in (IOCType.MD5, IOCType.SHA1, IOCType.SHA256, IOCType.FILE_HASH):
            endpoint = f"{base}/files/{value}"
        else:
            return {"error": f"Desteklenmeyen IOC tipi: {itype.value}"}

        headers = {"x-apikey": self.vt_key}
        try:
            resp = await self.client.get(endpoint, headers=headers, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            attrs = data.get("data", {}).get("attributes", {})
            stats = attrs.get("last_analysis_stats", {})
            return {
                "value": value,
                "type": itype.value,
                "malicious": stats.get("malicious", 0),
                "suspicious": stats.get("suspicious", 0),
                "harmless": stats.get("harmless", 0),
                "undetected": stats.get("undetected", 0),
                "last_analysis_date": attrs.get("last_analysis_date"),
                "reputation": attrs.get("reputation"),
                "tags": attrs.get("tags", []),
            }
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return {"error": "IOC VirusTotal'da bulunamadı (404)."}
            return {"error": f"HTTP {exc.response.status_code}"}
        except Exception as exc:
            return {"error": str(exc)}

    # ------------------------------------------------------------------
    # Quarantine List Generation
    # ------------------------------------------------------------------

    def build_quarantine_list(self, output_path: Optional[str] = None) -> str:
        """Aktif IOC'lerden karantina listesi oluşturur.

        Format: Cisco ASA / Fortinet / pfBlockerNG / hosts uyumlu çıktı.
        """
        active = self.list_active()
        lines: List[str] = [
            "# TurkishJarvis IOC Quarantine List",
            f"# Generated: {datetime.utcnow().isoformat()} UTC",
            f"# Total IOCs: {len(active)}",
            "",
        ]
        for rec in active:
            if rec.ioc_type == IOCType.IP and not IOCValidator.is_private_ip(rec.value):
                lines.append(f"{rec.value}  # {rec.source} | {rec.malware_family or 'N/A'} | {','.join(rec.tags)}")
            elif rec.ioc_type == IOCType.DOMAIN:
                lines.append(f"0.0.0.0 {rec.value}  # {rec.source} | {rec.malware_family or 'N/A'}")
            elif rec.ioc_type == IOCType.URL:
                lines.append(f"# URL: {rec.value}  # {rec.source} | {rec.malware_family or 'N/A'}")
        text = "\n".join(lines)
        if output_path:
            Path(output_path).write_text(text, encoding="utf-8")
        return text

    def build_ioc_json_feed(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """IOC kayıtlarını JSON threat feed formatında dışa aktarır."""
        feed = {
            "feed_info": {
                "name": "TurkishJarvis-IOC-Feed",
                "generated": datetime.utcnow().isoformat(),
                "count": len(self.records),
            },
            "indicators": [r.to_dict() for r in self.records.values()],
        }
        if output_path:
            with open(output_path, "w", encoding="utf-8") as fh:
                json.dump(feed, fh, ensure_ascii=False, indent=2)
        return feed

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def summary_report(self) -> str:
        """IOC envanterinin kısa özet raporu."""
        total = len(self.records)
        active = len(self.list_active())
        inactive = len(self.list_by_status(IOCStatus.INACTIVE))
        whitelisted = len(self.list_by_status(IOCStatus.WHITELISTED))
        remediated = len(self.list_by_status(IOCStatus.REMEDIATED))
        pending = len(self.list_by_status(IOCStatus.PENDING))
        by_type: Dict[str, int] = {}
        for r in self.records.values():
            by_type[r.ioc_type.value] = by_type.get(r.ioc_type.value, 0) + 1
        lines = [
            "# IOC Envanter Raporu",
            "",
            f"- **Toplam IOC:** {total}",
            f"- **Aktif:** {active}",
            f"- **Inactive:** {inactive}",
            f"- **Whitelisted:** {whitelisted}",
            f"- **Remediated:** {remediated}",
            f"- **Pending:** {pending}",
            "",
            "## Tipe Göre Dağılım",
            "",
        ]
        for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
            lines.append(f"- **{t}:** {c}")
        lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
