# Antigravity Ajanı için Proje Kuralları (Sirket-Veritabani)

Bu dosya, bu projedeki otonom ajanların çalışma prensiplerini ve uyacakları kuralları belirler.

## Genel Kurallar
1. **Sıfır Maliyet Prensibi:** Araç seçimlerinde (API'ler, Veritabanları, Doğrulama servisleri) olabildiğince ücretsiz, hacking/dorking temelli ve API limiti yemeyen yöntemler tercih edilmelidir.
2. **SQL Kullanımı:** Kullanıcı aksini belirtmedikçe PostgreSQL, MySQL, SQLite vb. SQL veritabanı kütüphaneleri kullanılmamalı, veriler `CSV` veya `JSON` formatında düz dosyalara (flat files) kaydedilmelidir.
3. **Veri Temizliği:** Çekilen isimler ve domainler, mutlaka özel temizleme (deduplication) fonksiyonlarından geçirilmeli ve `master_sirketler.csv` dosyasında birleştirilmelidir.
4. **IP Ban Koruması:** Tüm Python scraping scriptlerinde (BeautifulSoup, requests) mutlaka rastgele bekleme (time.sleep) süreleri ve User-Agent rotasyonu eklenmelidir.
