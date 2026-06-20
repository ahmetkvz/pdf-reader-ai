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
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-2 mb-8">
          <FileText className="text-indigo-600" size={28} />
          <span className="text-xl font-semibold text-gray-800">PDF Reader AI</span>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          {sent ? (
            <div className="text-center py-4">
              <CheckCircle className="text-green-500 mx-auto mb-3" size={40} />
              <h1 className="text-lg font-semibold text-gray-800 mb-2">Email Gönderildi</h1>
              <p className="text-sm text-gray-500">
                Eğer bu email kayıtlıysa, şifre sıfırlama bağlantısı gönderildi. Gelen kutunu kontrol et.
              </p>
            </div>
          ) : (
            <>
              <h1 className="text-lg font-semibold text-gray-800 mb-2">Şifremi Unuttum</h1>
              <p className="text-sm text-gray-500 mb-5">Email adresini gir, sana sıfırlama bağlantısı gönderelim.</p>

              {error && (
                <div className="bg-red-50 text-red-600 text-sm rounded-lg px-3 py-2 mb-4">{error}</div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">E-posta</label>
                  <div className="relative">
                    <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full border border-gray-200 rounded-lg pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="ornek@email.com"
                      required
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg py-2.5 text-sm font-medium transition-colors disabled:opacity-60"
                >
                  {loading ? "Gönderiliyor..." : "Sıfırlama Bağlantısı Gönder"}
                </button>
              </form>
            </>
          )}
        </div>

        <p className="text-center text-sm text-gray-500 mt-4">
          <Link to="/login" className="text-indigo-600 font-medium hover:underline">Girişe Dön</Link>
        </p>
      </div>
    </div>
  );
}
