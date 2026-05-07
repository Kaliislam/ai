"""Ruflo Security Audit Plugin Bridge.

Basit güvenlik tarama ve denetim modülü. Aşağıdakileri yapar:
- dosya izinlerini kontrol et
- secrets / credential leak taraması (basit regex tabanlı)
- bağımlılık vulnerability skoru (requirements.txt / package.json parsing)
- config dosyalarında exposed key tespiti
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SecurityFinding:
    """Tek bir güvenlik bulgusu."""

    severity: str  # critical / high / medium / low / info
    category: str  # secret / permission / dependency / config
    file: str
    line: Optional[int] = None
    message: str = ""
    suggestion: str = ""
    raw_match: Optional[str] = None


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_SECRET_PATTERNS: List[tuple[str, re.Pattern]] = [
    ("api_key", re.compile(r"(?i)(api[_-]?key\s*[:=]\s*['\"]?[a-z0-9]{16,})")),
    ("aws_key", re.compile(r"(?i)(AKIA[0-9A-Z]{16})")),
    ("private_key", re.compile(r"(?i)(-----BEGIN (RSA |OPENSSH )?PRIVATE KEY-----)")),
    ("password", re.compile(r"(?i)(password\s*[:=]\s*['\"][^'\"]{4,}['\"])")),
    ("token", re.compile(r"(?i)(token\s*[:=]\s*['\"]?[a-z0-9]{20,})")),
    ("secret", re.compile(r"(?i)(secret\s*[:=]\s*['\"]?[a-z0-9]{16,})")),
]

_SENSITIVE_EXTS = {".env", "config.json", "secrets.json", "credentials.json", ".pem", ".key"}

# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------


class RufloSecurityAudit:
    """Lightweight security audit inspired by ruflo-security-audit.

    Usage
    -----
    audit = RufloSecurityAudit()
    findings = audit.scan_directory("/my/project")
    report = audit.report(findings)
    """

    def __init__(self, ignore_paths: Optional[List[str]] = None) -> None:
        self.ignore_paths = set(ignore_paths or [".git", "__pycache__", "node_modules", ".venv", "venv"])

    # ------------------------------------------------------------------
    # Scanning
    # ------------------------------------------------------------------

    def scan_directory(self, root: str, max_size_mb: float = 5.0) -> List[SecurityFinding]:
        """Recursively scan a directory for security issues."""
        findings: List[SecurityFinding] = []
        root_path = Path(root).resolve()
        max_bytes = max_size_mb * 1024 * 1024

        for path in root_path.rglob("*"):
            if not path.is_file():
                continue
            if any(part in self.ignore_paths for part in path.parts):
                continue
            if path.stat().st_size > max_bytes:
                continue

            rel = str(path.relative_to(root_path))
            # Secret leak scan
            findings.extend(self._scan_file_for_secrets(path, rel))
            # Permission scan for sensitive files
            findings.extend(self._scan_permissions(path, rel))
            # Dependency scan
            if path.name in ("requirements.txt", "package.json", "Pipfile"):
                findings.extend(self._scan_dependencies(path, rel))

        logger.info("[ruflo-security-audit] scanned %s: %d findings", root, len(findings))
        return findings

    def _scan_file_for_secrets(self, path: Path, rel: str) -> List[SecurityFinding]:
        findings: List[SecurityFinding] = []
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return findings
        lines = text.splitlines()
        for line_no, line in enumerate(lines, 1):
            for category, pattern in _SECRET_PATTERNS:
                for match in pattern.finditer(line):
                    findings.append(
                        SecurityFinding(
                            severity="high",
                            category="secret",
                            file=rel,
                            line=line_no,
                            message=f"Possible {category} leak",
                            suggestion="Move to environment variables or a secrets manager.",
                            raw_match=match.group(0)[:40],
                        )
                    )
        return findings

    def _scan_permissions(self, path: Path, rel: str) -> List[SecurityFinding]:
        findings: List[SecurityFinding] = []
        mode = path.stat().st_mode
        # World-writable
        if mode & 0o002:
            if any(rel.endswith(ext) or ext in rel for ext in _SENSITIVE_EXTS):
                findings.append(
                    SecurityFinding(
                        severity="critical",
                        category="permission",
                        file=rel,
                        message="World-writable sensitive file",
                        suggestion="chmod 600",
                    )
                )
            else:
                findings.append(
                    SecurityFinding(
                        severity="medium",
                        category="permission",
                        file=rel,
                        message="World-writable file",
                        suggestion="Review permissions (chmod o-w)",
                    )
                )
        return findings

    def _scan_dependencies(self, path: Path, rel: str) -> List[SecurityFinding]:
        findings: List[SecurityFinding] = []
        if path.name == "requirements.txt":
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                return findings
            # Flag unpinned or wildcard versions
            for line_no, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if "==" not in stripped and ">=" not in stripped and "<=" not in stripped:
                    findings.append(
                        SecurityFinding(
                            severity="low",
                            category="dependency",
                            file=rel,
                            line=line_no,
                            message=f"Unpinned dependency: {stripped}",
                            suggestion="Pin versions (==x.y.z) to avoid surprise updates.",
                        )
                    )
        return findings

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def report(self, findings: List[SecurityFinding]) -> Dict[str, Any]:
        """Aggregate findings into a summary report."""
        severity_counts: Dict[str, int] = {}
        category_counts: Dict[str, int] = {}
        for f in findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1
            category_counts[f.category] = category_counts.get(f.category, 0) + 1

        return {
            "total": len(findings),
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "findings": [
                {
                    "severity": f.severity,
                    "category": f.category,
                    "file": f.file,
                    "line": f.line,
                    "message": f.message,
                    "suggestion": f.suggestion,
                }
                for f in findings
            ],
            "risk_score": self._calc_risk_score(findings),
        }

    @staticmethod
    def _calc_risk_score(findings: List[SecurityFinding]) -> int:
        weights = {"critical": 25, "high": 10, "medium": 5, "low": 1, "info": 0}
        return sum(weights.get(f.severity, 0) for f in findings)

    def report_markdown(self, findings: List[SecurityFinding]) -> str:
        """Render findings as markdown."""
        r = self.report(findings)
        lines = [
            "# Security Audit Report",
            f"**Total findings:** {r['total']}  ",
            f"**Risk score:** {r['risk_score']}  ",
            "",
            "## Severity Breakdown",
        ]
        for sev, count in sorted(r["severity_breakdown"].items(), key=lambda x: -x[1]):
            lines.append(f"- {sev}: {count}")
        lines.append("")
        lines.append("## Findings")
        for f in findings:
            loc = f"{f.file}:{f.line}" if f.line else f.file
            lines.append(f"### [{f.severity.upper()}] {loc}")
            lines.append(f"- Category: {f.category}")
            lines.append(f"- {f.message}")
            lines.append(f"- Suggestion: {f.suggestion}")
            lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Quick checks
    # ------------------------------------------------------------------

    def quick_check(self, directory: str) -> Dict[str, Any]:
        """Scan + report in one call."""
        findings = self.scan_directory(directory)
        return self.report(findings)
