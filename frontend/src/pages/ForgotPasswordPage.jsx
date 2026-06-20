import { useState } from "react";
import { Link } from "react-router-dom";
import { authService } from "../services/api";
import { FileText, Mail, CheckCircle } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authService.forgotPassword(email);
      setSent(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden bg-gradient-to-br from-slate-100 via-white to-indigo-100 dark:from-slate-900 dark:via-slate-800 dark:to-indigo-950">
      {/* Dekoratif parlama efektleri */}
      <div className="absolute top-[-10%] left-[-10%] w-72 h-72 bg-indigo-400/20 dark:bg-indigo-500/20 rounded-full blur-3xl" />
      <div className="absolute bottom-[-10%] right-[-10%] w-80 h-80 bg-purple-400/20 dark:bg-purple-500/20 rounded-full blur-3xl" />

      <div className="w-full max-w-sm relative z-10">
        {/* Logo */}
        <div className="flex flex-col items-center justify-center gap-3 mb-8">
          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-3 shadow-lg shadow-indigo-500/30">
            <FileText className="text-white" size={28} />
          </div>
          <span className="text-2xl font-bold text-slate-800 dark:text-white tracking-tight">PDF Reader AI</span>
        </div>

        {/* Kart */}
        <div className="bg-white/80 dark:bg-slate-800/60 backdrop-blur-xl rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700/50 p-7">
          {sent ? (
            <div className="text-center py-4">
              <div className="bg-green-100 dark:bg-green-500/10 rounded-full p-3 w-fit mx-auto mb-3">
                <CheckCircle className="text-green-500" size={36} />
              </div>
              <h1 className="text-lg font-semibold text-slate-800 dark:text-white mb-2">Email Gönderildi</h1>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Eğer bu email kayıtlıysa, şifre sıfırlama bağlantısı gönderildi. Gelen kutunu kontrol et.
              </p>
            </div>
          ) : (
            <>
              <h1 className="text-lg font-semibold text-slate-800 dark:text-white mb-2">Şifremi Unuttum</h1>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-5">Email adresini gir, sana sıfırlama bağlantısı gönderelim.</p>

              {error && (
                <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-600 dark:text-red-400 text-sm rounded-lg px-3 py-2.5 mb-4">{error}</div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-600 dark:text-slate-300 mb-1.5">E-posta</label>
                  <div className="relative">
                    <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full bg-white dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-white rounded-lg pl-9 pr-3 py-2.5 text-sm placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                      placeholder="ornek@email.com"
                      required
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-lg py-2.5 text-sm font-medium transition-all shadow-lg shadow-indigo-500/30 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {loading ? "Gönderiliyor..." : "Sıfırlama Bağlantısı Gönder"}
                </button>
              </form>
            </>
          )}
        </div>

        <p className="text-center text-sm text-slate-500 dark:text-slate-400 mt-5">
          <Link to="/login" className="text-indigo-500 dark:text-indigo-400 font-medium hover:text-indigo-600 dark:hover:text-indigo-300 transition-colors">Girişe Dön</Link>
        </p>
      </div>
    </div>
  );
}
