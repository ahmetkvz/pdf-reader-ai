import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { documentService, analysisService } from "../services/api";
import { ArrowLeft, Play, Loader2, AlertCircle, FileText, Tag, Shield, Star, BookOpen, User, FileSearch } from "lucide-react";

const DOCTYPE_LABELS = {
  cv: { label: "CV", color: "bg-blue-100 text-blue-700" },
  lecture_note: { label: "Ders Notu", color: "bg-purple-100 text-purple-700" },
  general: { label: "Genel", color: "bg-gray-100 text-gray-600" },
};

const SENSITIVE_LABELS = {
  email: "E-posta", phone: "Telefon", tckn: "TC Kimlik No", iban: "IBAN", card_number: "Kart Numarası",
};

function Section({ icon: Icon, title, children, color = "text-indigo-500" }) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Icon size={17} className={color} />
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function CVAnalysis({ data }) {
  return (
    <div className="space-y-3">
      {data.strongSides?.length > 0 && (
        <Section icon={Star} title="Güçlü Yönler" color="text-amber-500">
          <ul className="space-y-1.5">{data.strongSides.map((s, i) => <li key={i} className="text-sm text-gray-600 flex items-start gap-2"><span className="text-amber-400 mt-0.5">•</span>{s}</li>)}</ul>
        </Section>
      )}
      {data.technicalSkills?.length > 0 && (
        <Section icon={Tag} title="Teknik Beceriler" color="text-blue-500">
          <div className="flex flex-wrap gap-1.5">{data.technicalSkills.map((s, i) => <span key={i} className="bg-blue-50 text-blue-700 text-xs px-2.5 py-1 rounded-full font-medium">{s}</span>)}</div>
        </Section>
      )}
      {data.improvementSuggestions?.length > 0 && (
        <Section icon={AlertCircle} title="Öneriler" color="text-orange-400">
          <ul className="space-y-1.5">{data.improvementSuggestions.map((s, i) => <li key={i} className="text-sm text-gray-600 flex items-start gap-2"><span className="text-orange-300 mt-0.5">•</span>{s}</li>)}</ul>
        </Section>
      )}
    </div>
  );
}

function LectureAnalysis({ data }) {
  return (
    <div className="space-y-3">
      {data.examFocusedNotes?.length > 0 && (
        <Section icon={BookOpen} title="Sınav Notları" color="text-purple-500">
          <ul className="space-y-1.5">{data.examFocusedNotes.map((s, i) => <li key={i} className="text-sm text-gray-600 flex items-start gap-2"><span className="text-purple-300 mt-0.5">•</span>{s}</li>)}</ul>
        </Section>
      )}
      {data.studySuggestions?.length > 0 && (
        <Section icon={Star} title="Çalışma Önerileri" color="text-amber-500">
          <ul className="space-y-1.5">{data.studySuggestions.map((s, i) => <li key={i} className="text-sm text-gray-600 flex items-start gap-2"><span className="text-amber-300 mt-0.5">•</span>{s}</li>)}</ul>
        </Section>
      )}
    </div>
  );
}

export default function DocumentPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [doc, setDoc] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      documentService.getMyDocuments(),
      analysisService.get(id).catch(() => null),
    ]).then(([docsRes, analysisRes]) => {
      const found = docsRes.data.documents.find((d) => d._id === id);
      setDoc(found || null);
      if (analysisRes) setAnalysis(analysisRes.data.analysis);
    }).finally(() => setLoading(false));
  }, [id]);

  const runAnalysis = async () => {
    setAnalyzing(true);
    setError("");
    try {
      const res = await analysisService.run(id);
      setAnalysis(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Analiz başarısız.");
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center"><Loader2 className="animate-spin text-indigo-400" size={28} /></div>;

  const typeInfo = DOCTYPE_LABELS[doc?.documentType] || DOCTYPE_LABELS.general;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate("/")} className="text-gray-400 hover:text-gray-700 transition-colors"><ArrowLeft size={20} /></button>
        <div className="flex items-center gap-2 min-w-0">
          <FileText size={18} className="text-indigo-400 shrink-0" />
          <span className="text-sm font-medium text-gray-700 truncate">{doc?.originalName || "Belge"}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${typeInfo.color}`}>{typeInfo.label}</span>
        </div>
      </header>
      <main className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {!analysis && (
          <div className="bg-white border border-gray-200 rounded-2xl p-5 text-center">
            <FileSearch size={36} className="text-indigo-300 mx-auto mb-3" />
            <p className="text-sm text-gray-600 mb-4">Bu belge henüz analiz edilmedi.</p>
            {error && <div className="flex items-center justify-center gap-1.5 text-red-500 text-sm mb-3"><AlertCircle size={14} />{error}</div>}
            <button onClick={runAnalysis} disabled={analyzing} className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl px-5 py-2.5 text-sm font-medium flex items-center gap-2 mx-auto transition-colors disabled:opacity-60">
              {analyzing ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />}
              {analyzing ? "Analiz ediliyor..." : "Analizi Başlat"}
            </button>
          </div>
        )}
        {analysis && (
          <>
            <div className="flex justify-end">
              <button onClick={runAnalysis} disabled={analyzing} className="flex items-center gap-1.5 text-xs text-indigo-500 hover:text-indigo-700 disabled:opacity-50">
                {analyzing ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
                {analyzing ? "Yenileniyor..." : "Analizi Yenile"}
              </button>
            </div>
            <Section icon={FileText} title="Özet"><p className="text-sm text-gray-600 leading-relaxed">{analysis.summary}</p></Section>
            {analysis.importantPoints?.length > 0 && (
              <Section icon={Star} title="Önemli Noktalar" color="text-amber-500">
                <ul className="space-y-2">{analysis.importantPoints.map((p, i) => <li key={i} className="text-sm text-gray-600 flex items-start gap-2"><span className="text-amber-400 font-bold mt-0.5 shrink-0">{i + 1}.</span>{p}</li>)}</ul>
              </Section>
            )}
            {analysis.keywords?.length > 0 && (
              <Section icon={Tag} title="Anahtar Kelimeler" color="text-green-500">
                <div className="flex flex-wrap gap-1.5">{analysis.keywords.map((kw, i) => <span key={i} className="bg-green-50 text-green-700 text-xs px-2.5 py-1 rounded-full font-medium">{kw}</span>)}</div>
              </Section>
            )}
            <Section icon={Shield} title="Hassas Veri Tespiti" color="text-red-400">
              {analysis.sensitiveFindings?.length === 0 ? (
                <p className="text-sm text-green-600 flex items-center gap-1.5"><Shield size={14} /> Hassas veri tespit edilmedi.</p>
              ) : (
                <div className="space-y-2">{analysis.sensitiveFindings.map((f, i) => (
                  <div key={i} className="bg-red-50 rounded-xl px-3 py-2">
                    <p className="text-xs font-semibold text-red-600 mb-1">{SENSITIVE_LABELS[f.type] || f.type} ({f.count} adet)</p>
                    <div className="flex flex-wrap gap-1">{f.samples.map((s, j) => <span key={j} className="bg-red-100 text-red-700 text-xs px-2 py-0.5 rounded-md font-mono">{s}</span>)}</div>
                  </div>
                ))}</div>
              )}
            </Section>
            {analysis.documentType === "cv" && analysis.documentSpecificAnalysis && <CVAnalysis data={analysis.documentSpecificAnalysis} />}
            {analysis.documentType === "lecture_note" && analysis.documentSpecificAnalysis && <LectureAnalysis data={analysis.documentSpecificAnalysis} />}
          </>
        )}
      </main>
    </div>
  );
}
