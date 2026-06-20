import { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { authService } from "../services/api";
import { FileText, Lock, CheckCircle } from "lucide-react";
import PasswordInput from "../components/PasswordInput";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Şifreler eşleşmiyor.");
      return;
    }
    if (password.length < 6) {
      setError("Şifre en az 6 karakter olmalı.");
      return;
    }
    if (!token) {
      setError("Geçersiz bağlantı.");
      return;
    }

    setLoading(true);
    try {
      await authService.resetPassword(token, password);
      setSuccess(true);
      setTimeout(() => navigate("/login"), 2500);
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
          {success ? (
            <div className="text-center py-4">
              <CheckCircle className="text-green-500 mx-auto mb-3" size={40} />
              <h1 className="text-lg font-semibold text-gray-800 mb-2">Şifre Sıfırlandı</h1>
              <p className="text-sm text-gray-500">Giriş sayfasına yönlendiriliyorsun...</p>
            </div>
          ) : (
            <>
              <h1 className="text-lg font-semibold text-gray-800 mb-5">Yeni Şifre Belirle</h1>

              {error && (
                <div className="bg-red-50 text-red-600 text-sm rounded-lg px-3 py-2 mb-4">{error}</div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Yeni Şifre</label>
                  <PasswordInput
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full border border-gray-200 rounded-lg pl-3 pr-10 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Şifreyi Onayla</label>
                  <PasswordInput
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full border border-gray-200 rounded-lg pl-3 pr-10 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg py-2.5 text-sm font-medium transition-colors disabled:opacity-60"
                >
                  {loading ? "Kaydediliyor..." : "Şifreyi Sıfırla"}
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
