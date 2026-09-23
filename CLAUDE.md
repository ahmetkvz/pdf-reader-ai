# PDF Reader AI

Piyasaya sürülmesi planlanan bir ürün. Kullanıcı PDF yükler; uygulama metni
çıkarır, Groq üzerinden bir dil modeliyle analiz eder, belge üzerinden sohbet
ettirir, not aldırır ve PDF rapor üretir. Hedef kitle henüz kesinleşmedi
(öğrenciler ve hukukçular değerlendiriliyor). Bu yüzden aşağıdaki maddeler
sadece hata düzeltme değil, yayın öncesi hazırlık.

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

Frontend'i ayrı bir terminalde çalıştır:

```
cd frontend
npm run dev
```

Adres: http://localhost:5173

`frontend/.env.local` içindeki `VITE_API_URL` local backend'i gösterir
(`http://127.0.0.1:8000`). Bu dosya git'e girmez. Değişken yoksa kod canlı
backend adresine düşer, yani Vercel'de ayar gerekmez.

Canlı frontend: https://project-716py.vercel.app

Not: Proje kökünde de bir `.venv` var ama içi boş, onu kullanma.

## Ortam değişkenleri

`backend/.env` gerekli, git'e girmez. Kodun okuduğu isimler:

```
MONGO_URI, DB_NAME, JWT_SECRET, JWT_ALGORITHM,
ACCESS_TOKEN_EXPIRE_MINUTES, GROQ_API_KEY, RESEND_API_KEY,
GROQ_MODEL, MAX_PDF_PAGES
```

`MONGO_URI` ve `JWT_SECRET` zorunlu; eksikse uygulama açılmaz. Diğerlerinin
varsayılanı var (`GROQ_MODEL` → `openai/gpt-oss-120b`, `MAX_PDF_PAGES` → 500).

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
  backend adresini `VITE_API_URL`'den okur; tanımlı değilse canlı backend
  adresini kullanır.
- **Veritabanı:** MongoDB Atlas ücretsiz plan (`pdf-reader` cluster).

### Ücretsiz plan tuzakları

- Atlas uzun süre kullanılmayan cluster'ı durdurur. Durduğunda adresi DNS'ten
  düşer ve `The DNS query name does not exist` hatası gelir. Çözüm: Atlas
  panelinden **Resume**, ardından birkaç dakika bekle. Veriler kaybolmaz.
- Render ücretsiz plan istek gelmeyince uyur; ilk istek 50 saniye sürebilir.

## Kurallar

- `backend/.env` dosyasını okuma, yazma, içeriğini gösterme, commit etme.
- Ben söylemeden `git commit` veya `git push` yapma.
- Git komutlarını her zaman proje kökünden çalıştır:
  `cd C:\Users\Victus\Desktop\PROJELER\pdf-reader-ai`
  Terminal genelde `backend` klasöründe kalıyor ve yollar tutmuyor.
- `backend/__pycache__` altındaki `.pyc` dosyaları hâlâ git'te takipli.
  Commit'e ekleme, `git add .` kullanma; dosyaları tek tek ekle.
  (Madde 8'de git takibinden çıkarılacak.)
- Commit mesajları Türkçe, küçük harf, Türkçe karakter kullanmadan, kısa.
  Örnek: `korumasiz eski prototip endpointleri kaldirildi`
- Bir maddeyi bitirdiğinde bu dosyadaki kutucuğu `[x]` yap.
- Groq modelleri periyodik olarak kullanımdan kaldırılıyor.
  `llama-3.3-70b-versatile` 16 Ağustos 2026'da kapandı ve uygulama bir ay
  boyunca hiç cevap üretemedi. Model adı artık `GROQ_MODEL` ortam
  değişkeninde, varsayılan `openai/gpt-oss-120b`.

## Yapılacaklar

- [x] **1. Korumasız eski prototip endpoint'ler.** `main.py` içindeki
      `/upload`, `/files`, `/summary`, `/sensitive`, `/text-preview`,
      `/db-check` kimlik doğrulaması istemiyordu; yüklenen tüm PDF'ler
      herkese açıktı. Kaldırıldı. (commit `d093ca6`)

- [x] **2. JWT_SECRET varsayılanı.** `core/config.py` değişken yoksa
      `"supersecretkey123"` kullanıyor. Değişken eksikse uygulama hiç
      açılmamalı. Ayrıca kayıt ve şifre sıfırlamada minimum şifre uzunluğu
      kontrolü yok (şifre değiştirmede var). `config.py`'ye `_require_env`
      eklendi; `MONGO_URI` ve `JWT_SECRET` zorunlu oldu, eksikse uygulama
      açılmıyor. Şifre uzunluğu `MIN_PASSWORD_LENGTH = 8` sabitiyle kayıt,
      sıfırlama ve değiştirmede tutarlı hale getirildi. (commit `e87dc3d`)

- [x] **3. RAG indeksi RAM'de.** `services/rag_service.py` içindeki `_STORE`
      sözlüğü sunucu her yeniden başladığında siliniyor. Render uyuyup
      uyandığında indeks kayboluyor ve sohbet belgenin sadece ilk 4000
      karakterine bakıyor; sonraki sayfalarla ilgili sorulara "Bu bilgi
      belgede yer almıyor" cevabı dönüyor. `chat_routes.py` artık indeks
      yoksa Mongo'daki metinden yeniden kuruyor. (commit `e50e861`)

- [x] **4. Sadece ilk 20 sayfa.** Yüklemede `max_pages=20`; uzun belgelerin
      kalanı analize ve sohbete hiç girmiyor. Sınır `MAX_PDF_PAGES` ile 500
      oldu, `pageCount` ve `processedPages` kaydediliyor, sınır aşılırsa
      kullanıcıya bildiriliyor. (commit `c2b19f2`)

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
      Kullanıcıların ve olası ortakların ilk baktığı yer burası.

- [x] **11. Sabit ayarlar ortam değişkenine taşındı.** Groq model adı
      `analysis_service.py` içinde iki yerde sabitti; artık `GROQ_MODEL`
      değişkeninden okunuyor. Frontend API adresi `api.js` içinde sabitti;
      artık `VITE_API_URL` değişkeninden okunuyor. (commit `e50e861`)

- [ ] **12. Başarısız analiz kaydediliyor.** Analiz başarısız olduğunda hata
      metni sonuç olarak veritabanına kaydediliyor ve kullanıcıya özet diye
      gösteriliyor. Başarısız analiz kaydedilmemeli.

- [ ] **13. "PDF İndir" butonu.** Yüklenen belgeyi değil analiz raporunu
      indiriyor. Adı "Analiz Raporunu İndir" olmalı; orijinali indirmek için
      ayrı buton.

- [ ] **14. Arka arkaya sorularda cevaplar karışıyor.** Frontend cevapları
      karıştırıyor; bir sorunun cevabı hiç görünmüyor ve spinner sonsuza kadar
      dönüyor. Backend üçüne de 200 döndürüyor, sorun arayüzde. Her isteğe
      kimlik verilip cevabı kendi sorusuyla eşleştirilmeli, hata halinde
      spinner kapanmalı.

- [ ] **15. Sohbet cevapları kesiliyor.** `analysis_service.py` içinde sohbet
      cevapları `max_tokens=350` ile sınırlı. Cevaplar cümlenin hatta
      kelimenin ortasında kesiliyor. 800-1000'e çıkar.

- [ ] **16. PDF tekrar tekrar indiriliyor.** Aynı PDF dosyası Mongo'dan
      defalarca yeniden indiriliyor (loglarda `GET /documents/{id}/file`
      tekrar tekrar görünüyor). Gereksiz yük.

- [ ] **17. Analiz sadece belgenin başına bakıyor.** Analiz fonksiyonları
      metni `text[:3000]` / `text[:4000]` ile kesiyor, yani belgenin sadece
      ilk 1-2 sayfasını özetliyor. Sohbet 4. maddeden sonra tüm sayfalara
      ulaşıyor ama analiz ulaşmıyor. Uzun belgelerde parça parça özetleyip
      birleştirmek gerekiyor.

- [ ] **18. Hassas veri tespiti.** `analysis_service.py` `detect_sensitive`
      içindeki telefon deseninde yakalama grubu var: `(\+90|0)`.
      `re.findall` yakalama grubu varsa sadece grubu döndürdüğü için arayüzde
      telefon numarası olarak "0" görünüyor. `(?:\+90|0)` yapılmalı. Ayrıca
      silinen eski `main.py`'deki hassas veri tespitinde Luhn algoritması
      kontrolü ve telefon eleme mantığı vardı, bu sürümde yok. O kod
      `3130e7d` commit'inde duruyor, oradan geri alınabilir.

## Ürün yol haritası

Hata listesinden ayrı, kod dışı işler.

- Kullanım kotası ve hız limiti (kart bağlanmadan önce şart)
- Ödeme altyapısı (Türkiye için iyzico/PayTR, yurt dışı için Stripe)
- KVKK: aydınlatma metni, gizlilik politikası, veri silme hakkı
- Altyapı: Render ücretsiz plan uykuya dalıyor, ürün için yetersiz
- Kendi alan adı (güven + mail gönderimi, 5. maddeyi de çözer)
- Hata takibi (Sentry benzeri)
- Maliyet: `gpt-oss-120b` ile mesaj başına ~0,0006 dolar, analiz ~0,0023
  dolar. Asıl maliyet yapay zeka değil depolama olacak (6. madde).
