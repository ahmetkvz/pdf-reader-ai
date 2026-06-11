import re
from collections import Counter


COURSE_METADATA_TERMS = [
    "ders günü", "ders gunu",
    "dersin kredisi",
    "akts",
    "gbs linki",
    "ders bilgileri",
    "öğretim üyesi",
    "ogretim uyesi",
    "dersin öğretim",
    "dersin ogretim",
    "görüşme gün",
    "gorusme gun",
    "görüşme saati",
    "gorusme saati",
    "blok",
    "nolu oda",
    "dersin haftası",
    "dersin haftasi",
    "dersin adı",
    "dersin adi",
    "dersin öğretim üyesi",
    "dersin ogretim uyesi",
    "dersin öğretim üyesininkonumu",
    "dersin ogretim uyesininkonumu",
]


def normalize_text(text: str) -> str:
    """
    PDF/TXT içinden gelen metni genel şekilde normalize eder.
    Amaç: boşlukları, satır tekrarlarını ve gereksiz karakter yoğunluğunu azaltmak.
    """
    if not text:
        return ""

    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_probably_noise_line(line: str) -> bool:
    """
    Belgeye özel isimlere bağlı kalmadan genel gürültü satırlarını tespit eder.
    Örneğin:
    - sadece sayfa numarası
    - URL
    - e-posta
    - telefon
    - çok kısa anlamsız satır
    - ders bilgisi / kredi / oda / saat gibi metadata satırları
    """
    if not line:
        return True

    cleaned = line.strip()
    lower = cleaned.lower()

    if len(cleaned) <= 2:
        return True

    if re.fullmatch(r"\d+", cleaned):
        return True

    if re.fullmatch(r"page\s*\d+", lower):
        return True

    if re.fullmatch(r"sayfa\s*\d+", lower):
        return True

    if "http://" in lower or "https://" in lower or "www." in lower:
        return True

    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", cleaned):
        return True

    if re.search(r"(?:\+90|0)?5\d{9}", cleaned):
        return True

    # Çok fazla sembolden oluşan satırlar
    alpha_count = len(re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]", cleaned))
    if len(cleaned) >= 5 and alpha_count / max(len(cleaned), 1) < 0.35:
        return True

    # Ders bilgi sayfalarında sık görülen metadata satırları
    metadata_hit_count = 0
    for term in COURSE_METADATA_TERMS:
        if term in lower:
            metadata_hit_count += 1

    if metadata_hit_count >= 2:
        return True

    # Slayt/PDF footer-header tarzı genel etiketler
    generic_noise_terms = [
        "copyright",
        "all rights reserved",
        "confidential",
        "slide",
        "presentation",
        "department",
        "faculty",
        "web:",
        "mail:",
        "email:",
        "phone:",
        "tel:",
    ]

    for term in generic_noise_terms:
        if term in lower and len(cleaned) < 100:
            return True

    return False


def clean_extracted_text(text: str) -> str:
    """
    PDF'ten çıkarılan ham metni daha analiz edilebilir hale getirir.
    Burada belirli bir PDF'e özel kelime temizliği değil,
    genel tekrar/gürültü temizliği yapılır.
    """
    text = normalize_text(text)

    if not text:
        return ""

    raw_lines = [ln.strip() for ln in text.split("\n")]
    raw_lines = [re.sub(r"\s+", " ", ln).strip() for ln in raw_lines if ln.strip()]

    if not raw_lines:
        return ""

    line_counts = Counter(raw_lines)
    cleaned_lines = []

    for line in raw_lines:
        # Çok tekrar eden kısa satırlar genelde header/footer olur.
        if line_counts[line] >= 3 and len(line) < 80:
            continue

        if is_probably_noise_line(line):
            continue

        # Çok kısa satırlar çoğu zaman tek başına anlamlı değildir.
        if len(line) < 8:
            continue

        cleaned_lines.append(line)

    cleaned_text = "\n".join(cleaned_lines)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    cleaned_text = re.sub(r"[ \t]+", " ", cleaned_text)
    return cleaned_text.strip()


def sentence_split(text: str) -> list[str]:
    if not text or not text.strip():
        return []

    text = clean_extracted_text(text)

    flat = re.sub(r"[ \t]+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", flat)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) < 3:
        line_parts = [ln.strip() for ln in text.split("\n") if ln.strip()]
        merged = []

        for ln in line_parts:
            ln = re.sub(r"\s+", " ", ln).strip()
            if len(ln) >= 20:
                merged.append(ln)

        if merged:
            parts = merged

    return parts


def score_summary_line(line: str) -> int:
    score = 0
    lower = line.lower()

    if len(line) >= 40:
        score += 2

    if len(line) >= 80:
        score += 2

    content_keywords = [
        # CV / yazılım
        "software", "engineer", "engineering", "student", "intern",
        "experience", "education", "summary", "skills", "project",
        "react", "node", "python", ".net", "java", "university",
        "developer", "database", "api", "mongodb", "fastapi",
        "artificial intelligence", "llm", "rag",

        # Ders notu / akademik
        "tanım", "tanımlanır", "kavram", "örnek", "formül",
        "istatistik", "aritmetik", "ortalama", "frekans", "seri",
        "örneklem", "ana kütle", "anakütle", "parametre", "değişken",
        "varyans", "standart sapma", "mod", "medyan", "dağılım",
        "hipotez", "analiz", "sonuç", "veri", "yöntem",
        "tahminleme", "güven aralığı", "güven düzeyi", "nokta tahmin",
        "rassal", "örnekleme dağılımı"
    ]

    for kw in content_keywords:
        if kw in lower:
            score += 2

    # Soru-cevap formatlı ders notları için faydalı olabilir
    if "soru:" in lower:
        score += 2

    if "cevap:" in lower:
        score += 2

    digit_count = sum(ch.isdigit() for ch in line)

    # Çok fazla rakam varsa bazen iletişim/tarih/gereksiz tablo olabilir.
    if digit_count >= 12:
        score -= 2

    if "@" in line:
        score -= 3

    if "linkedin.com" in lower or "github.com" in lower:
        score -= 2

    if "http://" in lower or "https://" in lower or "www." in lower:
        score -= 3

    # Ders bilgi/kredi/oda/saat gibi metadata içeren satırları özet seçiminde geriye at.
    for term in COURSE_METADATA_TERMS:
        if term in lower:
            score -= 5

    return score


def simple_summary(text: str, max_sentences: int = 5, max_chars: int = 900) -> str:
    if not text or not text.strip():
        return "Belgeden metin çıkarılamadı."

    cleaned_text = clean_extracted_text(text)
    parts = sentence_split(cleaned_text)

    if not parts:
        cleaned = re.sub(r"\s+", " ", cleaned_text).strip()
        return cleaned[:max_chars] + ("..." if len(cleaned) > max_chars else "")

    ranked = sorted(
        ((score_summary_line(p), idx, p) for idx, p in enumerate(parts)),
        key=lambda x: (-x[0], x[1])
    )

    selected = []
    used = set()

    for _, _, part in ranked:
        normalized = re.sub(r"\s+", " ", part).strip()
        lower = normalized.lower()

        if normalized in used:
            continue

        if len(normalized) < 25:
            continue

        if normalized.count("@") >= 1 and len(normalized) < 120:
            continue

        if "http://" in lower or "https://" in lower or "www." in lower:
            continue

        if is_probably_noise_line(normalized):
            continue

        used.add(normalized)
        selected.append(normalized)

        if len(selected) >= max_sentences:
            break

    if not selected:
        cleaned = re.sub(r"\s+", " ", cleaned_text).strip()
        return cleaned[:max_chars] + ("..." if len(cleaned) > max_chars else "")

    summary = " ".join(selected)
    summary = re.sub(r"\s+", " ", summary).strip()

    if len(summary) > max_chars:
        summary = summary[:max_chars].rstrip() + "..."

    return summary


def luhn_check(number: str) -> bool:
    if not number.isdigit():
        return False

    total = 0
    reverse_digits = number[::-1]

    for i, d in enumerate(reverse_digits):
        n = int(d)

        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9

        total += n

    return total % 10 == 0


def detect_sensitive(text: str):
    findings = []

    if not text:
        return findings

    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    if emails:
        uniq = sorted(set(emails))
        findings.append({
            "type": "email",
            "count": len(uniq),
            "samples": uniq[:5]
        })

    phones = re.findall(r"(?:\+90|0)?5\d{9}", text)
    if phones:
        uniq = sorted(set(phones))
        findings.append({
            "type": "phone",
            "count": len(uniq),
            "samples": uniq[:5]
        })

    tckn = re.findall(r"\b[1-9]\d{10}\b", text)
    if tckn:
        uniq = sorted(set(tckn))
        findings.append({
            "type": "tckn",
            "count": len(uniq),
            "samples": uniq[:5]
        })

    ibans = re.findall(r"\bTR\d{24}\b", text, flags=re.IGNORECASE)
    if ibans:
        uniq = sorted(set(i.upper() for i in ibans))
        findings.append({
            "type": "iban",
            "count": len(uniq),
            "samples": uniq[:5]
        })

    raw_cards = re.findall(r"\b(?:\d[ -]*?){13,19}\b", text)
    cleaned_cards = []

    phone_set = set(re.sub(r"\D", "", p) for p in phones) if phones else set()

    for candidate in raw_cards:
        digits = re.sub(r"\D", "", candidate)

        if not (13 <= len(digits) <= 19):
            continue

        if digits in phone_set:
            continue

        if re.fullmatch(r"(?:90)?5\d{9}", digits):
            continue

        if not luhn_check(digits):
            continue

        cleaned_cards.append(digits)

    if cleaned_cards:
        uniq = sorted(set(cleaned_cards))
        findings.append({
            "type": "card_number",
            "count": len(uniq),
            "samples": uniq[:5]
        })

    return findings


def extract_keywords(text: str, top_n: int = 10):
    if not text:
        return []

    cleaned_text = clean_extracted_text(text)
    words = re.findall(r"\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{4,}\b", cleaned_text.lower())

    stopwords = {
        # Türkçe genel kelimeler
        "ve", "ile", "için", "gibi", "olan", "olarak", "ama", "fakat",
        "çünkü", "daha", "çok", "bir", "biri", "bunu", "şunu", "şöyle",
        "böyle", "olur", "olmak", "olduğu", "olduğunu", "edilir",
        "ifade", "göre", "sonra", "önce", "ancak", "veya", "yada", "yani",
        "ise", "değil", "kadar", "tarafından", "verilir", "adı", "adi",
        "temel", "bazı", "ayrı", "şeklinde", "sekilde", "hakkında",
        "hakkinda", "üzerinden", "arasında", "arasinda", "kullanılan",
        "kullanilan", "bulunan", "edilen", "yapılan", "yapilan",

        # İngilizce genel kelimeler
        "the", "and", "for", "this", "that", "from", "have", "with",
        "your", "you", "are", "was", "were", "been", "will", "can",
        "could", "should", "about", "into", "their", "there", "which",
        "using", "used", "based", "also", "such", "more", "most",

        # Ders/slayt/PDF genel tekrar kelimeleri
        "ders", "dersin", "notu", "hafta", "haftası", "haftasi",
        "bölüm", "bolum", "sayfa", "page", "slide", "presentation",
        "faculty", "department", "university", "telefon", "phone",
        "email", "posta", "web", "website", "link", "copyright",
        "confidential", "rights", "reserved",

        # Soru yönergesi tarzı kelimeler
        "aşağıdaki", "asagidaki", "yukarıdaki", "yukaridaki",
        "verilen", "bulunuz", "hesaplayınız", "hesaplayiniz",
        "tanımlayınız", "tanimlayiniz", "açıklayınız", "aciklayiniz",
        "yazınız", "yaziniz", "belirtiniz", "gösteriniz", "gosteriniz",

        # Tek başına çok genel kalan akademik kelimeler
        "bilgileri", "konumu", "günü", "gunu", "saati", "kredi",
        "akts", "görüşme", "gorusme", "amacıyla", "amaciyla"
    }

    freq = {}

    for word in words:
        word = word.strip().lower()

        if word in stopwords:
            continue

        if len(word) < 4:
            continue

        if word.isdigit():
            continue

        if word.startswith("http"):
            continue

        # Çok tekrar eden kurumsal/site etiketlerini genel olarak azaltır.
        if "edu" in word and len(word) > 8:
            continue

        if "www" in word:
            continue

        freq[word] = freq.get(word, 0) + 1

    ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in ranked[:top_n]]


def extract_important_points(text: str, limit: int = 5):
    if not text:
        return []

    cleaned_text = clean_extracted_text(text)
    parts = sentence_split(cleaned_text)

    if not parts:
        return []

    ranked = sorted(
        ((score_summary_line(p), idx, p) for idx, p in enumerate(parts)),
        key=lambda x: (-x[0], x[1])
    )

    results = []
    seen = set()

    for _, _, part in ranked:
        normalized = re.sub(r"\s+", " ", part).strip()
        lower = normalized.lower()

        if len(normalized) < 25:
            continue

        if normalized in seen:
            continue

        if is_probably_noise_line(normalized):
            continue

        if "http://" in lower or "https://" in lower or "www." in lower:
            continue

        if normalized.count("@") >= 1 and len(normalized) < 120:
            continue

        seen.add(normalized)
        results.append(normalized)

        if len(results) >= limit:
            break

    return results


def detect_document_type(text: str, filename: str = "") -> str:
    """
    Belge türünü ilk aşamada kural tabanlı tespit eder.
    Şimdilik desteklenen türler:
    - cv
    - lecture_note
    - general

    Bu fonksiyon hâlâ kural tabanlıdır.
    İleride LLM entegrasyonu geldiğinde AI destekli sınıflandırma eklenebilir.
    """
    cleaned_text = clean_extracted_text(text)
    combined = f"{filename}\n{cleaned_text}".lower()
    combined = re.sub(r"\s+", " ", combined)

    cv_keywords = [
        "cv",
        "resume",
        "curriculum vitae",
        "professional summary",
        "summary",
        "experience",
        "work experience",
        "education",
        "skills",
        "technical skills",
        "projects",
        "linkedin",
        "github",
        "software engineering student",
        "software engineer",
        "developer",
        "intern",
        "internship",
        "languages",
        "certificates",
        "certifications",
        "career",
        "profile"
    ]

    lecture_keywords = [
        "ders",
        "ders notu",
        "lecture",
        "lecture note",
        "chapter",
        "unit",
        "ünite",
        "konu",
        "hafta",
        "course",
        "soru",
        "cevap",
        "tanım",
        "örnek",
        "açıklayınız",
        "madde",
        "öğrenme",
        "algoritma",
        "veri",
        "not",
        "final",
        "vize",
        "istatistik",
        "aritmetik ortalama",
        "frekans",
        "örneklem",
        "ana kütle",
        "parametre",
        "değişken",
        "formül",
        "problem",
        "çözüm"
    ]

    cv_score = 0
    lecture_score = 0

    for kw in cv_keywords:
        if kw in combined:
            cv_score += 1

    for kw in lecture_keywords:
        if kw in combined:
            lecture_score += 1

    filename_lower = filename.lower()

    if "cv" in filename_lower or "resume" in filename_lower:
        cv_score += 5

    if "ders" in filename_lower or "not" in filename_lower or "lecture" in filename_lower:
        lecture_score += 4

    if "soru" in combined and "cevap" in combined:
        lecture_score += 4

    if "dersin haftası" in combined or "dersin haftasi" in combined:
        lecture_score += 3

    if "technical skills" in combined:
        cv_score += 3

    if "professional summary" in combined:
        cv_score += 3

    if "linkedin" in combined:
        cv_score += 2

    if "experience" in combined and "education" in combined and "skills" in combined:
        cv_score += 4

    print("DOCUMENT TYPE DEBUG")
    print("Filename:", filename)
    print("CV score:", cv_score)
    print("Lecture score:", lecture_score)

    if cv_score >= 4 and cv_score >= lecture_score:
        return "cv"

    if lecture_score >= 4 and lecture_score > cv_score:
        return "lecture_note"

    return "general"