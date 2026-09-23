# PDF Reader AI

PDF belgelerini yükleyip içerikleri üzerinden doğal dilde soru sorabildiğiniz, yapay zeka destekli bir okuma asistanı. Belgeyi özetler, anahtar noktaları çıkarır, içindeki hassas verileri tespit eder ve belge bağlamında sohbet etmenizi sağlar.

Web uygulaması olarak çalışır, Android paketi (APK) olarak da derlenebilir.

**Canlı uygulama:** https://project-716py.vercel.app
**API:** https://pdf-reader-backend-4rea.onrender.com

> Backend ücretsiz barındırma katmanında çalıştığı için uzun süre kullanılmadığında uykuya geçer. İlk istek 30–50 saniye sürebilir, sonrasında normal hızına döner.

---

## Ekran görüntüleri

<!-- Ekran görüntülerini docs/ klasörüne koyup buradaki yolları güncelleyin -->
<!-- ![Ana ekran](docs/anaekran.png) -->
<!-- ![Belge sohbeti](docs/sohbet.png) -->

---

## Özellikler

- **Belge yükleme ve metin çıkarma** — PDF dosyalarından sayfa bazlı metin çıkarımı
- **Belge üzerinden sohbet** — sorulan soruya göre ilgili bölümler getirilir ve cevap yalnızca belge içeriğine dayandırılır
- **Otomatik özet ve anahtar noktalar** — belgenin tamamı için özet çıkarımı
- **Hassas veri tespiti** — belge içindeki kimlik numarası, telefon, e-posta gibi kişisel verilerin işaretlenmesi
- **Not alma** — belge sayfaları üzerinde not tutma ve yönetme
- **PDF görüntüleyici** — belgeyi uygulama içinde açma
- **Dışa aktarma** — analiz sonuçlarının PDF olarak indirilmesi
- **Kullanıcı hesapları** — JWT tabanlı kimlik doğrulama, şifre sıfırlama ve e-posta doğrulama
- **Koyu / açık tema**
- **Mobil sürüm** — Capacitor ile Android APK

---

## Teknoloji yığını

### Backend
| Katman | Teknoloji |
|---|---|
| Çerçeve | FastAPI (Python) |
| Veritabanı | MongoDB Atlas |
| Dil modeli | Groq API üzerinden LLaMA 3.3 70B |
| Kimlik doğrulama | JWT (HS256), bcrypt ile şifre özetleme |
| PDF işleme | pypdf |
| E-posta | Resend |
| Dağıtım | Render |

### Frontend
| Katman | Teknoloji |
|---|---|
| Çerçeve | React + Vite |
| Stil | Tailwind CSS |
| Mobil | Capacitor (Android) |
| Dağıtım | Vercel |

---

## Mimari

```
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│   React SPA  │  HTTP  │   FastAPI    │        │ MongoDB Atlas│
│   (Vercel)   ├───────►│   (Render)   ├───────►│              │
└──────────────┘        └──────┬───────┘        └──────────────┘
       │                       │
       │                       │  metin parçaları + soru
┌──────▼───────┐        ┌──────▼───────┐
│ Android APK  │        │   Groq API   │
│ (Capacitor)  │        │  LLaMA 3.3   │
└──────────────┘        └──────────────┘
```

### İstek akışı

1. Kullanıcı PDF yükler; `pdf_service` metni sayfa bazında çıkarır ve parçalara böler
2. Belge ve parçalar MongoDB'ye kaydedilir
3. Kullanıcı soru sorduğunda `rag_service` soruyla en alakalı parçaları seçer
4. Seçilen parçalar ve soru birlikte dil modeline gönderilir
5. Model cevabı yalnızca verilen bağlama dayanarak üretir

### Getirme (retrieval) katmanı hakkında

Projede başlangıçta ChromaDB ile vektör tabanlı arama kullanıldı. Ancak ücretsiz barındırma katmanındaki bellek sınırı, gömme modeli ile vektör deposunun aynı süreçte çalışmasına izin vermedi ve servis kararsız hale geldi.

Uygulamanın kapsamı tek bir belge üzerinden soru cevaplama olduğu ve arama alanı dar kaldığı için, anahtar kelime ağırlıklı özel bir getirme katmanı yazıldı (`services/rag_service.py`). Cevap kalitesi kabul edilebilir düzeyde kaldı, servis kararlılığı sağlandı.

---

## Klasör yapısı

```
pdf-reader-ai/
├── backend/
│   ├── core/           # yapılandırma, bağımlılıklar, güvenlik (JWT, hashing)
│   ├── db/             # veritabanı bağlantısı
│   ├── models/         # veri modelleri
│   ├── schemas/        # istek/yanıt şemaları (Pydantic)
│   ├── routes/         # auth, document, chat, analysis, notes uçları
│   ├── services/       # iş mantığı: pdf, rag, analysis, email, export
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/            # React bileşenleri ve sayfalar
│   ├── android/        # Capacitor Android projesi
│   └── package.json
└── mobile/
```

İş mantığı `services` katmanında toplanmıştır; `routes` katmanı yalnızca istekleri karşılar ve doğrulama yapar.

---

## Kurulum

### Gereksinimler
- Python 3.10+
- Node.js 18+
- MongoDB Atlas hesabı
- Groq API anahtarı
- Resend API anahtarı (e-posta özellikleri için)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # değerleri kendi anahtarlarınızla doldurun
uvicorn main:app --reload
```

API varsayılan olarak `http://localhost:8000` adresinde çalışır.
Otomatik dokümantasyon: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Uygulama `http://localhost:5173` adresinde açılır.

### Ortam değişkenleri

`backend/.env.example` dosyasına bakın. Gerekli değişkenler:

| Değişken | Açıklama |
|---|---|
| `MONGODB_URI` | MongoDB Atlas bağlantı dizesi |
| `JWT_SECRET` | Token imzalama anahtarı |
| `JWT_ALGORITHM` | Varsayılan: `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token geçerlilik süresi |
| `GROQ_API_KEY` | Groq API anahtarı |
| `RESEND_API_KEY` | Resend API anahtarı |
| `MAIL_USERNAME` | Gönderici e-posta adresi |
| `MAIL_PASSWORD` | Uygulama şifresi |

---

## Android sürümü

```bash
cd frontend
npm run build
npx cap sync android
npx cap open android
```

Android Studio üzerinden APK derlenir. Capacitor yapılandırması `frontend/capacitor.config.json` dosyasındadır.

---

## Bilinen eksikler ve geliştirme planı

Bu bölüm projenin mevcut sınırlarını açıkça belirtmek için tutulmaktadır.

- **Vektör araması yok.** Getirme katmanı anahtar kelime ağırlıklı çalışıyor. Anlamsal arama, eşanlamlı ifadelerle sorulan sorularda daha iyi sonuç verirdi. PostgreSQL + pgvector ya da harici bir vektör servisi ile geri kazanılabilir.
- **Getirme kalitesi ölçülmüyor.** Doğru parçanın getirilip getirilmediğini ölçen bir değerlendirme seti bulunmuyor. Bir sonraki adımda örnek soru–kaynak eşleşmelerinden oluşan bir set kurulması planlanıyor.
- **Otomatik test kapsamı sınırlı.** Kritik akışlar (kimlik doğrulama, belge yükleme, getirme) için birim testleri yazılmadı.
- **Soğuk başlangıç.** Ücretsiz barındırma katmanı nedeniyle uzun süre kullanılmayan servisin ilk isteği yavaş.
- **Büyük belgelerde performans.** Çok sayfalı belgelerde metin çıkarımı istek içinde yapılıyor; arka plana taşınması gerekir.
- **Yüklenen dosyalar diskte tutuluyor.** Ölçeklenebilir bir kurulumda nesne depolama (S3 benzeri) kullanılmalı.

---

## Lisans

Bu proje bitirme projesi kapsamında geliştirilmiştir.

## İletişim

Ahmet Hakan Kavaz — [github.com/ahmetkvz](https://github.com/ahmetkvz)
