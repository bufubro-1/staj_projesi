import csv
import re
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time

def scrape_und():
    print("UND Üye Listesi taranıyor... (İlk sayfa inceleniyor)")
    base_url = "https://www.und.org.tr/uyelerimiz"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 1. Aşama: Şirket listesi ve ID'leri çek
    sirket_linkleri = []
    
    page = 1
    while True:
        url = f"{base_url}?p={page}" if page > 1 else base_url
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            break
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = soup.find_all('a', href=re.compile(r'/firma-bilgileri/\d+'))
        
        if not links:
            break # Sayfada link yoksa döngüyü kır (Son sayfaya geldik)
            
        yeni_link_sayisi = 0
        for link in links:
            href = link.get('href')
            ad = link.get_text(strip=True)
            if href and ad and (href, ad) not in sirket_linkleri:
                sirket_linkleri.append((href, ad))
                yeni_link_sayisi += 1
                
        if yeni_link_sayisi == 0:
            break # Bu sayfada hiç yeni link bulamadıysak sonuna gelmişizdir
            
        print(f"Sayfa {page} tarandı, şu ana kadar {len(sirket_linkleri)} şirket bulundu...")
        page += 1
        time.sleep(1) # Banlanmamak için
        
    print(f"Toplam {len(sirket_linkleri)} adet UND üyesi detay sayfası bulundu. Detaylar çekiliyor (Bu işlem yaklaşık 15-20 dakika sürebilir)...")
    
    # 2. Aşama: Detay sayfalarından veri çek
    sirketler_listesi = []
    for link, ad in tqdm(sirket_linkleri):
        detay_url = link if link.startswith('http') else "https://www.und.org.tr" + link
        
        try:
            resp = requests.get(detay_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                dsoup = BeautifulSoup(resp.text, 'html.parser')
                
                # Detay sayfasından website, telefon, sehir bul
                # Daha önce "Arkas Lojistik" örneğinde websitesinin a href'te veya tabloda olduğunu gördük
                website = None
                telefon = None
                sehir = None
                email = None
                
                # Sitede "Website" yazan tablo satırını bulma
                tds = dsoup.find_all('td')
                for i, td in enumerate(tds):
                    text = td.get_text(strip=True)
                    if 'Website' in text and i + 2 < len(tds):
                        a = tds[i+2].find('a')
                        if a: website = a.get('href')
                    elif 'Telefon' in text and i + 2 < len(tds):
                        telefon = tds[i+2].get_text(strip=True)
                    elif 'İl / Ülke' in text and i + 2 < len(tds):
                        sehir_metin = tds[i+2].get_text(strip=True)
                        sehir = sehir_metin.split('/')[0].strip() if '/' in sehir_metin else sehir_metin
                        
                domain = clean_domain(website)
                
                sirketler_listesi.append({
                    'ad': ad,
                    'domain': domain if domain else '',
                    'email': email if email else '',
                    'telefon': telefon if telefon else '',
                    'sehir': sehir if sehir else ''
                })
        except Exception as e:
            pass
            
        time.sleep(0.5)
        
    # 3. Aşama: CSV'ye yaz
    csv_file = "und_sirketler.csv"
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['ad', 'domain', 'email', 'telefon', 'sehir'])
        writer.writeheader()
        writer.writerows(sirketler_listesi)
        
    print(f"\nUND işlemi tamamlandı! {len(sirketler_listesi)} şirket 'und_sirketler.csv'ye yazıldı.")

if __name__ == "__main__":
    scrape_und()
