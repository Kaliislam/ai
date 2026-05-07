"""Bug Bounty writeup (rapor) metinlerini analiz eden modul.

Teknik adimlari, payload'lari, etki (impact) analizini ve onerileri
writeup metinlerinden otomatik olarak cikarir.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlparse


@dataclass
class Payload:
    """Cikarilan payload bilgisi."""

    raw: str
    type: str          # XSS, SQLi, Command, Template, etc.
    context: str       # HTML, JS, URL, Header, etc.
    encoded: bool      # URL-encoded mi
    sanitized: bool    # WAF/filtre tarafindan temizlenmis mi
    severity_hint: str # Low / Medium / High / Critical


@dataclass
class TechniqueStep:
    """Teknik adim bilgisi."""

    order: int
    action: str        # "Keşif", "Payload gonderme", "Bypass", etc.
    description: str
    target: str        # Hedef endpoint / parametre
    payload: Optional[str]
    evidence: str      # Yanit / davranis / ekran goruntusu aciklamasi


@dataclass
class ImpactAnalysis:
    """Etki analizi sonuclari."""

    confidentiality: bool
    integrity: bool
    availability: bool
    data_exfiltration: bool
    account_takeover: bool
    privilege_escalation: bool
    lateral_movement: bool
    financial_impact: bool
    summary: str
    cvss_vector: Optional[str]


@dataclass
class WriteupAnalysis:
    """Writeup analizi sonucu."""

    title: str
    platform: str
    reporter: str
    original_url: str
    summary: str
    steps: List[TechniqueStep] = field(default_factory=list)
    payloads: List[Payload] = field(default_factory=list)
    impact: Optional[ImpactAnalysis] = None
    recommendations: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    bypasses: List[str] = field(default_factory=list)
    chain_length: int = 1
    complexity_score: float = 0.0  # 0.0 - 10.0
    language: str = "en"


class WriteupAnalyzer:
    """Bug bounty writeup metinlerini derinlemesine analiz eden sinif.

    Regex tabanli cikarim + basit NLP ile adimlari, payload'lari,
    etki analizini ve onerileri cikarir.
    """

    # Known vulnerability patterns with payload regexes
    PAYLOAD_PATTERNS = {
        "xss": [
            r"<script[^>]*>.*?</script>",
            r"javascript:\s*",
            r"on\w+\s*=\s*['\"]?[^'\"\s>]+",
            r"<img[^>]+onerror\s*=",
            r"<svg[^>]*onload\s*=",
            r"<iframe[^>]*src\s*=",
            r"<body[^>]*onload\s*=",
            r"alert\s*\(",
            r"prompt\s*\(",
            r"confirm\s*\(",
            r"document\.cookie",
            r"window\.location",
            r"eval\s*\(",
        ],
        "sqli": [
            r"['\"]\s*or\s*['\"]?1['\"]?\s*=\s*['\"]?1",
            r"union\s+select",
            r"sleep\s*\(\s*\d+",
            r"benchmark\s*\(",
            r"pg_sleep",
            r"waitfor\s+delay",
            r"information_schema",
            r"sqlmap",
            r";\s*drop\s+table",
            r"'\s*--",
            r"'\s*#",
            r"'\s*/\*",
        ],
        "command_injection": [
            r";\s*\w+\s*",
            r"\|\s*\w+\s*",
            r"`[^`]+`",
            r"\$\([^)]+\)",
            r"\$\{[^}]+\}",
            r"&&\s*\w+",
            r"\|\|\s*\w+",
            r"cat\s+/etc/passwd",
            r"nc\s+-[e]",
            r"bash\s+-i",
            r"python\s+-c",
            r"curl\s+.*\|",
        ],
        "ssrf": [
            r"http://127\.0\.0\.1",
            r"http://localhost",
            r"http://0\.0\.0\.0",
            r"http://169\.254\.169\.254",
            r"file:///etc/passwd",
            r"gopher://",
            r"dict://",
            r"ldap://",
            r"ftp://",
        ],
        "lfi": [
            r"\.\./",
            r"%2e%2e%2f",
            r"..%2f",
            r"%252e%252e%252f",
            r"/etc/passwd",
            r"/proc/self/environ",
            r"/windows/win\.ini",
            r"php://filter",
            r"php://input",
            r"data://",
        ],
        "ssti": [
            r"\{\{[^}]+\}\}",
            r"\$\{[^}]+\}",
            r"\{%[^%]+%\}",
            r"\#\{[^}]+\}",
            r"\$\{T\([^)]+\)\}",
        ],
        "xxe": [
            r"<!ENTITY[^>]+SYSTEM",
            r"<!ENTITY[^>]+PUBLIC",
            r"file:///",
            r"xee",
        ],
        "open_redirect": [
            r"//evil\.com",
            r"\\@evil\.com",
            r"//[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+",
            r"%2f%2f",
            r"\x2f\x2f",
        ],
        "nosql": [
            r"\$ne",
            r"\$gt",
            r"\$lt",
            r"\$regex",
            r"\$where",
            r"\$exists",
        ],
        "graphql_injection": [
            r"\{\s*\w+\s*\(",
            r"__typename",
            r"__schema",
            r"IntrospectionQuery",
        ],
    }

    # Step detection keywords
    STEP_KEYWORDS = [
        ("Reconnaissance", ["recon", "keşif", "discovery", "enumerate", "enumeration",
                           "fuzzing", "fuzzer", "parametre", "parameter"]),
        ("Identification", ["identif", "belirleme", "notice", "observe", "fark et",
                             "tespit", "buldum", "found"]),
        ("Payload Development", ["payload", "olusturdum", "crafted", "prepare",
                                 "gelistirdim", "encode", "double encode"]),
        ("Exploitation", ["exploit", "sending", "gönderdim", "inject", "trigger",
                           "execute", "run", "fire"]),
        ("Bypass", ["bypass", "filter", "waf", "evade", "encode", "obfuscate",
                     "sanitize", "temizleme", "atlat"]),
        ("Chaining", ["chain", "combine", "birlestir", "leverage", "use .*(together|birlikte)",
                     "multiple"]),
        ("Verification", ["verify", "confirm", "dogruladim", "test", "reproduce",
                           "tekrar", "repeat"]),
        ("Impact Demonstration", ["impact", "etki", "sensitive", "pii", "credentials",
                                   "token", "session", "cookie", "account"]),
    ]

    TOOL_PATTERNS = [
        r"burp\s+suite", r"sqlmap", r"nmap", r"ffuf", r"gobuster",
        r"dirbuster", r"dirb", r"wfuzz", r"postman", r"curl", r"wget",
        r"python", r"ruby", r"node\.?js", r"js", r"grep", r"awk", r"sed",
        r"jq", r"hydra", r"masscan", r"amass", r"sublist3r", r"waybackurls",
        r"gau", r"httpx", r"nuclei", r"dalfox", r"xsstrike", r"gf",
        r"commix", r"tplmap", r"ysoserial", r"automation",
    ]

    BYPASS_KEYWORDS = [
        "bypass", "filter bypass", "waf bypass", "blacklist bypass",
        "whitelist bypass", "input sanitization bypass", "html encode",
        "url encode", "double encode", "unicode normalize", "null byte",
        "truncation", "integer overflow", "type juggling", "json bypass",
        "cors bypass", "csp bypass", "oauth bypass", "2fa bypass",
        "mfa bypass", "rate limit bypass", "captcha bypass",
    ]

    IMPACT_KEYWORDS = {
        "confidentiality": ["sensitive", "pii", "password", "credential", "token",
                            "secret", "key", "confidential", "private", "exfiltrat",
                            "dump", "read"],
        "integrity": ["modify", "delet", "update", "insert", "tamper", "change",
                      "overwrite", "corrupt", "integrity"],
        "availability": ["dos", "denial", "crash", "hang", "freeze", "unavailable",
                         "flood", "resource", "cpu", "memory", "bandwidth"],
        "account_takeover": ["account takeover", "ato", "session hijack", "impersonate",
                             "login as", "become", "elevate", "privilege"],
        "privilege_escalation": ["privilege escalation", "vertical", "horizontal",
                                   "admin", "root", "superuser", "elevate", "promote"],
        "lateral_movement": ["lateral", "pivot", "network", "internal", "infrastructure"],
        "financial_impact": ["money", "payment", "credit card", "billing", "transaction",
                             "fraud", "wallet", "balance"],
    }

    def __init__(self):
        self._compiled_payload_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        for vuln_type, patterns in self.PAYLOAD_PATTERNS.items():
            compiled = []
            for pat in patterns:
                try:
                    compiled.append(re.compile(pat, re.IGNORECASE))
                except re.error:
                    continue
            self._compiled_payload_patterns[vuln_type] = compiled

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, text: str, title: str = "", platform: str = "",
                reporter: str = "", url: str = "") -> WriteupAnalysis:
        """Writeup metnini analiz ederek WriteupAnalysis uretir."""
        text_lower = text.lower()

        analysis = WriteupAnalysis(
            title=title,
            platform=platform,
            reporter=reporter,
            original_url=url,
            summary=self._generate_summary(text),
        )

        analysis.steps = self._extract_steps(text)
        analysis.payloads = self._extract_payloads(text)
        analysis.impact = self._analyze_impact(text)
        analysis.recommendations = self._extract_recommendations(text)
        analysis.tools_used = self._extract_tools(text)
        analysis.bypasses = self._extract_bypasses(text)
        analysis.chain_length = self._estimate_chain_length(text, analysis.steps)
        analysis.complexity_score = self._calculate_complexity(analysis)
        analysis.language = self._detect_language(text)

        return analysis

    def analyze_batch(self, texts: List[Tuple[str, str, str, str, str]]) -> List[WriteupAnalysis]:
        """Coklu writeup analizi.

        Args:
            texts: List of (text, title, platform, reporter, url) tuples.
        """
        return [self.analyze(t, title, plat, rep, url)
                for t, title, plat, rep, url in texts]

    # ------------------------------------------------------------------
    # Summary generation
    # ------------------------------------------------------------------

    def _generate_summary(self, text: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        summary_sentences = []
        keywords = ["vulnerability", "discovered", "found", "identified", "exploit",
                    "zafiyet", "buldum", "tespit", "payload", "impact", "etki"]
        for s in sentences[:20]:
            s_lower = s.lower()
            if any(kw in s_lower for kw in keywords):
                summary_sentences.append(s)
            if len(summary_sentences) >= 3:
                break
        summary = " ".join(summary_sentences)
        if len(summary) > 500:
            summary = summary[:497] + "..."
        return summary or "Ozeti cikartilamadi."

    # ------------------------------------------------------------------
    # Step extraction
    # ------------------------------------------------------------------

    def _extract_steps(self, text: str) -> List[TechniqueStep]:
        steps: List[TechniqueStep] = []
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        step_counter = 0

        for para in paragraphs:
            para_lower = para.lower()
            for action_name, keywords in self.STEP_KEYWORDS:
                if any(re.search(kw, para_lower) for kw in keywords):
                    step_counter += 1
                    # Basit payload bulma (paragraf icinde ilk payload benzeri string)
                    payload = self._find_first_payload_in_text(para)
                    steps.append(TechniqueStep(
                        order=step_counter,
                        action=action_name,
                        description=para[:200] + ("..." if len(para) > 200 else ""),
                        target=self._extract_target(para),
                        payload=payload,
                        evidence="",
                    ))
                    break

        # Eger hic adim bulunamazsa, paragraf sayisi kadar genel adim uret
        if not steps and len(paragraphs) > 1:
            for idx, para in enumerate(paragraphs[:10], 1):
                steps.append(TechniqueStep(
                    order=idx,
                    action="General",
                    description=para[:200],
                    target="",
                    payload=None,
                    evidence="",
                ))

        return steps

    def _find_first_payload_in_text(self, text: str) -> Optional[str]:
        for vuln_type, patterns in self._compiled_payload_patterns.items():
            for pat in patterns:
                m = pat.search(text)
                if m:
                    raw = m.group(0)
                    if 5 < len(raw) < 300:
                        return raw
        return None

    def _extract_target(self, text: str) -> str:
        # URL / endpoint cikarimi
        url_match = re.search(r"https?://[^\s\"<>]+|/[^\s\"<>]+", text)
        if url_match:
            return url_match.group(0)
        # Parametre cikarimi
        param_match = re.search(r"[?&](\w+)\s*=", text)
        if param_match:
            return f"?{param_match.group(1)}=..."
        return ""

    # ------------------------------------------------------------------
    # Payload extraction
    # ------------------------------------------------------------------

    def _extract_payloads(self, text: str) -> List[Payload]:
        payloads: List[Payload] = []
        seen: set = set()

        for vuln_type, patterns in self._compiled_payload_patterns.items():
            for pat in patterns:
                for m in pat.finditer(text):
                    raw = m.group(0)
                    if raw in seen:
                        continue
                    seen.add(raw)

                    context = self._detect_context(raw, text)
                    encoded = "%" in raw or "0x" in raw.lower()
                    sanitized = any(s in raw.lower() for s in ["sanitized", "cleaned", "removed", "stripped"])
                    severity_hint = self._payload_severity_hint(vuln_type, raw)

                    payloads.append(Payload(
                        raw=raw,
                        type=vuln_type.upper(),
                        context=context,
                        encoded=encoded,
                        sanitized=sanitized,
                        severity_hint=severity_hint,
                    ))

        return payloads

    def _detect_context(self, raw: str, surrounding: str) -> str:
        if any(tag in surrounding.lower() for tag in ["<script", "<img", "<svg", "<iframe"]):
            return "HTML"
        if "javascript" in surrounding.lower() or "js" in surrounding.lower():
            return "JavaScript"
        if "header" in surrounding.lower() or "user-agent" in surrounding.lower():
            return "HTTP Header"
        if "url" in surrounding.lower() or "redirect" in surrounding.lower():
            return "URL Parameter"
        if "json" in surrounding.lower():
            return "JSON"
        if "xml" in surrounding.lower():
            return "XML"
        if "cookie" in surrounding.lower():
            return "Cookie"
        return "Unknown"

    def _payload_severity_hint(self, vuln_type: str, raw: str) -> str:
        critical_types = {"rce", "sqli", "command_injection", "ssrf", "xxe"}
        high_types = {"xss", "ssti", "idor", "auth_bypass"}
        if vuln_type.lower() in critical_types:
            return "Critical"
        if vuln_type.lower() in high_types:
            return "High"
        return "Medium"

    # ------------------------------------------------------------------
    # Impact analysis
    # ------------------------------------------------------------------

    def _analyze_impact(self, text: str) -> ImpactAnalysis:
        text_lower = text.lower()

        def has_any(keywords: List[str]) -> bool:
            return any(kw in text_lower for kw in keywords)

        impact = ImpactAnalysis(
            confidentiality=has_any(self.IMPACT_KEYWORDS["confidentiality"]),
            integrity=has_any(self.IMPACT_KEYWORDS["integrity"]),
            availability=has_any(self.IMPACT_KEYWORDS["availability"]),
            data_exfiltration=has_any(["exfiltrat", "dump", "download", "export", "steal"]),
            account_takeover=has_any(self.IMPACT_KEYWORDS["account_takeover"]),
            privilege_escalation=has_any(self.IMPACT_KEYWORDS["privilege_escalation"]),
            lateral_movement=has_any(self.IMPACT_KEYWORDS["lateral_movement"]),
            financial_impact=has_any(self.IMPACT_KEYWORDS["financial_impact"]),
            summary="",
            cvss_vector=None,
        )

        impacts = []
        if impact.confidentiality:
            impacts.append("Gizlilik ihlali")
        if impact.integrity:
            impacts.append("Butunluk ihlali")
        if impact.availability:
            impacts.append("Erisilebilirlik ihlali")
        if impact.account_takeover:
            impacts.append("Hesap ele gecirme")
        if impact.privilege_escalation:
            impacts.append("Yetki yukseltme")
        if impact.data_exfiltration:
            impacts.append("Veri sizintisi")
        if impact.financial_impact:
            impacts.append("Finansal etki")

        impact.summary = "; ".join(impacts) if impacts else "Dusuk / bilgi aciklamasi seviyesinde etki."

        # CVSS vector olusturma
        vector_parts = ["CVSS:3.1"]
        vector_parts.append("AV:N")  # Network
        vector_parts.append("AC:L")  # Low
        vector_parts.append("PR:N")  # None
        vector_parts.append("UI:N")  # None
        if impact.confidentiality or impact.data_exfiltration:
            vector_parts.append("C:H")
        else:
            vector_parts.append("C:N")
        if impact.integrity or impact.privilege_escalation:
            vector_parts.append("I:H")
        else:
            vector_parts.append("I:N")
        if impact.availability:
            vector_parts.append("A:H")
        else:
            vector_parts.append("A:N")
        impact.cvss_vector = "/".join(vector_parts)

        return impact

    # ------------------------------------------------------------------
    # Recommendations extraction
    # ------------------------------------------------------------------

    def _extract_recommendations(self, text: str) -> List[str]:
        recs = []
        text_lower = text.lower()

        recommendation_map = {
            "Input validation": ["input validation", "validate", "sanitize", "filtre"],
            "Output encoding": ["encode", "escap", "html encode", "htmlspecialchars"],
            "Parameterized queries": ["parameterized", "prepared statement", "bind parameter"],
            "Content Security Policy": ["csp", "content security policy"],
            "Rate limiting": ["rate limit", "throttle", "request limit"],
            "Authentication hardening": ["2fa", "mfa", "multi.factor", "otp", "strong auth"],
            "Access control": ["access control", "authorization", "rbac", "acl"],
            "WAF rule": ["waf", "web application firewall", "virtual patch"],
            "Logging & monitoring": ["log", "monitor", "alert", "siem"],
            "Dependency update": ["update", "patch", "version", "library"],
        }

        for rec_name, keywords in recommendation_map.items():
            if any(kw in text_lower for kw in keywords):
                recs.append(rec_name)

        if not recs:
            recs.append("Genel guvenlik incelemesi ve penetration testi onerilir.")

        return list(dict.fromkeys(recs))  # preserve order, remove dups

    # ------------------------------------------------------------------
    # Tools & bypass extraction
    # ------------------------------------------------------------------

    def _extract_tools(self, text: str) -> List[str]:
        tools = []
        text_lower = text.lower()
        for pat in self.TOOL_PATTERNS:
            if re.search(pat, text_lower):
                tools.append(pat.replace("\\s+", " ").strip())
        return tools

    def _extract_bypasses(self, text: str) -> List[str]:
        found = []
        text_lower = text.lower()
        for kw in self.BYPASS_KEYWORDS:
            if kw.lower() in text_lower:
                found.append(kw)
        return found

    def _estimate_chain_length(self, text: str, steps: List[TechniqueStep]) -> int:
        chain_indicators = ["chain", "combine", "leverage", "use.*together", "multiple",
                            "step", "stage", "phase", "then", "sonra", "ardindan", "sonraki"]
        text_lower = text.lower()
        count = sum(1 for ind in chain_indicators if ind in text_lower)
        return max(1, min(5, len(steps) // 2 + count // 2))

    def _calculate_complexity(self, analysis: WriteupAnalysis) -> float:
        score = 1.0
        score += len(analysis.payloads) * 0.5
        score += len(analysis.bypasses) * 1.0
        score += analysis.chain_length * 0.8
        score += len(analysis.tools_used) * 0.3
        if analysis.impact and analysis.impact.privilege_escalation:
            score += 2.0
        if analysis.impact and analysis.impact.account_takeover:
            score += 2.5
        if analysis.impact and analysis.impact.lateral_movement:
            score += 3.0
        return min(10.0, round(score, 1))

    def _detect_language(self, text: str) -> str:
        turkish_indicators = ["ve", "icin", "ile", "bu", "bir", "degil", "rapor",
                              "zafiyet", "buldum", "tespit", "oncelikle", "ardindan"]
        text_lower = text.lower()
        tr_count = sum(1 for w in turkish_indicators if w in text_lower)
        return "tr" if tr_count >= 3 else "en"

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    def to_markdown(self, analysis: WriteupAnalysis) -> str:
        """Analizi Markdown formatinda raporlar."""
        lines = [
            f"# Writeup Analizi: {analysis.title}",
            "",
            f"**Platform**: {analysis.platform}",
            f"**Arastirmaci**: {analysis.reporter}",
            f"**Orijinal URL**: {analysis.original_url}",
            f"**Karmasiklik Puani**: {analysis.complexity_score}/10",
            f"**Zincir Uzunlugu**: {analysis.chain_length} adim",
            f"**Dil**: {analysis.language}",
            "",
            "## Ozet",
            analysis.summary,
            "",
            "## Teknik Adimlar",
        ]

        for step in analysis.steps:
            lines.append(f"### Adim {step.order}: {step.action}")
            lines.append(f"- **Aciklama**: {step.description}")
            lines.append(f"- **Hedef**: {step.target or 'Belirtilmemis'}")
            lines.append(f"- **Payload**: `{step.payload or 'Yok'}`")
            lines.append("")

        lines.append("## Cikarilan Payload'lar")
        for p in analysis.payloads:
            lines.append(f"- **Tip**: {p.type} | **Context**: {p.context} | **Severity**: {p.severity_hint}")
            lines.append(f"  ```")
            lines.append(f"  {p.raw}")
            lines.append(f"  ```")
            lines.append(f"  Encoded: {p.encoded} | Sanitized: {p.sanitized}")
            lines.append("")

        if analysis.impact:
            lines.append("## Etki Analizi")
            lines.append(f"- **Gizlilik**: {'Evet' if analysis.impact.confidentiality else 'Hayir'}")
            lines.append(f"- **Butunluk**: {'Evet' if analysis.impact.integrity else 'Hayir'}")
            lines.append(f"- **Erisilebilirlik**: {'Evet' if analysis.impact.availability else 'Hayir'}")
            lines.append(f"- **Hesap Ele Gecirme**: {'Evet' if analysis.impact.account_takeover else 'Hayir'}")
            lines.append(f"- **Yetki Yukseltme**: {'Evet' if analysis.impact.privilege_escalation else 'Hayir'}")
            lines.append(f"- **Veri Sizintisi**: {'Evet' if analysis.impact.data_exfiltration else 'Hayir'}")
            lines.append(f"- **CVSS Vector**: `{analysis.impact.cvss_vector}`")
            lines.append(f"- **Ozet**: {analysis.impact.summary}")
            lines.append("")

        lines.append("## Kullanilan Araclar")
        lines.append(", ".join(analysis.tools_used) or "Belirtilmemis")
        lines.append("")

        lines.append("## Bypass / Evasyon Teknikleri")
        lines.append(", ".join(analysis.bypasses) or "Tespit edilmedi")
        lines.append("")

        lines.append("## Guvenlik Onerileri")
        for rec in analysis.recommendations:
            lines.append(f"- {rec}")
        lines.append("")

        return "\n".join(lines)

    def to_dict(self, analysis: WriteupAnalysis) -> Dict[str, Any]:
        """Analizi dict olarak dondurur."""
        return {
            "title": analysis.title,
            "platform": analysis.platform,
            "reporter": analysis.reporter,
            "original_url": analysis.original_url,
            "summary": analysis.summary,
            "steps": [
                {"order": s.order, "action": s.action, "description": s.description,
                 "target": s.target, "payload": s.payload, "evidence": s.evidence}
                for s in analysis.steps
            ],
            "payloads": [
                {"raw": p.raw, "type": p.type, "context": p.context,
                 "encoded": p.encoded, "sanitized": p.sanitized, "severity_hint": p.severity_hint}
                for p in analysis.payloads
            ],
            "impact": {
                "confidentiality": analysis.impact.confidentiality,
                "integrity": analysis.impact.integrity,
                "availability": analysis.impact.availability,
                "data_exfiltration": analysis.impact.data_exfiltration,
                "account_takeover": analysis.impact.account_takeover,
                "privilege_escalation": analysis.impact.privilege_escalation,
                "lateral_movement": analysis.impact.lateral_movement,
                "financial_impact": analysis.impact.financial_impact,
                "summary": analysis.impact.summary,
                "cvss_vector": analysis.impact.cvss_vector,
            } if analysis.impact else None,
            "recommendations": analysis.recommendations,
            "tools_used": analysis.tools_used,
            "bypasses": analysis.bypasses,
            "chain_length": analysis.chain_length,
            "complexity_score": analysis.complexity_score,
            "language": analysis.language,
        }


# ----------------------------------------------------------------------
# Demo / CLI
# ----------------------------------------------------------------------

def _demo() -> None:
    sample_text = """
    Title: Reflected XSS on login page via redirect parameter

    I was testing the login functionality and noticed a redirect parameter
    in the URL: https://example.com/login?redirect=/dashboard

    I tried basic XSS payloads but the WAF blocked them. After some
    fuzzing with ffuf I found that double URL encoding bypasses the filter.

    Payload: %253Cscript%253Ealert(document.cookie)%253C%252Fscript%253E
    This triggered a reflected XSS in the login page context.

    Impact: I was able to steal session cookies of users clicking the link.
    This leads to account takeover.

    Recommendation: Implement strict input validation and CSP headers.
    Use output encoding with htmlspecialcharacters.
    """

    analyzer = WriteupAnalyzer()
    result = analyzer.analyze(
        text=sample_text,
        title="Reflected XSS on login page",
        platform="HackerOne",
        reporter="demo_hunter",
        url="https://hackerone.com/reports/12345",
    )

    print(analyzer.to_markdown(result))
    print("\n--- DICT OUTPUT ---\n")
    import json
    print(json.dumps(analyzer.to_dict(result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    _demo()
