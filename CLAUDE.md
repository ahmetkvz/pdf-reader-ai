# PDF Reader AI

Bitirme projesi. Kullanıcı PDF yükler; uygulama metni çıkarır, Groq/LLaMA 3.3 70B
ile analiz eder, belge üzerinden sohbet ettirir, not aldırır ve PDF rapor üretir.

## Dil

Bu projede bana her zaman Türkçe cevap ver.

## Yapı

- `backend/` — FastAPI + MongoDB Atlas. Render'da yayında.
- `frontend/` — React + Vite. Vercel'de yayında. Capacitor ile Android paketi var.
- `mobile/` — Yarım kalmış Expo denemesi. Kullanılmıyor (madde 9'da kaldırılacak).

## Çalıştırma (Windows / PowerShell)

Sanal ortam `backend/.venv` içinde. Proje `Desktop`'tan `Desktop/PROJELER`
altına taşındığı için venv'in kısayolları (`uvicorn.exe`, `pip.exe`) eski yolu
arıyor ve çalışmıyor. Bu yüzden komutları `python -m` ile çağır:

```
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload
```

Doğrudan `uvicorn main:app` yazma — "not recognized" hatası verir.
Aynı şekilde `pip install` yerine `python -m pip install`.

API dokümanı: http://127.0.0.1:8000/docs

Not: Proje kökünde de bir `.venv` var ama içi boş, onu kullanma.

## Ortam değişkenleri

`backend/.env` gerekli, git'e girmez. Kodun okuduğu isimler:

```
MONGO_URI, DB_NAME, JWT_SECRET, JWT_ALGORITHM,
ACCESS_TOKEN_EXPIRE_MINUTES, GROQ_API_KEY, RESEND_API_KEY
```

Dikkat: `backend/.env.example` dosyasında yanlışlıkla `MONGODB_URI` yazıyor,
kod ise `MONGO_URI` okuyor. Örneği birebir kopyalayan veritabanına bağlanamaz.
(Madde 8'de düzeltilecek.)

## Yayın

- **Backend:** Render → `ahmetkvz/pdf-reader-ai`, branch `main`,
  Root Directory `backend`,
  Build Command `pip install -r requirements.txt`,
  Start Command `uvicorn main:app --host 0.0.0.0 --port $PORT`.
  Auto-Deploy açık.
- **Frontend:** Vercel. `frontend/src/services/api.js` içindeki `baseURL`
  backend adresini gösterir.
- **Veritabanı:** MongoDB Atlas ücretsiz plan (`pdf-reader` cluster).

### Ücretsiz plan tuzakları

- Atlas uzun süre kullanılmayan cluster'ı durdurur. Durduğunda adresi DNS'ten
  düşer ve `The DNS query name does not exist` hatası gelir. Çözüm: Atlas
  panelinden **Resume**, ardından birkaç dakika bekle. Veriler kaybolmaz.
- Render ücretsiz plan istek gelmeyince uyur; ilk istek 50 saniye sürebilir.

## Kurallar

- `backend/.env` dosyasını okuma, yazma, içeriğini gösterme, commit etme.
- Ben söylemeden `git commit` veya `git push` yapma.
- `backend/__pycache__` altındaki `.pyc` dosyaları hâlâ git'te takipli.
  Commit'e ekleme, `git add .` kullanma; dosyaları tek tek ekle.
  (Madde 8'de git takibinden çıkarılacak.)
- Commit mesajları Türkçe, küçük harf, Türkçe karakter kullanmadan, kısa.
  Örnek: `korumasiz eski prototip endpointleri kaldirildi`
- Bir maddeyi bitirdiğinde bu dosyadaki kutucuğu `[x]` yap.

## Yapılacaklar

- [x] **1. Korumasız eski prototip endpoint'ler.** `main.py` içindeki
      `/upload`, `/files`, `/summary`, `/sensitive`, `/text-preview`,
      `/db-check` kimlik doğrulaması istemiyordu; yüklenen tüm PDF'ler
      herkese açıktı. Kaldırıldı. (commit `d093ca6`)

- [ ] **2. JWT_SECRET varsayılanı.** `core/config.py` değişken yoksa
      `"supersecretkey123"` kullanıyor. Değişken eksikse uygulama hiç
      açılmamalı. Ayrıca kayıt ve şifre sıfırlamada minimum şifre uzunluğu
      kontrolü yok (şifre değiştirmede var).

- [ ] **3. RAG indeksi RAM'de.** `services/rag_service.py` içindeki `_STORE`
      sözlüğü sunucu her yeniden başladığında siliniyor. Render uyuyup
      uyandığında indeks kayboluyor ve sohbet belgenin sadece ilk 4000
      karakterine bakıyor; sonraki sayfalarla ilgili sorulara "Bu bilgi
      belgede yer almıyor" cevabı dönüyor.

- [ ] **4. Sadece ilk 20 sayfa.** Yüklemede `max_pages=20`; uzun belgelerin
      kalanı analize ve sohbete hiç girmiyor.

- [ ] **5. Şifre sıfırlama maili.** `services/email_service.py` gönderici
      olarak `onboarding@resend.dev` kullanıyor. Resend bu test adresiyle
      yalnızca hesap sahibinin kendi adresine gönderiyor, diğer kullanıcılara
      mail ulaşmıyor.

- [ ] **6. PDF base64 olarak Mongo'da.** Dosya, metinle aynı dokümanda
      saklanıyor. MongoDB'nin 16 MB doküman sınırı yüzünden ~12 MB üstü
      dosyalar 500 hatası veriyor. Boyut sınırı ve anlaşılır hata mesajı
      gerekiyor. Ayrıca diske de yazılıyor ama Render'da kalıcı olmadığı için
      gereksiz.

- [ ] **7. Öksüz notlar.** Belge silinince `notes` koleksiyonundaki notları
      kalıyor (`routes/document_routes.py` sadece `analyses` siliyor).

- [ ] **8. Repo temizliği.** 16 adet `.pyc` ve `.vscode` dosyası hâlâ git'te
      takipli, bu yüzden backend her çalıştığında `git status` kirleniyor.
      Git takibinden çıkar. `.env.example`'daki `MONGODB_URI` → `MONGO_URI`
      düzelt.

- [ ] **9. Bağımlılık temizliği.** `requirements.txt`'te 94 paket var, kodun
      doğrudan kullandığı ~15 tanesi; gerisi ChromaDB ve Gemini döneminden
      kalma. Temizle ve sanal ortamı sıfırdan kur (taşınma sorunu da böylece
      çözülür). `mobile/` klasörünü kaldır. `analysis_service.py` içindeki
      `_with_gemini` fonksiyon adlarını düzelt (artık Groq kullanılıyor).

- [ ] **10. README.** Kök dizinde README yok; mevcut iki README Vite ve
      Expo'nun hazır şablonları. Kurulum adımları, ortam değişkenleri,
      çalıştırma komutları, mimari özeti ve ücretsiz plan uyarıları yazılacak.
      İşverenlerin ilk baktığı yer burası.
