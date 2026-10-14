import os
import re
import json
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from groq import Groq
from dotenv import load_dotenv

from core.config import CHAT_MAX_TOKENS, AI_TEMPERATURE, ANALYSIS_MAX_CHARS

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


def _ask_groq(prompt: str, max_tokens: int = 1000) -> str:
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=AI_TEMPERATURE,
        )
    except Exception as e:
        logger.exception("Groq analiz isteği başarısız")
        raise AIServiceError(str(e)) from e
    finally:
        # Başarısız çağrılar da maliyet/kota tüketebilir; hepsi sayılır
        scope = _ai_scope.get()
        if scope is not None:
            scope["calls"] += 1

    answer = (response.choices[0].message.content or "").strip()
    if not answer:
        logger.error("Groq analiz isteği boş cevap döndü (finish_reason=%s)",
                     response.choices[0].finish_reason)
        raise AIServiceError("Yapay zeka boş cevap döndü.")
    return answer


def _parse_json_object(raw: str, fallback: dict) -> dict:
    """Model cevabından JSON nesnesini çıkarır; olmazsa fallback döndürür.

    Model bazen ```json ... ``` bloğu içinde ya da başına açıklama ekleyerek yanıt veriyor.
    """
    text = re.sub(r"```(?:json)?", "", raw or "", flags=re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            parsed = json.loads(text[start:end + 1])
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return fallback


# --- Belge analizi ---
# Belge bir kez gezilir: her parça için TEK çağrı özet + önemli noktalar + anahtar
# kelimeleri birlikte döndürür. Sonra tek birleştirme çağrısı, sonra belge türüne
# özel tek çağrı. Çağrı sayısı: parça sayısı + 2 (tek parçalı belgede 2).

# Parça ve birleştirme cevapları JSON; gpt-oss bütçenin bir kısmını düşünmeye harcadığı
# için 1000 token'da JSON yarıda kesilebiliyor. ~5.000 girdi + 2.000 çıktı dakikalık
# 8.000 token sınırının altında kalır.
_JSON_MAX_TOKENS = 2000

_ai_scope: ContextVar = ContextVar("ai_scope", default=None)


@contextmanager
def ai_call_scope():
    """Bir analiz isteği boyunca yapay zeka çağrılarını sayar.

    Kullanım: with ai_call_scope() as scope: ... ; scope["calls"] toplam çağrı sayısı.
    """
    scope = {"calls": 0}
    token = _ai_scope.set(scope)
    try:
        yield scope
    finally:
        _ai_scope.reset(token)


def _split_text(text: str, size: int) -> list:
    """Metni en fazla `size` karakterlik parçalara böler; mümkünse paragraf/satır/kelime sınırından keser."""
    chunks = []
    while len(text) > size:
        cut = -1
        for sep in ("\n\n", "\n", " "):
            cut = text.rfind(sep, size // 2, size)
            if cut != -1:
                break
        if cut == -1:
            cut = size
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        chunks.append(text)
    return chunks


def _merge_round_robin(lists: list, limit: int) -> list:
    """Parça sonuçlarını sırayla birer birer alarak birleştirir, tekrarları eler.

    Böylece sonuç sadece ilk parçanın maddelerinden oluşmaz, her parçadan temsil edilir.
    Birleştirme çağrısı ayrıştırılamazsa yerel yedek olarak kullanılır.
    """
    merged, seen = [], set()
    for i in range(max((len(lst) for lst in lists), default=0)):
        for lst in lists:
            if i < len(lst):
                key = lst[i].casefold()
                if key not in seen:
                    seen.add(key)
                    merged.append(lst[i])
    return merged[:limit]


def _as_str_list(value) -> list:
    """Modelden gelen liste alanını temizler; liste değilse boş liste döndürür."""
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if str(v).strip()]


def _normalize_result(data: dict) -> dict:
    return {
        "ozet": str(data.get("ozet") or "").strip(),
        "onemli_noktalar": _as_str_list(data.get("onemli_noktalar")),
        "anahtar_kelimeler": _as_str_list(data.get("anahtar_kelimeler")),
    }


def _analyze_chunk(chunk: str, part: int, total: int) -> dict:
    prompt = f"""Aşağıdaki metin uzun bir belgenin {total} parçasından {part}. parçasıdır.
Bu parçayı analiz et ve SADECE şu şemada bir JSON nesnesi döndür, başka hiçbir şey yazma:
{{"ozet": "...", "onemli_noktalar": ["..."], "anahtar_kelimeler": ["..."]}}

Kurallar:
- "ozet" 8-10 cümle olsun.
- "onemli_noktalar" en fazla 5 madde olsun.
- "anahtar_kelimeler" en fazla 10 kelime veya kavram olsun.
- İsimleri, sayıları ve tarihleri koru.
- Türkçe yaz.

Metin:
{chunk}"""
    raw = _ask_groq(prompt, max_tokens=_JSON_MAX_TOKENS)
    fallback = {"ozet": raw[:1500], "onemli_noktalar": [], "anahtar_kelimeler": []}
    return _normalize_result(_parse_json_object(raw, fallback))


def _merge_locally(results: list, limit: int, top_n: int, max_chars: int = 900) -> dict:
    """Birleştirme çağrısı ayrıştırılamazsa yapay zekasız yedek birleştirme."""
    summary = " ".join(r["ozet"] for r in results if r["ozet"])
    if len(summary) > max_chars:
        summary = summary[:max_chars].rsplit(" ", 1)[0] + "…"
    return {
        "ozet": summary,
        "onemli_noktalar": _merge_round_robin([r["onemli_noktalar"] for r in results], limit),
        "anahtar_kelimeler": _merge_round_robin([r["anahtar_kelimeler"] for r in results], top_n),
    }


def _reduce_once(results: list, max_sentences: int, max_chars: int, limit: int, top_n: int) -> dict:
    payload = json.dumps(results, ensure_ascii=False)
    prompt = f"""Aşağıdaki JSON listesindeki sonuçlar tek bir belgenin parçalarından çıkarıldı.
Tekrarları birleştir ve belgenin bütününü temsil eden TEK bir sonuç üret.
SADECE şu şemada bir JSON nesnesi döndür, başka hiçbir şey yazma:
{{"ozet": "...", "onemli_noktalar": ["..."], "anahtar_kelimeler": ["..."]}}

Kurallar:
- "ozet" en fazla {max_sentences} cümle ve en fazla {max_chars} karakter olsun.
- "onemli_noktalar" en fazla {limit} madde olsun.
- "anahtar_kelimeler" en fazla {top_n} kelime veya kavram olsun.
- Türkçe yaz.

Parça sonuçları:
{payload}"""
    raw = _ask_groq(prompt, max_tokens=_JSON_MAX_TOKENS)
    parsed = _parse_json_object(raw, None)
    if parsed is None:
        logger.warning("Birleştirme cevabı JSON olarak ayrıştırılamadı; yerel birleştirmeye düşülüyor")
        return _merge_locally(results, limit, top_n, max_chars)

    result = _normalize_result(parsed)
    result["onemli_noktalar"] = result["onemli_noktalar"][:limit]
    result["anahtar_kelimeler"] = result["anahtar_kelimeler"][:top_n]
    return result


def _group_results(results: list, max_chars: int) -> list:
    """Sonuçları, her grubun JSON hâli max_chars'ı aşmayacak şekilde ardışık gruplara böler."""
    groups, current, size = [], [], 0
    for r in results:
        r_size = len(json.dumps(r, ensure_ascii=False))
        if current and size + r_size > max_chars:
            groups.append(current)
            current, size = [], 0
        current.append(r)
        size += r_size
    if current:
        groups.append(current)
    return groups


def _reduce_results(results: list, max_sentences: int, limit: int, top_n: int) -> dict:
    """Parça sonuçlarını aynı şemada tek sonuca indirger.

    Toplam metin ANALYSIS_MAX_CHARS'ı aşıyorsa gruplar ayrı ayrı birleştirilir ve
    çıkanlar tekrar birleştirilir; en fazla 3 tur, sonra sığmayan kısım kırpılır.
    """
    for round_no in range(1, 4):
        if len(json.dumps(results, ensure_ascii=False)) <= ANALYSIS_MAX_CHARS:
            break
        groups = _group_results(results, ANALYSIS_MAX_CHARS)
        logger.info("Birleştirme %d. tur: %d sonuç %d gruba bölündü", round_no, len(results), len(groups))
        # Ara turlarda özet daha uzun tutulur ki bilgi son birleştirmeden önce kaybolmasın
        results = [_reduce_once(g, 10, 1500, limit, top_n) for g in groups]
    else:
        if len(json.dumps(results, ensure_ascii=False)) > ANALYSIS_MAX_CHARS:
            logger.warning("Birleştirme 3 turda sığmadı; ilk %d karakterlik kısım kullanılıyor", ANALYSIS_MAX_CHARS)
            kept, size = [], 0
            for r in results:
                size += len(json.dumps(r, ensure_ascii=False))
                if kept and size > ANALYSIS_MAX_CHARS:
                    break
                kept.append(r)
            results = kept

    return _reduce_once(results, max_sentences, 900, limit, top_n)


def analyze_document(text: str, document_type: str) -> dict:
    """Belgeyi tek geçişte analiz eder. Herhangi bir çağrı başarısız olursa AIServiceError fırlar."""
    chunks = _split_text(text, ANALYSIS_MAX_CHARS)
    logger.info("Analiz: %d karakter, %d parça", len(text), len(chunks))

    results = [_analyze_chunk(c, i + 1, len(chunks)) for i, c in enumerate(chunks)]

    if len(results) == 1:
        # Tek parçada birleştirme çağrısı yapılmaz; parça sonucu doğrudan kullanılır
        final = results[0]
        final["onemli_noktalar"] = final["onemli_noktalar"][:5]
        final["anahtar_kelimeler"] = final["anahtar_kelimeler"][:10]
        # Tek parçalı metin zaten sınırın altında; belge türüne özel analiz ham metni görsün
        # (CV'de beceriler, ders notunda kavramlar özette kaybolmasın). Ek çağrı açmaz.
        specific_input = chunks[0]
    else:
        final = _reduce_results(results, max_sentences=5, limit=5, top_n=10)
        # Yeni özetleme turu açmadan parça özetlerinin birleşimi kullanılır
        specific_input = "\n\n".join(r["ozet"] for r in results if r["ozet"])
        if len(specific_input) > ANALYSIS_MAX_CHARS:
            # Çok uzun belgede parça özetleri de sığmıyorsa birleştirilmiş sonucu kullan
            specific_input = final["ozet"] + "\n\n" + "\n".join(f"- {p}" for p in final["onemli_noktalar"])

    if document_type == "cv":
        document_specific = analyze_cv_with_gemini(specific_input)
    elif document_type == "lecture_note":
        document_specific = analyze_lecture_with_gemini(specific_input)
    else:
        document_specific = analyze_general_with_gemini(specific_input)

    return {
        "summary": final["ozet"],
        "important_points": final["onemli_noktalar"],
        "keywords": final["anahtar_kelimeler"],
        "document_specific": document_specific,
    }


def analyze_cv_with_gemini(text: str) -> dict:
    prompt = f"""Sen bir kariyer danışmanısın. Aşağıdaki CV'yi analiz et ve JSON formatında yanıt ver.

CV metni:
{text}

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
    return _parse_json_object(result, {
        "profileSummary": result[:300],
        "strongSides": [],
        "technicalSkills": [],
        "experienceHighlights": [],
        "improvementSuggestions": [],
        "careerAdvice": ""
    })


def analyze_lecture_with_gemini(text: str) -> dict:
    prompt = f"""Sen bir eğitim asistanısın. Aşağıdaki ders notunu analiz et ve JSON formatında yanıt ver.

Ders notu:
{text}

Şu alanları içeren bir JSON objesi döndür (başka hiçbir şey yazma, sadece JSON):
{{
  "lessonSummary": "dersin genel özeti",
  "keyConcepts": ["kavram 1", "kavram 2", "kavram 3"],
  "examFocusedNotes": ["sınav notu 1", "sınav notu 2", "sınav notu 3"],
  "studySuggestions": ["çalışma önerisi 1", "çalışma önerisi 2"],
  "possibleExamQuestions": ["olası soru 1", "olası soru 2", "olası soru 3"]
}}"""

    result = _ask_groq(prompt)
    return _parse_json_object(result, {
        "lessonSummary": result[:300],
        "keyConcepts": [],
        "examFocusedNotes": [],
        "studySuggestions": [],
        "possibleExamQuestions": []
    })


def analyze_general_with_gemini(text: str) -> dict:
    prompt = f"""Aşağıdaki belgeyi analiz et ve JSON formatında yanıt ver.

Belge:
{text}

Şu alanları içeren bir JSON objesi döndür (başka hiçbir şey yazma, sadece JSON):
{{
  "generalSummary": "belgenin genel özeti",
  "mainTopics": ["ana konu 1", "ana konu 2", "ana konu 3"],
  "documentWarnings": ["uyarı veya önemli not"],
  "recommendations": ["tavsiye 1", "tavsiye 2"]
}}"""

    result = _ask_groq(prompt)
    return _parse_json_object(result, {
        "generalSummary": result[:300],
        "mainTopics": [],
        "documentWarnings": [],
        "recommendations": []
    })


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
