import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { authService } from "../services/api";
import { ArrowLeft, User, Lock, LogOut, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import PasswordInput from "../components/PasswordInput";

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess(false);

    if (newPassword !== confirmPassword) {
      setError("Yeni şifreler eşleşmiyor.");
      return;
    }
    if (newPassword.length < 6) {
      setError("Yeni şifre en az 6 karakter olmalı.");
      return;
    }

    setLoading(true);
    try {
      await authService.changePassword(currentPassword, newPassword);
      setSuccess(true);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err.response?.data?.detail || "Bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate("/")} className="text-gray-400 hover:text-gray-700 transition-colors">
          <ArrowLeft size={20} />
        </button>
        <span className="text-sm font-medium text-gray-700">Profil</span>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {/* User info */}
        <div className="bg-white border border-gray-200 rounded-2xl p-5">
          <div className="flex items-center gap-3 mb-1">
            <div className="bg-indigo-100 rounded-full p-3">
              <User size={20} className="text-indigo-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800">{user?.name || "Kullanıcı"}</p>
              <p className="text-xs text-gray-500">{user?.email}</p>
            </div>
          </div>
        </div>

        {/* Change password */}
        <div className="bg-white border border-gray-200 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Lock size={17} className="text-indigo-500" />
            <h3 className="text-sm font-semibold text-gray-700">Şifre Değiştir</h3>
          </div>

          {success && (
            <div className="flex items-center gap-1.5 text-green-600 text-sm bg-green-50 rounded-lg px-3 py-2 mb-4">
              <CheckCircle size={14} /> Şifre başarıyla değiştirildi.
            </div>
          )}
          {error && (
            <div className="flex items-center gap-1.5 text-red-500 text-sm bg-red-50 rounded-lg px-3 py-2 mb-4">
              <AlertCircle size={14} /> {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Mevcut Şifre</label>
              <PasswordInput
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Yeni Şifre</label>
              <PasswordInput
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Yeni Şifre (Tekrar)</label>
              <PasswordInput
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg py-2.5 text-sm font-medium transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {loading && <Loader2 size={14} className="animate-spin" />}
              {loading ? "Kaydediliyor..." : "Şifreyi Güncelle"}
            </button>
          </form>
        </div>

        {/* Logout */}
        <button
          onClick={logout}
          className="w-full bg-white border border-gray-200 rounded-2xl p-4 flex items-center justify-center gap-2 text-red-500 hover:bg-red-50 transition-colors text-sm font-medium"
        >
          <LogOut size={16} />
          Çıkış Yap
        </button>
      </main>
    </div>
  );
}
