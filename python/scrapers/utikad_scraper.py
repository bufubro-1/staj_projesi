import sys
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from proje_kok import csv_yol

def clean_domain(url):
    """URL'den 'http(s)://' ve 'www.' kısımlarını atar."""
    if not url:
        return None
    url = url.lower().strip()
    url = re.sub(r'^https?:\/\/', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.split('/')[0] # Path varsa at
    if len(url) < 3 or '.' not in url:
        return None
    return url

def scrape_utikad():
    print("UTİKAD Üye Listesi taranıyor...")
    url = "https://www.utikad.org.tr/UTIKAD-Uye-Listesi"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Hata! Sayfaya erişilemedi: {response.status_code}")
        return
        
    with open("scrapers/debug.html", "w", encoding="utf-8") as f:
        f.write(response.text)

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # UTİKAD'daki üyeler genellikle <div class="col-md-6 mb-3"> veya benzeri kartlar içinde listeleniyor
    # Veya list-group-item. HTML yapısını önceki araştırmamıza dayanarak analiz edelim:
    # Sayfada genellikle <a> tagleri içinde veya tabloda bulunuyor.
    
    sirket_bloklari = soup.find_all('div', class_='Uyeler')
    
    if not sirket_bloklari:
        print("HTML'de 'Uyeler' div'leri bulunamadı. Yapı değişmiş olabilir.")
        return
        
    # Dictionary kullanarak domain bazında tekilleştirme yapıyoruz
    sirketler_dict = {}
    
    for blok in sirket_bloklari:
        # İsim ve Website
        isim_tag = blok.find('div', class_='col-sm-12')
        if not isim_tag:
            continue
            
        a_tag = isim_tag.find('a')
        isim = a_tag.get_text(strip=True) if a_tag else isim_tag.get_text(strip=True)
        website = a_tag.get('href', '') if a_tag else ''
        domain = clean_domain(website)
        
        # Email
        email_tag = blok.find('a', href=re.compile(r'^mailto:'))
        email = email_tag.get('href').replace('mailto:', '').strip() if email_tag else None
        if email and email == "": email = None
        
        # Telefon
        telefon_tag = blok.find('span', class_='glyphicon-earphone')
        telefon = None
        if telefon_tag:
            tel_i = telefon_tag.find_next_sibling('i')
            if tel_i:
                telefon = tel_i.get_text(strip=True)
                
        # Adres ve Şehir
        adres_tag = blok.find('span', class_='glyphicon-map-marker')
        sehir = None
        if adres_tag:
            adres_i = adres_tag.find_next_sibling('i')
            if adres_i:
                adres_metin = adres_i.get_text(strip=True)
                # Genellikle "Adres / İlçe / ŞEHİR" formatında oluyor
                parcalar = [p.strip() for p in adres_metin.split('/')]
                if len(parcalar) > 1:
                    sehir = parcalar[-1] # En sondaki il
                else:
                    sehir = adres_metin

        if domain: # Sadece geçerli domaini olanları kaydet
            # Eğer domain daha önce eklendiyse ve boş veriler varsa doldur
            if domain in sirketler_dict:
                if not sirketler_dict[domain]['email'] and email:
                    sirketler_dict[domain]['email'] = email
                if not sirketler_dict[domain]['telefon'] and telefon:
                    sirketler_dict[domain]['telefon'] = telefon
            else:
                sirketler_dict[domain] = {
                    'ad': isim,
                    'domain': domain,
                    'email': email,
                    'telefon': telefon,
                    'sehir': sehir
                }

    print(f"Toplam {len(sirketler_dict)} adet benzersiz şirket bulundu. DB'ye yazılıyor...")
    
    import csv
    
    with open(csv_yol("sirketler.csv"), mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['ad', 'domain', 'email', 'telefon', 'sehir'])
        writer.writeheader()
        for veriler in sirketler_dict.values():
            writer.writerow(veriler)

    print(f"\nİşlem Tamamlandı!")
    print(f"Veriler '{csv_yol('sirketler.csv')}' dosyasına başarıyla kaydedildi.")

if __name__ == "__main__":
    scrape_utikad()
