import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { documentService, analysisService, notesService } from "../services/api";
import api from "../services/api";
import { ArrowLeft, Play, Loader2, AlertCircle, FileText, Tag, Shield, Star, BookOpen, MessageCircle, Send, X, Download, Eye, StickyNote, Trash2, Plus, ChevronDown, ChevronUp } from "lucide-react";
import PdfViewer from "../components/PdfViewer";
import { Capacitor } from "@capacitor/core";
import { Filesystem, Directory } from "@capacitor/filesystem";
import { Share } from "@capacitor/share";

const DOCTYPE_LABELS = {
  cv: { label: "CV", color: "bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300" },
  lecture_note: { label: "Ders Notu", color: "bg-purple-100 text-purple-700 dark:bg-purple-500/15 dark:text-purple-300" },
  general: { label: "Genel", color: "bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-slate-300" },
};

const SENSITIVE_LABELS = {
  email: "E-posta", phone: "Telefon", tckn: "TC Kimlik No", iban: "IBAN", card_number: "Kart Numarası",
};

function Section({ icon: Icon, title, children, color = "text-indigo-500" }) {
  return (
    <div className="bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/50 rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Icon size={17} className={color} />
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">{title}</h3>
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
          <ul className="space-y-1.5">{data.strongSides.map((s, i) => <li key={i} className="text-sm text-slate-600 dark:text-slate-300 flex items-start gap-2"><span className="text-amber-400 mt-0.5">•</span>{s}</li>)}</ul>
        </Section>
      )}
      {data.technicalSkills?.length > 0 && (
        <Section icon={Tag} title="Teknik Beceriler" color="text-blue-500">
          <div className="flex flex-wrap gap-1.5">{data.technicalSkills.map((s, i) => <span key={i} className="bg-blue-50 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300 text-xs px-2.5 py-1 rounded-full font-medium">{s}</span>)}</div>
        </Section>
      )}
      {data.improvementSuggestions?.length > 0 && (
        <Section icon={AlertCircle} title="Öneriler" color="text-orange-400">
          <ul className="space-y-1.5">{data.improvementSuggestions.map((s, i) => <li key={i} className="text-sm text-slate-600 dark:text-slate-300 flex items-start gap-2"><span className="text-orange-300 mt-0.5">•</span>{s}</li>)}</ul>
        </Section>
      )}
      {data.careerAdvice && (
        <Section icon={Star} title="Kariyer Tavsiyesi" color="text-green-500">
          <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">{data.careerAdvice}</p>
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
          <ul className="space-y-1.5">{data.examFocusedNotes.map((s, i) => <li key={i} className="text-sm text-slate-600 dark:text-slate-300 flex items-start gap-2"><span className="text-purple-300 mt-0.5">•</span>{s}</li>)}</ul>
        </Section>
      )}
      {data.studySuggestions?.length > 0 && (
        <Section icon={Star} title="Çalışma Önerileri" color="text-amber-500">
          <ul className="space-y-1.5">{data.studySuggestions.map((s, i) => <li key={i} className="text-sm text-slate-600 dark:text-slate-300 flex items-start gap-2"><span className="text-amber-300 mt-0.5">•</span>{s}</li>)}</ul>
        </Section>
      )}
      {data.possibleExamQuestions?.length > 0 && (
        <Section icon={BookOpen} title="Olası Sınav Soruları" color="text-red-400">
          <ul className="space-y-1.5">{data.possibleExamQuestions.map((s, i) => <li key={i} className="text-sm text-slate-600 dark:text-slate-300 flex items-start gap-2"><span className="text-red-300 mt-0.5">•</span>{s}</li>)}</ul>
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

  const [chatOpen, setChatOpen] = useState(false);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [notes, setNotes] = useState([]);
  const [noteText, setNoteText] = useState("");
  const [noteLoading, setNoteLoading] = useState(false);
  const [notesLoading, setNotesLoading] = useState(true);
  const [chatExpanded, setChatExpanded] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [question, setQuestion] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    Promise.all([
      documentService.getMyDocuments(),
      analysisService.get(id).catch(() => null),
      api.get(`/chat/${id}`).catch(() => null),
    ]).then(([docsRes, analysisRes, chatRes]) => {
      const found = docsRes.data.documents.find((d) => d._id === id);
      setDoc(found || null);
      if (analysisRes) setAnalysis(analysisRes.data.analysis);
      if (chatRes) setChatHistory(chatRes.data.chatHistory || []);
    }).finally(() => setLoading(false));

    notesService.getByDocument(id)
      .then((res) => setNotes(res.data.notes || []))
      .catch(() => {})
      .finally(() => setNotesLoading(false));
  }, [id]);

  const addNote = async () => {
    if (!noteText.trim()) return;
    setNoteLoading(true);
    try {
      const res = await notesService.create(id, noteText.trim());
      setNotes(prev => [res.data, ...prev]);
      setNoteText("");
    } catch {
    } finally {
      setNoteLoading(false);
    }
  };

  const deleteNote = async (noteId) => {
    try {
      await notesService.delete(noteId);
      setNotes(prev => prev.filter(n => n._id !== noteId));
    } catch {
    }
  };

  useEffect(() => {
    if (chatOpen) chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, chatOpen]);

  const downloadPdf = async () => {
    try {
      const res = await analysisService.exportPdf(id);
      const fileName = `${(doc?.originalName || "analiz").replace(/\.[^/.]+$/, "")}_rapor.pdf`;

      if (Capacitor.isNativePlatform()) {
        const base64 = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result.split(",")[1]);
          reader.onerror = reject;
          reader.readAsDataURL(new Blob([res.data], { type: "application/pdf" }));
        });
        const saved = await Filesystem.writeFile({
          path: fileName,
          data: base64,
          directory: Directory.Cache,
        });
        await Share.share({
          title: fileName,
          url: saved.uri,
          dialogTitle: "PDF Raporunu Paylaş",
        });
      } else {
        const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", fileName);
        document.body.appendChild(link);
        link.click();
        link.remove();
      }
    } catch {
      alert("PDF indirilemedi.");
    }
  };

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

  const sendQuestion = async () => {
    if (!question.trim() || chatLoading) return;
    const q = question.trim();
    setQuestion("");
    setChatLoading(true);
    const tempMsg = { question: q, answer: null, timestamp: new Date().toISOString() };
    setChatHistory(prev => [...prev, tempMsg]);
    try {
      const res = await api.post(`/chat/${id}`, { question: q });
      setChatHistory(prev => prev.map((m, i) => i === prev.length - 1 ? res.data : m));
    } catch {
      setChatHistory(prev => prev.map((m, i) => i === prev.length - 1 ? { ...m, answer: "Bir hata oluştu." } : m));
    } finally {
      setChatLoading(false);
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900"><Loader2 className="animate-spin text-indigo-400" size={28} /></div>;

  const typeInfo = DOCTYPE_LABELS[doc?.documentType] || DOCTYPE_LABELS.general;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      <header className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-lg border-b border-slate-200 dark:border-slate-700/50 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate("/")} className="text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors"><ArrowLeft size={20} /></button>
        <div className="flex items-center gap-2 min-w-0">
          <FileText size={18} className="text-indigo-400 shrink-0" />
          <span className="text-sm font-medium text-slate-700 dark:text-slate-200 truncate">{doc?.originalName || "Belge"}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${typeInfo.color}`}>{typeInfo.label}</span>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-4 pb-24">
        {!analysis && (
          <div className="bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/50 rounded-2xl p-5 text-center">
            <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-3 w-fit mx-auto mb-3 shadow-lg shadow-indigo-500/20">
              <FileText size={28} className="text-white" />
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-300 mb-4">Bu belge henüz analiz edilmedi.</p>
            {error && <div className="flex items-center justify-center gap-1.5 text-red-500 dark:text-red-400 text-sm mb-3"><AlertCircle size={14} />{error}</div>}
            <button onClick={runAnalysis} disabled={analyzing} className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-xl px-5 py-2.5 text-sm font-medium flex items-center gap-2 mx-auto transition-all shadow-lg shadow-indigo-500/30 disabled:opacity-60">
              {analyzing ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />}
              {analyzing ? "Analiz ediliyor..." : "Analizi Başlat"}
            </button>
          </div>
        )}

        {analysis && (
          <>
            <div className="flex flex-wrap justify-end gap-2">
              {doc?.fileType === "pdf" && (
                <button onClick={() => setViewerOpen(true)} className="flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-500/20 transition-colors">
                  <Eye size={15} />
                  PDF Görüntüle
                </button>
              )}
              <button onClick={downloadPdf} className="flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg bg-green-50 dark:bg-green-500/10 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-500/20 transition-colors">
                <Download size={15} />
                PDF İndir
              </button>
              <button onClick={runAnalysis} disabled={analyzing} className="flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-500/20 transition-colors disabled:opacity-50">
                {analyzing ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />}
                {analyzing ? "Yenileniyor..." : "Analizi Yenile"}
              </button>
            </div>
            <Section icon={FileText} title="Özet"><p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">{analysis.summary}</p></Section>
            {analysis.importantPoints?.length > 0 && (
              <Section icon={Star} title="Önemli Noktalar" color="text-amber-500">
                <ul className="space-y-2">{analysis.importantPoints.map((p, i) => <li key={i} className="text-sm text-slate-600 dark:text-slate-300 flex items-start gap-2"><span className="text-amber-400 font-bold mt-0.5 shrink-0">{i + 1}.</span>{p}</li>)}</ul>
              </Section>
            )}
            {analysis.keywords?.length > 0 && (
              <Section icon={Tag} title="Anahtar Kelimeler" color="text-green-500">
                <div className="flex flex-wrap gap-1.5">{analysis.keywords.map((kw, i) => <span key={i} className="bg-green-50 text-green-700 dark:bg-green-500/15 dark:text-green-300 text-xs px-2.5 py-1 rounded-full font-medium">{kw}</span>)}</div>
              </Section>
            )}
            <Section icon={Shield} title="Hassas Veri Tespiti" color="text-red-400">
              {analysis.sensitiveFindings?.length === 0 ? (
                <p className="text-sm text-green-600 dark:text-green-400 flex items-center gap-1.5"><Shield size={14} /> Hassas veri tespit edilmedi.</p>
              ) : (
                <div className="space-y-2">{analysis.sensitiveFindings.map((f, i) => (
                  <div key={i} className="bg-red-50 dark:bg-red-500/10 rounded-xl px-3 py-2">
                    <p className="text-xs font-semibold text-red-600 dark:text-red-400 mb-1">{SENSITIVE_LABELS[f.type] || f.type} ({f.count} adet)</p>
                    <div className="flex flex-wrap gap-1">{f.samples.map((s, j) => <span key={j} className="bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300 text-xs px-2 py-0.5 rounded-md font-mono">{s}</span>)}</div>
                  </div>
                ))}</div>
              )}
            </Section>
            {analysis.documentType === "cv" && analysis.documentSpecificAnalysis && <CVAnalysis data={analysis.documentSpecificAnalysis} />}
            {analysis.documentType === "lecture_note" && analysis.documentSpecificAnalysis && <LectureAnalysis data={analysis.documentSpecificAnalysis} />}

            <Section icon={StickyNote} title="Notlarım" color="text-amber-500">
              <div className="flex gap-2 mb-3">
                <input
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && addNote()}
                  placeholder="Bir not ekle..."
                  className="flex-1 bg-white dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-white rounded-lg px-3 py-2 text-sm placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  onClick={addNote}
                  disabled={noteLoading || !noteText.trim()}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg px-3 py-2 transition-colors disabled:opacity-50"
                >
                  {noteLoading ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
                </button>
              </div>
              {notesLoading ? (
                <div className="flex justify-center py-4"><Loader2 size={18} className="animate-spin text-slate-300 dark:text-slate-600" /></div>
              ) : notes.length === 0 ? (
                <p className="text-xs text-slate-400 dark:text-slate-500 text-center py-2">Henüz not eklenmedi.</p>
              ) : (
                <div className="space-y-2">
                  {notes.map((note) => (
                    <div key={note._id} className="flex items-start justify-between gap-2 bg-amber-50 dark:bg-amber-500/10 rounded-lg px-3 py-2">
                      <p className="text-sm text-slate-700 dark:text-slate-200 flex-1">{note.content}</p>
                      <button
                        onClick={() => deleteNote(note._id)}
                        className="text-slate-300 dark:text-slate-600 hover:text-red-400 dark:hover:text-red-400 transition-colors shrink-0"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </Section>

            {chatHistory.length > 0 && (
              <div className="bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/50 rounded-2xl p-4">
                <button
                  onClick={() => setChatExpanded(!chatExpanded)}
                  className="w-full flex items-center justify-between"
                >
                  <div className="flex items-center gap-2">
                    <MessageCircle size={17} className="text-indigo-500" />
                    <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">Sohbet Geçmişi</h3>
                    <span className="text-xs text-slate-400 dark:text-slate-500">({chatHistory.length})</span>
                  </div>
                  {chatExpanded ? <ChevronUp size={16} className="text-slate-400" /> : <ChevronDown size={16} className="text-slate-400" />}
                </button>
                {chatExpanded && (
                  <div className="space-y-3 max-h-60 overflow-y-auto mt-3">
                    {chatHistory.map((m, i) => (
                      <div key={i} className="space-y-1">
                        <div className="flex justify-end"><span className="bg-indigo-600 text-white text-sm px-3 py-2 rounded-2xl rounded-tr-sm max-w-xs">{m.question}</span></div>
                        {m.answer && <div className="flex justify-start"><span className="bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-sm px-3 py-2 rounded-2xl rounded-tl-sm max-w-xs">{m.answer}</span></div>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </main>

      {/* Chat floating button */}
      {analysis && (
        <button
          onClick={() => setChatOpen(true)}
          className="fixed bottom-6 right-6 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-full p-4 shadow-lg shadow-indigo-500/40 transition-all z-20"
        >
          <MessageCircle size={24} />
        </button>
      )}

      {/* Chat panel */}
      {chatOpen && (
        <div className="fixed inset-0 z-30 flex items-end sm:items-center justify-center sm:justify-end sm:pr-6 sm:pb-6">
          <div className="absolute inset-0 bg-black/30 sm:bg-transparent" onClick={() => setChatOpen(false)} />
          <div className="relative bg-white dark:bg-slate-800 rounded-t-2xl sm:rounded-2xl shadow-2xl w-full sm:w-96 h-[70vh] sm:h-[500px] flex flex-col border border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 dark:border-slate-700">
              <div className="flex items-center gap-2">
                <MessageCircle size={18} className="text-indigo-500" />
                <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Belgeyle Sohbet</span>
              </div>
              <button onClick={() => setChatOpen(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"><X size={18} /></button>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
              {chatHistory.length === 0 && (
                <p className="text-xs text-slate-400 dark:text-slate-500 text-center mt-8">Belge hakkında bir şeyler sor!</p>
              )}
              {chatHistory.map((m, i) => (
                <div key={i} className="space-y-1">
                  <div className="flex justify-end"><span className="bg-indigo-600 text-white text-sm px-3 py-2 rounded-2xl rounded-tr-sm max-w-xs leading-relaxed">{m.question}</span></div>
                  {m.answer ? (
                    <div className="flex justify-start"><span className="bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-sm px-3 py-2 rounded-2xl rounded-tl-sm max-w-xs leading-relaxed">{m.answer}</span></div>
                  ) : (
                    <div className="flex justify-start"><span className="bg-slate-100 dark:bg-slate-700 text-slate-400 text-sm px-3 py-2 rounded-2xl rounded-tl-sm"><Loader2 size={14} className="animate-spin" /></span></div>
                  )}
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>

            <div className="px-4 py-3 border-t border-slate-100 dark:border-slate-700">
              <div className="flex gap-2">
                <input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendQuestion()}
                  placeholder="Bir soru sor..."
                  className="flex-1 bg-white dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-white rounded-xl px-3 py-2 text-sm placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  onClick={sendQuestion}
                  disabled={chatLoading || !question.trim()}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl px-3 py-2 transition-colors disabled:opacity-50"
                >
                  <Send size={16} />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {viewerOpen && (
        <PdfViewer documentId={id} onClose={() => setViewerOpen(false)} />
      )}
    </div>
  );
}
