import os
import re
import json
import logging
from groq import Groq
from dotenv import load_dotenv

from core.config import CHAT_MAX_TOKENS, AI_TEMPERATURE

load_dotenv()

logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


class AIServiceError(Exception):
    """Yapay zeka servisi cevap üretemediğinde fırlatılır."""


# Desenlerde yakalama grubu kullanma: re.findall grup varsa tüm eşleşme yerine
# sadece grubu döndürür. Gerekirse yakalamayan grup (?:...) kullan.
SENSITIVE_PATTERNS = {
    # Sondaki nokta alan adına dahil edilmez ("a@b.com." → "a@b.com")
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    # Rakamla bitişik değilse; aksi halde TCKN gibi uzun sayıların içinden telefon çıkıyor
    "phone": r"(?<!\d)(?:\+90|0)?[\s\-]?5\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}(?!\d)",
    "tckn": r"\b[1-9][0-9]{10}\b",
    "iban": r"\bTR\d{2}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{2}\b",
}
CARD_CANDIDATE_PATTERN = r"\b(?:\d[ -]*?){13,19}\b"


def luhn_check(number: str) -> bool:
    if not number.isdigit():
        return False

    total = 0
    for i, d in enumerate(reversed(number)):
        n = int(d)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n

    return total % 10 == 0


def _find_card_numbers(text: str, phones: list, ibans: list) -> list:
    # IBAN rakamları kart adayı olarak taranmasın
    for iban in ibans:
        text = text.replace(iban, " ")

    phone_digits = {re.sub(r"\D", "", p) for p in phones}
    cards = []

    for candidate in re.findall(CARD_CANDIDATE_PATTERN, text):
        digits = re.sub(r"\D", "", candidate)

        if not (13 <= len(digits) <= 19):
            continue
        # Telefon numarası kart sanılmasın
        if digits in phone_digits or re.fullmatch(r"(?:90)?5\d{9}", digits):
            continue
        # Öğrenci/fatura numarası gibi rastgele sayılar Luhn kontrolünden geçmez
        if not luhn_check(digits):
            continue

        cards.append(digits)

    return cards


def detect_sensitive(text: str) -> list:
    matches = {key: re.findall(pattern, text) for key, pattern in SENSITIVE_PATTERNS.items()}
    matches["card_number"] = _find_card_numbers(text, matches["phone"], matches["iban"])

    findings = []
    for key, found in matches.items():
        found = [m.strip() for m in found]
        if found:
            findings.append({
                "type": key,
                "count": len(found),
                # Görülme sırasını koruyarak tekrarları ele
                "samples": list(dict.fromkeys(found))[:3]
            })
    return findings


def detect_document_type(text: str, filename: str = "") -> str:
    combined = (text[:1000] + filename).lower()
    cv_score = 0
    lecture_score = 0

    cv_keywords = ["deneyim", "experience", "education", "egitim", "skills", "beceri",
                   "cv", "resume", "ozgecmis", "is deneyimi", "referans", "linkedin"]
    lecture_keywords = ["ders", "lecture", "hafta", "week", "sinav", "exam", "konu",
                        "ogretim", "universite", "bolum", "ders notu", "tanim", "teorem"]

    for kw in cv_keywords:
        if kw in combined:
            cv_score += 1
    for kw in lecture_keywords:
        if kw in combined:
            lecture_score += 1

    if "linkedin" in combined or "cv" in combined:
        cv_score += 2
    if "experience" in combined and "education" in combined and "skills" in combined:
        cv_score += 4
    if cv_score >= 4 and cv_score >= lecture_score:
        return "cv"
    if lecture_score >= 4 and lecture_score > cv_score:
        return "lecture_note"
    return "general"


def _ask_groq(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=AI_TEMPERATURE,
        )
    except Exception as e:
        logger.exception("Groq analiz isteği başarısız")
        raise AIServiceError(str(e)) from e

    answer = (response.choices[0].message.content or "").strip()
    if not answer:
        logger.error("Groq analiz isteği boş cevap döndü (finish_reason=%s)",
                     response.choices[0].finish_reason)
        raise AIServiceError("Yapay zeka boş cevap döndü.")
    return answer


def _parse_list(text: str) -> list:
    lines = text.strip().split("\n")
    result = []
    for line in lines:
        line = re.sub(r"^[\-\*\d\.\)]+\s*", "", line).strip()
        if line:
            result.append(line)
    return result


def simple_summary(text: str, max_sentences: int = 5, max_chars: int = 900) -> str:
    prompt = f"""Aşağıdaki metni Türkçe olarak {max_sentences} cümleyi geçmeyecek şekilde özetle. 
Özet en fazla {max_chars} karakter olsun. Sadece özeti yaz, başka bir şey ekleme.

Metin:
{text[:3000]}"""
    return _ask_groq(prompt)


def extract_keywords(text: str, top_n: int = 10) -> list:
    prompt = f"""Aşağıdaki metinden en önemli {top_n} anahtar kelimeyi veya kavramı çıkar.
Her kelimeyi ayrı satıra yaz, sadece kelime/kavramı yaz başka açıklama ekleme.

Metin:
{text[:3000]}"""
    result = _ask_groq(prompt)
    return _parse_list(result)[:top_n]


def extract_important_points(text: str, limit: int = 5) -> list:
    prompt = f"""Aşağıdaki metinden en önemli {limit} noktayı çıkar.
Her noktayı ayrı satıra yaz, madde işareti ile başlat.
Türkçe olarak yaz.

Metin:
{text[:3000]}"""
    result = _ask_groq(prompt)
    return _parse_list(result)[:limit]


def analyze_cv_with_gemini(text: str) -> dict:
    prompt = f"""Sen bir kariyer danışmanısın. Aşağıdaki CV'yi analiz et ve JSON formatında yanıt ver.

CV metni:
{text[:4000]}

Şu alanları içeren bir JSON objesi döndür (başka hiçbir şey yazma, sadece JSON):
{{
  "profileSummary": "kişi hakkında 2-3 cümlelik genel değerlendirme",
  "strongSides": ["güçlü yön 1", "güçlü yön 2", "güçlü yön 3"],
  "technicalSkills": ["beceri1", "beceri2", "beceri3"],
  "experienceHighlights": ["deneyim notu 1", "deneyim notu 2"],
  "improvementSuggestions": ["öneri 1", "öneri 2", "öneri 3"],
  "careerAdvice": "kariyer tavsiyesi paragrafı"
}}"""

    result = _ask_groq(prompt)
    try:
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass

    return {
        "profileSummary": result[:300],
        "strongSides": [],
        "technicalSkills": [],
        "experienceHighlights": [],
        "improvementSuggestions": [],
        "careerAdvice": ""
    }


def analyze_lecture_with_gemini(text: str) -> dict:
    prompt = f"""Sen bir eğitim asistanısın. Aşağıdaki ders notunu analiz et ve JSON formatında yanıt ver.

Ders notu:
{text[:4000]}

Şu alanları içeren bir JSON objesi döndür (başka hiçbir şey yazma, sadece JSON):
{{
  "lessonSummary": "dersin genel özeti",
  "keyConcepts": ["kavram 1", "kavram 2", "kavram 3"],
  "examFocusedNotes": ["sınav notu 1", "sınav notu 2", "sınav notu 3"],
  "studySuggestions": ["çalışma önerisi 1", "çalışma önerisi 2"],
  "possibleExamQuestions": ["olası soru 1", "olası soru 2", "olası soru 3"]
}}"""

    result = _ask_groq(prompt)
    try:
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass

    return {
        "lessonSummary": result[:300],
        "keyConcepts": [],
        "examFocusedNotes": [],
        "studySuggestions": [],
        "possibleExamQuestions": []
    }


def analyze_general_with_gemini(text: str) -> dict:
    prompt = f"""Aşağıdaki belgeyi analiz et ve JSON formatında yanıt ver.

Belge:
{text[:4000]}

Şu alanları içeren bir JSON objesi döndür (başka hiçbir şey yazma, sadece JSON):
{{
  "generalSummary": "belgenin genel özeti",
  "mainTopics": ["ana konu 1", "ana konu 2", "ana konu 3"],
  "documentWarnings": ["uyarı veya önemli not"],
  "recommendations": ["tavsiye 1", "tavsiye 2"]
}}"""

    result = _ask_groq(prompt)
    try:
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass

    return {
        "generalSummary": result[:300],
        "mainTopics": [],
        "documentWarnings": [],
        "recommendations": []
    }


def _ask_groq_chat(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=CHAT_MAX_TOKENS,
            temperature=AI_TEMPERATURE,
        )
    except Exception as e:
        logger.exception("Groq sohbet isteği başarısız")
        raise AIServiceError(str(e)) from e

    choice = response.choices[0]
    answer = (choice.message.content or "").strip()

    # Token sınırına takıldıysa cevap yarım kalmıştır; kullanıcıya belirt
    if choice.finish_reason == "length":
        note = "(Cevap uzunluk sınırına takıldığı için kesildi. Soruyu daraltarak tekrar sorabilirsiniz.)"
        answer = f"{answer}…\n\n{note}" if answer else note

    if not answer:
        logger.error("Groq sohbet isteği boş cevap döndü (finish_reason=%s)", choice.finish_reason)
        raise AIServiceError("Yapay zeka boş cevap döndü.")

    return answer
