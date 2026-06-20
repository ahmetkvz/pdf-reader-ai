import { useState, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import api from "../services/api";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Loader2, X } from "lucide-react";

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export default function PdfViewer({ documentId, onClose }) {
  const [fileBlob, setFileBlob] = useState(null);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");

    api.get(`/documents/${documentId}/file`, { responseType: "blob" })
      .then((res) => {
        if (!active) return;
        const url = URL.createObjectURL(res.data);
        setFileBlob(url);
      })
      .catch(() => {
        if (active) setError("PDF yüklenemedi.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, [documentId]);

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setPageNumber(1);
  };

  return (
    <div className="fixed inset-0 z-40 bg-black/60 flex items-center justify-center p-2 sm:p-6">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-3xl h-full sm:h-[90vh] flex flex-col overflow-hidden border border-slate-200 dark:border-slate-700">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 dark:border-slate-700 shrink-0">
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">PDF Görüntüleyici</span>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
            <X size={20} />
          </button>
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-slate-100 dark:border-slate-700 shrink-0">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPageNumber(p => Math.max(1, p - 1))}
              disabled={pageNumber <= 1}
              className="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-30"
            >
              <ChevronLeft size={18} />
            </button>
            <span className="text-xs text-slate-600 dark:text-slate-300 min-w-[70px] text-center">
              {numPages ? `${pageNumber} / ${numPages}` : "—"}
            </span>
            <button
              onClick={() => setPageNumber(p => Math.min(numPages || 1, p + 1))}
              disabled={!numPages || pageNumber >= numPages}
              className="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-30"
            >
              <ChevronRight size={18} />
            </button>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setScale(s => Math.max(0.5, s - 0.2))}
              className="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
            >
              <ZoomOut size={16} />
            </button>
            <span className="text-xs text-slate-500 dark:text-slate-400 w-10 text-center">{Math.round(scale * 100)}%</span>
            <button
              onClick={() => setScale(s => Math.min(2.5, s + 0.2))}
              className="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
            >
              <ZoomIn size={16} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto bg-slate-100 dark:bg-slate-900 flex items-start justify-center p-4">
          {loading && (
            <div className="flex flex-col items-center gap-2 text-slate-400 mt-10">
              <Loader2 size={28} className="animate-spin" />
              <p className="text-xs">PDF yükleniyor...</p>
            </div>
          )}
          {error && (
            <div className="text-center mt-10">
              <p className="text-sm text-red-500 dark:text-red-400">{error}</p>
            </div>
          )}
          {fileBlob && !error && (
            <Document
              file={fileBlob}
              onLoadSuccess={onDocumentLoadSuccess}
              loading={<Loader2 size={28} className="animate-spin text-slate-400 mt-10" />}
              error={<p className="text-sm text-red-500 dark:text-red-400 mt-10">PDF görüntülenemedi.</p>}
            >
              <Page
                pageNumber={pageNumber}
                scale={scale}
                renderTextLayer={true}
                renderAnnotationLayer={true}
                className="shadow-lg"
              />
            </Document>
          )}
        </div>
      </div>
    </div>
  );
}
