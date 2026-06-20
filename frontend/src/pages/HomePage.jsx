import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { documentService } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import {
  Upload, FileText, LogOut, Clock, ChevronRight, Loader2, AlertCircle,
  Trash2, Menu, X, User, History, Sun, Moon
} from "lucide-react";

const DOCTYPE_LABELS = {
  cv: { label: "CV", color: "bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300" },
  lecture_note: { label: "Ders Notu", color: "bg-purple-100 text-purple-700 dark:bg-purple-500/15 dark:text-purple-300" },
  general: { label: "Genel", color: "bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-slate-300" },
};

function formatDate(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleDateString("tr-TR", { day: "2-digit", month: "short", year: "numeric" });
}

export default function HomePage() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const fileRef = useRef();

  const [documents, setDocuments] = useState([]);
  const [docsLoading, setDocsLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);

  const handleDelete = async (e, docId) => {
    e.stopPropagation();
    if (!window.confirm("Bu belgeyi silmek istediğinize emin misiniz?")) return;
    setDeletingId(docId);
    try {
      await documentService.deleteDocument(docId);
      setDocuments(prev => prev.filter(d => d._id !== docId));
    } catch {
    } finally {
      setDeletingId(null);
    }
  };

  const fetchDocs = () => {
    setDocsLoading(true);
    documentService.getMyDocuments()
      .then((res) => setDocuments(res.data.documents || []))
      .catch(() => {})
      .finally(() => setDocsLoading(false));
  };

  useEffect(() => { fetchDocs(); }, []);

  const handleFile = async (file) => {
    if (!file) return;
    if (!file.name.match(/\.(pdf|txt)$/i)) {
      setUploadError("Sadece PDF veya TXT dosyası yükleyebilirsiniz.");
      return;
    }
    setUploadError("");
    setUploading(true);
    try {
      const res = await documentService.upload(file);
      navigate(`/document/${res.data.documentId}`);
    } catch (err) {
      setUploadError(err.response?.data?.detail || "Yükleme başarısız.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      {/* Navbar */}
      <header className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-lg border-b border-slate-200 dark:border-slate-700/50 px-4 py-3 flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-2.5">
          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg p-1.5 shadow-md shadow-indigo-500/20">
            <FileText className="text-white" size={18} />
          </div>
          <span className="font-bold text-slate-800 dark:text-white text-base">PDF Reader AI</span>
        </div>
        <button
          onClick={() => setMenuOpen(true)}
          className="text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white transition-colors p-1"
        >
          <Menu size={22} />
        </button>
      </header>

      {/* Hamburger menu overlay */}
      {menuOpen && (
        <div className="fixed inset-0 z-30 flex justify-end">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setMenuOpen(false)}
          />
          <div className="relative bg-white dark:bg-slate-800 w-72 h-full shadow-2xl flex flex-col">
            <div className="flex items-center justify-between px-4 py-4 border-b border-slate-100 dark:border-slate-700">
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Menü</span>
              <button onClick={() => setMenuOpen(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                <X size={20} />
              </button>
            </div>

            <div className="px-4 py-4 border-b border-slate-100 dark:border-slate-700">
              <div className="flex items-center gap-3">
                <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full p-2.5 shrink-0">
                  <User size={18} className="text-white" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-800 dark:text-white truncate">{user?.name || "Kullanıcı"}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{user?.email}</p>
                </div>
              </div>
            </div>

            <nav className="flex-1 px-2 py-3 space-y-1">
              <button
                onClick={() => { setMenuOpen(false); navigate("/"); }}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
              >
                <History size={18} className="text-indigo-500 dark:text-indigo-400" />
                Analiz Geçmişi
              </button>
              <button
                onClick={() => { setMenuOpen(false); navigate("/profile"); }}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
              >
                <User size={18} className="text-indigo-500 dark:text-indigo-400" />
                Profil
              </button>
              <button
                onClick={toggleTheme}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
              >
                {theme === "dark" ? <Sun size={18} className="text-amber-400" /> : <Moon size={18} className="text-indigo-500" />}
                {theme === "dark" ? "Açık Tema" : "Koyu Tema"}
              </button>
            </nav>

            <div className="px-2 py-3 border-t border-slate-100 dark:border-slate-700">
              <button
                onClick={logout}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
              >
                <LogOut size={18} />
                Çıkış Yap
              </button>
            </div>
          </div>
        </div>
      )}

      <main className="max-w-2xl mx-auto px-4 py-8 space-y-8">
        {/* Upload area */}
        <div>
          <h2 className="text-base font-semibold text-slate-700 dark:text-slate-200 mb-3">Belge Yükle</h2>
          <div
            onClick={() => !uploading && fileRef.current.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]); }}
            className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
              dragOver
                ? "border-indigo-400 bg-indigo-50 dark:bg-indigo-500/10"
                : "border-slate-300 dark:border-slate-700 hover:border-indigo-400 dark:hover:border-indigo-500 hover:bg-slate-50 dark:hover:bg-slate-800/50"
            } ${uploading ? "opacity-60 cursor-not-allowed" : ""}`}
          >
            <input ref={fileRef} type="file" accept=".pdf,.txt" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />
            {uploading ? (
              <div className="flex flex-col items-center gap-2 text-indigo-600 dark:text-indigo-400">
                <Loader2 size={32} className="animate-spin" />
                <p className="text-sm font-medium">Yükleniyor...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-3 shadow-lg shadow-indigo-500/20">
                  <Upload size={26} className="text-white" />
                </div>
                <p className="text-sm font-medium text-slate-700 dark:text-slate-200">PDF veya TXT dosyası yükle</p>
                <p className="text-xs text-slate-400 dark:text-slate-500">Sürükle bırak veya tıkla</p>
              </div>
            )}
          </div>
          {uploadError && (
            <div className="mt-2 flex items-center gap-1.5 text-red-500 dark:text-red-400 text-sm">
              <AlertCircle size={14} />{uploadError}
            </div>
          )}
        </div>

        {/* Documents list */}
        <div>
          <h2 className="text-base font-semibold text-slate-700 dark:text-slate-200 mb-3">Belgelerim</h2>
          {docsLoading ? (
            <div className="flex justify-center py-10"><Loader2 className="animate-spin text-indigo-400" size={24} /></div>
          ) : documents.length === 0 ? (
            <div className="text-center py-10 text-slate-400 dark:text-slate-500 text-sm">Henüz belge yüklemediniz.</div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => {
                const typeInfo = DOCTYPE_LABELS[doc.documentType] || DOCTYPE_LABELS.general;
                return (
                  <div
                    key={doc._id}
                    onClick={() => navigate(`/document/${doc._id}`)}
                    className="bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/50 rounded-xl px-4 py-3 flex items-center justify-between cursor-pointer hover:border-indigo-300 dark:hover:border-indigo-500/50 hover:shadow-md transition-all"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <FileText size={18} className="text-indigo-400 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-800 dark:text-slate-100 truncate">{doc.originalName}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${typeInfo.color}`}>{typeInfo.label}</span>
                          <span className="flex items-center gap-1 text-xs text-slate-400 dark:text-slate-500"><Clock size={11} />{formatDate(doc.uploadDate)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={(e) => handleDelete(e, doc._id)}
                        disabled={deletingId === doc._id}
                        className="p-1.5 text-slate-300 dark:text-slate-600 hover:text-red-400 dark:hover:text-red-400 transition-colors disabled:opacity-50"
                      >
                        {deletingId === doc._id ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                      </button>
                      <ChevronRight size={16} className="text-slate-300 dark:text-slate-600" />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
