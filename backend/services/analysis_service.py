import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def detect_sensitive(text: str) -> list:
    findings = []
    patterns = {
        "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "phone": r"(\+90|0)?[\s\-]?5\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}",
        "tckn": r"\b[1-9][0-9]{10}\b",
        "iban": r"\bTR\d{2}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{2}\b",
        "card_number": r"\b(?:\d{4}[\s\-]?){3}\d{4}\b",
    }
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            findings.append({
                "type": key,
                "count": len(matches),
                "samples": list(set(matches))[:3]
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
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI yanıt üretemedi: {str(e)}"


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
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=350,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI yanıt üretemedi: {str(e)}"
