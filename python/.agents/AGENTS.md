# Sirket-Veritabani — Ajan Kuralları

Türkiye'deki lojistik şirketlerinin üye listelerinden toplanması, birleştirilmesi ve yönetici bilgilerinin zenginleştirilmesi için kullanılan staj projesi. Bu dosya, bu repoda çalışan otonom ajanların uyacağı kuralları tanımlar.

## Proje Yapısı

```
sirket-veritabani/
├── python/
│   ├── scrapers/
│   │   ├── utikad_scraper.py
│   │   ├── und_scraper.py
│   │   ├── merge_and_dedup.py
│   │   └── final_serpapi_scraper.py
│   └── database/
├── dotnet/                        # .NET CLI (aynı CSV'ler)
├── master_sirketler.csv
└── .env
```

## Veri Akışı

1. **Kaynak kazıma:** `utikad_scraper.py` ve `und_scraper.py` dernek sitelerinden şirket bilgisi çeker.
2. **Birleştirme:** `merge_and_dedup.py` kaynak dosyaları domain ve temizlenmiş isim bazında birleştirir.
3. **Zenginleştirme:** Yönetici bilgisi ya `website_scraper_legacy/` (ücretsiz, site taraması) ya da `final_serpapi_scraper.py` (SerpAPI, ücretli API) ile eklenir.

Scriptler proje kök dizininden çalıştırılmalıdır:

```bash
python python/scrapers/utikad_scraper.py
python python/scrapers/und_scraper.py
python python/scrapers/merge_and_dedup.py
python python/scrapers/final_serpapi_scraper.py
```

## CSV Şemaları

### Şirket dosyaları (`sirketler.csv`, `und_sirketler.csv`, `master_sirketler.csv`)

| Alan     | Açıklama                                      |
|----------|-----------------------------------------------|
| ad       | Şirket adı                                    |
| domain   | Temizlenmiş domain (www/https olmadan)        |
| email    | Genel e-posta                                 |
| telefon  | Telefon                                       |
| sehir    | Şehir                                         |
| kaynak   | Sadece `master_sirketler.csv`'de; örn. `UTIKAD + UND` |

### Yönetici dosyaları (`yoneticiler.csv`, `yoneticiler_final.csv`)

| Alan         | Açıklama                          |
|--------------|-----------------------------------|
| sirket_adi   | master listesindeki şirket adı    |
| departman    | Departman veya `Yönetici`         |
| isim         | Kişi adı                          |
| unvan        | Görev unvanı                      |
| email        | Gerçek veya tahmini e-posta       |
| linkedin_url | LinkedIn profil URL'si (varsa)    |

## Genel Kurallar

1. **Sıfır maliyet önceliği:** API'ler, doğrulama servisleri ve ücretli araçlar yerine mümkün olduğunca ücretsiz yöntemler (BeautifulSoup, requests, DuckDuckGo, site taraması) tercih edilmelidir. SerpAPI gibi ücretli servisler yalnızca kullanıcı açıkça istediğinde veya mevcut script üzerinde çalışıldığında kullanılmalıdır.

2. **Düz dosya depolama:** Kullanıcı aksini belirtmedikçe PostgreSQL, MySQL, SQLite vb. SQL kütüphaneleri eklenmemeli; veriler `CSV` veya `JSON` olarak düz dosyalara yazılmalıdır. `database/` modülü mevcut olsa da ikincil katmandır; yeni özellikler önce CSV pipeline'ına eklenmelidir.

3. **Veri temizliği:** Çekilen isimler ve domainler `clean_domain()` / `clean_company_name()` mantığına uygun temizlenmeli, domain bazında tekilleştirilmeli ve `master_sirketler.csv` dosyasında birleştirilmelidir. Yeni scraper'lar aynı temizleme fonksiyonlarını paylaşmalı veya `merge_and_dedup.py`'ye entegre edilmelidir.

4. **IP ban koruması:** Tüm scraping scriptlerinde rastgele bekleme (`time.sleep`) ve User-Agent rotasyonu kullanılmalıdır. UND scraper'daki `time.sleep(0.5–1)` aralığı referans alınabilir.

5. **Gizli bilgiler:** `.env` dosyası commit edilmemelidir. API anahtarları (`SERPAPI_KEY`) ve veritabanı şifreleri yalnızca ortam değişkenlerinden okunmalıdır. `.env.example` şablonu güncel tutulmalıdır.

6. **Git ve CSV:** Çoğu CSV dosyası `.gitignore`'dadır. Yalnızca `master_sirketler.csv` ve `und_sirketler.csv` izlenir. Geçici veya ara çıktılar commit edilmemelidir.

## Scraping Kuralları

- Yeni scraper'lar `scrapers/` altına eklenir; dosya adı `{kaynak}_scraper.py` formatını izler.
- Çıktı dosyaları proje köküne yazılır (ör. `sirketler.csv`, `und_sirketler.csv`).
- Domain temizleme: `https?://`, `www.` kaldırılır; path atılır; geçersiz domainler (`len < 3` veya `.` yok) filtrelenir.
- Şirket adı normalizasyonu: Türkçe karakterler ASCII'ye çevrilir, `A.Ş.`, `Ltd. Şti.` gibi yasal ekler temizlenir.
- Hata durumunda script çökmemeli; tek kayıt hataları loglanıp atlanmalı (`try/except` ile devam).

## Yönetici Zenginleştirme

- **Website scraper (legacy):** Şirket sitesindeki Hakkımızda/Ekip/Yönetim sayfalarını tarar; spaCy (`xx_ent_wiki_sm`) ile isim doğrulaması yapar.
- **SerpAPI scraper:** LinkedIn profillerini Google aramasıyla bulur; spaCy + unvan filtresi uygular; tahmini e-posta üretir.
- Yönetici isimleri 2–4 kelime, yalnızca harf içermeli; sektör/şirket kelimeleri (`lojistik`, `ltd`, `şti` vb.) filtrelenmelidir.

## Ortam Kurulumu

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Gerekli anahtarları doldur
```

Gerekli spaCy modeli `requirements.txt` içinde tanımlıdır (`xx_ent_wiki_sm`).

## Kod Stili

- Mevcut kod Türkçe değişken/fonksiyon adları kullanır; yeni kod aynı stili sürdürmelidir.
- Gereksiz soyutlama ve geniş kapsamlı refactor yapılmamalı; en küçük doğru diff tercih edilmelidir.
- Yorumlar yalnızca iş mantığı veya HTML yapısı gibi belirsiz noktalar için eklenmelidir.
- Test dosyaları yalnızca kullanıcı istediğinde veya anlamlı davranış kapsamı sağladığında yazılmalıdır.

## Veritabanı (İsteğe Bağlı)

`database/` modülü PostgreSQL'e bağlanır; başarısız olursa SQLite'a düşer. Yeni geliştirmelerde öncelik CSV pipeline'ındadır. SQL katmanına geçiş yalnızca kullanıcı açıkça istediğinde yapılmalıdır.
