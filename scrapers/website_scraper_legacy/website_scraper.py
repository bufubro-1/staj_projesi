"""
Aşama A: Şirket Websitelerinden Yönetici Bilgilerini Kazıma
============================================================
master_sirketler.csv'deki her domainin kendi sitesindeki
"Hakkımızda", "Ekibimiz", "Yönetim" gibi sayfalara giderek
yönetici isimlerini, unvanlarını ve e-postalarını çeker.

Çıktı: yoneticiler.csv (bulunanlara 'websitesi' kaynağı eklenir)
"""

import csv
import re
import os
import time
import random
import requests
import spacy
from bs4 import BeautifulSoup
from tqdm import tqdm

try:
    # Çok dilli küçük modeli yükle
    nlp = spacy.load("xx_ent_wiki_sm")
    print("[*] Spacy NLP modeli (xx_ent_wiki_sm) başarıyla yüklendi.")
except Exception as e:
    nlp = None
    print(f"[-] Spacy modeli yüklenemedi, varsayılan denetim kullanılacak. Hata: {e}")

INPUT_CSV = "sirketler.csv"  # veya master_sirketler.csv
OUTPUT_CSV = "yoneticiler.csv"
TARANAN_CSV = "taranan_sirketler.csv"  # Hangi şirketlerde bulundu/bulunmadı

# Türkçe yönetim sayfası yolları (en yaygın olanlar)
YONETIM_SAYFALARI = [
    '/hakkimizda', '/hakkinda', '/about', '/about-us',
    '/ekibimiz', '/ekip', '/team', '/our-team',
    '/yonetim', '/yonetim-kurulu', '/management', '/board',
    '/kurumsal', '/corporate', '/biz-kimiz',
    '/iletisim', '/contact', '/contact-us',
    '/kadromuz', '/organizasyon',
]

# Yönetici unvanları (Türkçe + İngilizce)
UNVAN_KALIPLARI = [
    r'genel\s*müdür', r'ceo', r'chief\s*executive',
    r'genel\s*koordinat', r'başkan',
    r'müdür', r'direktör', r'director',
    r'yönetim\s*kurulu', r'board',
    r'kurucu', r'founder', r'partner', r'ortak',
    r'satış\s*müdür', r'sales\s*(?:manager|director)',
    r'operasyon\s*müdür', r'operations?\s*(?:manager|director)',
    r'lojistik\s*müdür', r'logistics?\s*(?:manager|director)',
    r'finans\s*müdür', r'cfo', r'coo', r'cto',
    r'pazarlama\s*müdür', r'marketing\s*(?:manager|director)',
    r'insan\s*kaynakları', r'human\s*resources', r'hr\s*(?:manager|director)',
    r'manager', r'head\s*of',
]

UNVAN_REGEX = re.compile('|'.join(UNVAN_KALIPLARI), re.IGNORECASE)

# E-posta regex
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

# Genel/info/destek maillerini filtrele (Bunlar yönetici maili değil)
GENEL_MAIL_FILTRE = re.compile(r'^(info|destek|support|contact|iletisim|muhasebe|finans|sales|satis|halkla|hr|ik|kvkk|bilgi|admin|webmaster|noreply|no-reply)@', re.IGNORECASE)


def clean_unvan(unvan):
    """Unvan alanının başına yapışmış isim kalıplarını temizler.
    Örn: 'Gülgün DedeTicaret ve Operasyon Müdürü' → 'Ticaret ve Operasyon Müdürü'
    Örn: 'Sina KınayKINAY Yönetim Kurulu Başkanı' → 'Yönetim Kurulu Başkanı'
    """
    # Unvan içinde UNVAN_REGEX'e uyan ilk kalıbı bul, ondan öncesini kes
    match = UNVAN_REGEX.search(unvan)
    if match:
        # Eşleşen kısmın başlangıç indexinden itibaren al
        temiz = unvan[match.start():]
        # Baştaki küçük harfleri temizle (Örn: 'eTicaret' → 'Ticaret')
        temiz = re.sub(r'^[a-zçğıöşü]+', '', temiz).strip()
        if temiz:
            return temiz
    return unvan

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}


def get_page(url, timeout=8):
    """Sayfayı indir, hata varsa None döndür."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None


def extract_emails(html_text, domain):
    """HTML'den e-posta adreslerini çıkar. Sadece şirketin kendi domainindeki mailleri al."""
    mailler = EMAIL_REGEX.findall(html_text)
    # Sadece şirketin kendi domainindeki mailler (gmail, hotmail vs. atla)
    filtreli = []
    for m in mailler:
        m = m.lower().strip()
        # Şirketin domaini ile eşleşiyor mu?
        if domain in m and not GENEL_MAIL_FILTRE.match(m):
            filtreli.append(m)
    return list(set(filtreli))


def extract_people(soup):
    """
    Sayfadaki metinden isim + unvan çiftlerini bulmaya çalışır.
    """
    kisiler = []
    
    # Geçersiz isim kalıpları (UI metinleri, buton isimleri, ülke/şehir/şirket isimleri vb.)
    GECERSIZ_KELIMELER = {
        # UI / Buton metinleri
        'cookie', 'quote', 'mission', 'vision', 'policy', 'human', 'resources', 
        'contact', 'about', 'team', 'öneri', 'talep', 'başvuru', 'we', 'are',
        'yazın', 'bize', 'gönder', 'formu', 'form', 'submit', 'download', 'read',
        'more', 'click', 'here', 'view', 'show', 'menu', 'home', 'search',
        'why', 'choose', 'our', 'get', 'quick', 'learn', 'back', 'next', 'prev',
        'security', 'privacy', 'terms', 'conditions', 'suggestions', 'requests',
        # Ülke / Şehir isimleri
        'united', 'kingdom', 'turkey', 'türkiye', 'istanbul', 'ankara', 'izmir',
        'germany', 'london', 'usa', 'america', 'almanya', 'ingiltere', 'birleşik',
        'mersin', 'antalya', 'bursa', 'adana', 'samsun', 'eskişehir', 'kayseri',
        # Şirket tipleri ve sektör kelimeleri
        'ltd', 'şti', 'ticaret', 'sanayi', 'company', 'inc', 'corp',
        'hizmetleri', 'hizmetlere', 'services', 'service', 'destek', 'support',
        'lojistik', 'logistics', 'denizcilik', 'shipping', 'taşımacılık', 'transport',
        'gümrük', 'customs', 'global', 'uluslararası', 'international',
        'profesyonel', 'professional', 'industrial', 'scale', 'large',
        'ana', 'sayfa', 'page', 'araç', 'takibi', 'tracking',
        'ekip', 'çalışması', 'müşteri', 'formu', 'neden', 'seçmelisin',
        'repair', 'management', 'engine', 'cargo', 'white', 'glove',
        'incredible', 'personalized', 'full', 'beyan', 'bagaj', 'kargo',
        'taşıma', 'kara', 'yolu', 'digital', 'supply', 'chain', 'solutions',
        'hızlı', 'menü', 'menu', 'hizmeti', 'partnerliği'
    }
    
    text_blocks = soup.find_all(['p', 'li', 'td', 'span', 'div', 'h2', 'h3', 'h4', 'h5', 'strong'])
    
    for i, block in enumerate(text_blocks):
        text = block.get_text(strip=True)
        if not text or len(text) > 150:  
            continue
            
        if UNVAN_REGEX.search(text):
            unvan = text
            if len(unvan) > 60:
                continue
            # Unvan alanında @ veya http varsa atla (e-posta veya link, unvan değil)
            if '@' in unvan or 'http' in unvan:
                continue
                
            if i > 0:
                onceki = text_blocks[i-1].get_text(strip=True)
                kelimeler = onceki.split()
                if 2 <= len(kelimeler) <= 4 and not UNVAN_REGEX.search(onceki) and len(onceki) < 40:
                    # Sadece harf mi? (Boşluk hariç)
                    harfler_sadece = all(k.replace('.', '').isalpha() for k in kelimeler)
                    if harfler_sadece and all(k[0].isupper() for k in kelimeler if len(k) > 1):
                        if not any(g in onceki.lower() for g in GECERSIZ_KELIMELER):
                            # Spacy Denetimi
                            if nlp is not None:
                                doc = nlp(onceki)
                                if len(doc.ents) > 0 and not any(ent.label_ == "PER" for ent in doc.ents):
                                    continue # İçinde ORG, LOC var ama PER yoksa atla
                                    
                            kisiler.append({'isim': onceki, 'unvan': clean_unvan(unvan)})
                            continue
            
            parcalar = re.split(r'[\-–|/]', text)
            if len(parcalar) >= 2:
                potansiyel_isim = parcalar[0].strip()
                potansiyel_unvan = parcalar[1].strip()
                kelimeler = potansiyel_isim.split()
                if 2 <= len(kelimeler) <= 4 and not UNVAN_REGEX.search(potansiyel_isim) and len(potansiyel_isim) < 40:
                    harfler_sadece = all(k.replace('.', '').isalpha() for k in kelimeler)
                    if harfler_sadece and all(k[0].isupper() for k in kelimeler if len(k) > 1):
                        if not any(g in potansiyel_isim.lower() for g in GECERSIZ_KELIMELER):
                            # Spacy Denetimi
                            if nlp is not None:
                                doc = nlp(potansiyel_isim)
                                if len(doc.ents) > 0 and not any(ent.label_ == "PER" for ent in doc.ents):
                                    continue
                            kisiler.append({'isim': potansiyel_isim, 'unvan': clean_unvan(potansiyel_unvan)})
    
    # Tekilleştir (Deduplication)
    tekil_kisiler = []
    gorulenler = set()
    for k in kisiler:
        anahtar = (k['isim'], k['unvan'])
        if anahtar not in gorulenler:
            gorulenler.add(anahtar)
            tekil_kisiler.append(k)
            
    return tekil_kisiler


def scrape_company_website(domain):
    """Bir şirketin web sitesini tarayarak yönetici bilgilerini çeker."""
    bulunan_kisiler = []
    bulunan_mailler = []
    
    base_urls = [f"https://www.{domain}", f"https://{domain}", f"http://www.{domain}", f"http://{domain}"]
    
    calisan_url = None
    for base in base_urls:
        html = get_page(base)
        if html:
            calisan_url = base
            # Ana sayfadaki mailleri de topla
            bulunan_mailler.extend(extract_emails(html, domain))
            break
    
    if not calisan_url:
        return [], [], False  # Site erişilemez
    
    # Yönetim sayfalarını gez
    for sayfa_yolu in YONETIM_SAYFALARI:
        url = calisan_url + sayfa_yolu
        html = get_page(url)
        if not html:
            continue
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # E-posta çıkar
        mailler = extract_emails(html, domain)
        bulunan_mailler.extend(mailler)
        
        # Kişi bilgilerini çıkar
        kisiler = extract_people(soup)
        bulunan_kisiler.extend(kisiler)
        
        time.sleep(random.uniform(0.3, 0.8))  # Aynı siteye çok hızlı gitme
    
    # Şirket geneli tekilleştirme (Farklı sayfalardan aynı isim gelmişse)
    tekil_bulunan_kisiler = []
    gorulenler = set()
    for k in bulunan_kisiler:
        # İsimleri küçük harf yapıp boşlukları silerek tam eşleşme kontrolü yap
        anahtar = k['isim'].lower().replace(" ", "")
        if anahtar not in gorulenler:
            gorulenler.add(anahtar)
            tekil_bulunan_kisiler.append(k)
            
    bulunan_mailler = list(set(bulunan_mailler))
    
    return tekil_bulunan_kisiler, bulunan_mailler, True


def main():
    # Şirketleri oku
    sirketler = []
    if os.path.exists(INPUT_CSV):
        with open(INPUT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            sirketler = [row for row in reader if row.get('domain')]
    else:
        print(f"[-] {INPUT_CSV} bulunamadı!")
        return
        
    # Önceki taramada erişilemeyen siteleri oku ki tekrar vakit kaybetmeyelim
    erisilmez_siteler = set()
    if os.path.exists(TARANAN_CSV):
        with open(TARANAN_CSV, 'r', encoding='utf-8') as f:
            try:
                reader = csv.DictReader(f)
                erisilmez_siteler = {row['domain'] for row in reader if row.get('durum') == 'ERISILEMEDI'}
                print(f"[*] Önceki taramada erişilemeyen {len(erisilmez_siteler)} site atlanacak.")
            except Exception:
                pass
    
    print(f"[i] Toplam {len(sirketler)} şirketin websitesi taranacak...")
    print(f"[i] Her şirket için ~{len(YONETIM_SAYFALARI)} farklı sayfa denenecek.\n")
    
    bulundu_sayisi = 0
    bulunamadi_sayisi = 0
    erisim_yok_sayisi = 0
    
    # Çıktı dosyasını hazırla
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as out_f, \
         open(TARANAN_CSV, 'w', newline='', encoding='utf-8') as taran_f:
        
        yonetici_writer = csv.DictWriter(out_f, fieldnames=[
            'sirket_adi', 'domain', 'isim', 'unvan', 'email', 'kaynak'
        ])
        yonetici_writer.writeheader()
        
        taran_writer = csv.DictWriter(taran_f, fieldnames=[
            'ad', 'domain', 'durum', 'bulunan_kisi', 'bulunan_mail'
        ])
        taran_writer.writeheader()
        
        for sirket in tqdm(sirketler, desc="Websiteleri taranıyor"):
            domain = sirket.get('domain', '')
            ad = sirket.get('ad', '')
            
            if not domain:
                continue
                
            if domain in erisilmez_siteler:
                erisim_yok_sayisi += 1
                taran_writer.writerow({
                    'ad': ad,
                    'domain': domain,
                    'durum': 'ERISILEMEDI',
                    'bulunan_kisi': 0,
                    'bulunan_mail': 0
                })
                continue
            
            kisiler, mailler, erisilebildi = scrape_company_website(domain)
            
            if not erisilebildi:
                erisim_yok_sayisi += 1
                taran_writer.writerow({
                    'ad': ad, 'domain': domain,
                    'durum': 'ERİŞİLEMEDİ', 'bulunan_kisi': 0, 'bulunan_mail': 0
                })
                continue
            
            if kisiler:
                bulundu_sayisi += 1
                durum = 'BULUNDU'
                
                # Kişileri yaz
                for kisi in kisiler:
                    yonetici_writer.writerow({
                        'sirket_adi': ad,
                        'domain': domain,
                        'isim': kisi['isim'],
                        'unvan': kisi['unvan'],
                        'email': '',
                        'kaynak': 'websitesi'
                    })
            else:
                bulunamadi_sayisi += 1
                durum = 'BULUNAMADI'
            
            taran_writer.writerow({
                'ad': ad, 'domain': domain,
                'durum': durum,
                'bulunan_kisi': len(kisiler),
                'bulunan_mail': len(mailler)
            })
            
            # Siteler arası kısa bekleme (Ban koruması)
            time.sleep(random.uniform(0.5, 1.5))
    
    print(f"\n{'='*50}")
    print(f"İşlem Tamamlandı!")
    print(f"{'='*50}")
    print(f"✅ Yönetici/Mail Bulunan Şirket : {bulundu_sayisi}")
    print(f"❌ Bulunamayan Şirket           : {bulunamadi_sayisi}")
    print(f"🚫 Erişilemeyen Site            : {erisim_yok_sayisi}")
    print(f"📊 Toplam                       : {len(sirketler)}")
    print(f"\n[+] Sonuçlar '{OUTPUT_CSV}' dosyasına kaydedildi.")
    print(f"[+] Tarama raporu '{TARANAN_CSV}' dosyasına kaydedildi.")
    print(f"\n[i] Bulunamayan şirketler için Aşama B (Google Dorking) çalıştırılabilir.")


if __name__ == "__main__":
    main()
