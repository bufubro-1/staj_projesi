"""
DataForSEO Test Scripti
SerpApi ile aynı sorguyu DataForSEO üzerinden çalıştırıp sonuçları karşılaştırır.
"""
import os
import re
import csv
import json
import spacy
import requests
from base64 import b64encode
from unidecode import unidecode
from dotenv import load_dotenv

load_dotenv()

LOGIN = os.getenv("DATAFORSEO_LOGIN")
PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

credentials = b64encode(f"{LOGIN}:{PASSWORD}".encode()).decode()
HEADERS = {
    "Authorization": f"Basic {credentials}",
    "Content-Type": "application/json"
}

API_URL = "https://sandbox.dataforseo.com/v3/serp/google/organic/live/regular"

try:
    nlp = spacy.load("xx_ent_wiki_sm")
    print("[*] Spacy modeli yüklendi.")
except Exception:
    print("[-] Spacy yüklenemedi.")
    exit(1)

KONTROL_KELIMELERI = ["genel müdür", "ceo", "kurucu", "direktör", "manager", "müdür", "yönetici", "şef", "head"]

GECERSIZ_KELIMELER = {
    'lojistik', 'logistics', 'taşımacılık', 'transport', 'nakliyat', 'kargo',
    'gümrük', 'customs', 'global', 'uluslararası', 'international',
    'sanayi', 'ticaret', 'şirketi', 'ltd', 'şti', 'a.ş', 'aş', 'hizmetleri',
    'linkedin', 'profil'
}

def sirket_adini_temizle(ad):
    ad_lower = ad.lower()
    silinecekler = [
        "sanayi", "ticaret", "hizmetleri", "ltd.", "şti.", "ltd", "şti", "a.ş.", "aş.", "a.s.", "aş",
        "tic.", "san.", "ve", "danışmanlık", "müşavirliği", "yayıncılık", "turizm",
        "dış", "iç", "ithalat", "ihracat", "pazarlama", "uluslararası", "global",
        "nakliyat", "taşımacılık", "gıda", "dan.", "lojistik", "tic", "san", "dan"
    ]
    silinecekler.remove("lojistik")
    kelimeler = ad_lower.split()
    yeni_kelimeler = []
    for k in kelimeler:
        k_temiz = k.strip(".,;:|/'\"-")
        if k_temiz not in silinecekler:
            yeni_kelimeler.append(k_temiz)
    temiz_ad = " ".join(yeni_kelimeler)
    if not temiz_ad or len(temiz_ad) < 2:
        return ad.split()[0] if ad.split() else ad
    return temiz_ad.title()

def belirleyici_sirket_adi(kisa_ad):
    kelimeler = kisa_ad.split()
    return " ".join(kelimeler[:3]).lower() if len(kelimeler) >= 3 else kisa_ad.lower()

def clean_name(name):
    name = name.strip(".,;:|/'\"- ")
    words = name.split()
    if len(words) < 2 or len(words) > 4:
        return None
    if not all(w.replace('.','').isalpha() for w in words):
        return None
    name_lower = name.lower()
    if any(g in name_lower.split() for g in GECERSIZ_KELIMELER):
        return None
    return name.title()

def ismini_ve_unvanini_basliktan_cikar(baslik):
    parcalar = re.split(r'[-|·]', baslik)
    if not parcalar:
        return None, "Yönetici"
    olasi_isim = parcalar[0].strip()
    temiz_isim = clean_name(olasi_isim)
    if not temiz_isim:
        return None, "Yönetici"
    doc = nlp(temiz_isim)
    is_per, is_org = False, False
    for ent in doc.ents:
        if ent.label_ == "PER": is_per = True
        elif ent.label_ == "ORG": is_org = True
    if is_org and not is_per:
        return None, "Yönetici"
    unvan = parcalar[1].strip() if len(parcalar) > 1 else "Yönetici"
    unvan = unvan.replace("...", "").replace("..", "").strip()
    unvan = re.sub(r'(?i)\s+at\s+.*$', '', unvan)
    unvan = re.sub(r'(?i)\s+at$', '', unvan)
    unvan = re.sub(r'\s+@\s+.*$', '', unvan)
    unvan = re.sub(r'^.*? şirketinde ', '', unvan)
    unvan = re.sub(r'(?i)\s+(and|ve|&)$', '', unvan)
    unvan = unvan.strip(" -/,|")
    unvan_kelimeleri = ["müdür", "manager", "ceo", "kurucu", "direktör", "şef", "head", "uzman", "specialist", "coordinator", "president", "vp", "chief", "smmm", "analiz", "sales", "operation", "ik", "hr", "yönetici"]
    is_valid = any(k in unvan.lower() for k in unvan_kelimeleri)
    if not is_valid:
        if len(parcalar) > 2:
            unvan_2 = parcalar[2].strip()
            if any(k in unvan_2.lower() for k in unvan_kelimeleri):
                unvan = unvan_2
            else:
                unvan = "Yönetici"
        else:
            unvan = "Yönetici"
    if len(unvan) > 50: unvan = "Yönetici"
    return temiz_isim, unvan

def tahmini_mail_olustur(isim, domain):
    if not domain: return ""
    temiz_isim = unidecode(isim.lower()).replace(" ", ".")
    return f"{temiz_isim}@{domain} (Tahmini)"

def dataforseo_arama(sirket_adi, hedef_kelime, domain):
    query = f'site:linkedin.com/in ("Genel Müdür" OR "CEO" OR "Kurucu" OR "Müdür" OR "Manager" OR "Yönetici" OR "Direktör" OR "Şef") "{hedef_kelime}"'
    
    payload = [{
        "keyword": query,
        "location_code": 2792,
        "language_code": "tr",
        "depth": 15,
        "device": "desktop"
    }]
    
    print(f"\n[{sirket_adi}] Taranıyor...")
    
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.status_code != 200:
        print(f"  [-] HTTP Hata: {response.status_code}")
        print(f"  [-] Detay: {response.text}")
        return []
    
    data = response.json()
    if data.get("status_code") != 20000:
        print(f"  [-] API Hata: {data.get('status_message')}")
        return []
    
    tasks = data.get("tasks", [])
    if not tasks or tasks[0].get("status_code") != 20000:
        print(f"  -> [YOK] Sonuç dönmedi.")
        return []
    
    results = tasks[0].get("result", [])
    if not results:
        print(f"  -> [YOK] Sonuç dönmedi.")
        return []
    
    items = results[0].get("items", [])
    organic_items = [item for item in items if item.get("type") == "organic"]
    
    bulunanlar = []
    bulunan_isimler = set()
    
    for item in organic_items:
        baslik = item.get("title", "")
        link = item.get("url", "")
        snippet = item.get("description", "")
        
        baslik_lower = baslik.lower()
        snippet_lower = snippet.lower()
        
        sirket_geciyor = False
        hedef_3 = " ".join(hedef_kelime.split()[:3]) if len(hedef_kelime.split()) >= 3 else hedef_kelime
        if hedef_3 in baslik_lower or hedef_3 in snippet_lower:
            sirket_geciyor = True
        hedef_2 = " ".join(hedef_kelime.split()[:2]) if len(hedef_kelime.split()) >= 2 else hedef_kelime
        if not sirket_geciyor and not hedef_2.split()[0].isdigit():
            if hedef_2 in baslik_lower or hedef_2 in snippet_lower:
                sirket_geciyor = True
        if not sirket_geciyor:
            continue
        
        isim, linkedin_unvan = ismini_ve_unvanini_basliktan_cikar(baslik)
        if not isim:
            continue
        
        isim_temiz = unidecode(isim.lower())
        if isim_temiz in bulunan_isimler:
            continue
        
        if not any(k in linkedin_unvan.lower() or k in snippet_lower for k in KONTROL_KELIMELERI):
            continue
        
        bulunan_isimler.add(isim_temiz)
        email = tahmini_mail_olustur(isim, domain)
        
        print(f"  -> [BULUNDU] {linkedin_unvan}: {isim} | {link}")
        bulunanlar.append({
            'sirket_adi': sirket_adi,
            'departman': 'Yönetici',
            'isim': isim,
            'unvan': linkedin_unvan,
            'email': email,
            'linkedin_url': link
        })
    
    if not bulunanlar:
        print(f"  -> [YOK] Filtreleri geçen uygun bir yönetici adayı bulunamadı.")
    
    return bulunanlar

def main():
    if not LOGIN or not PASSWORD or "GIRIN" in (LOGIN or ""):
        print("[-] Lütfen .env dosyasına DataForSEO bilgilerinizi girin!")
        return
    
    print("[*] DataForSEO API Test Başlıyor...")
    
    # Bakiye kontrolü
    balance_url = "https://api.dataforseo.com/v3/appendix/user_data"
    balance_resp = requests.get(balance_url, headers=HEADERS)
    if balance_resp.status_code == 200:
        bdata = balance_resp.json()
        if bdata.get("tasks"):
            user_data = bdata["tasks"][0].get("result", [{}])[0]
            balance = user_data.get("money", {}).get("balance", "?")
            print(f"[💰] Hesap Bakiyesi: ${balance}")
    
    # master_sirketler.csv'den ilk 5 şirketi oku
    sirketler = []
    with open("master_sirketler.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('ad'):
                sirketler.append(row)
            if len(sirketler) >= 5:
                break
    
    print(f"[i] DataForSEO ile {len(sirketler)} şirket taranacak...\n")
    
    # CSV çıktı dosyası
    output_csv = "yoneticiler_dataforseo_test.csv"
    tum_bulunanlar = []
    
    for sirket in sirketler:
        orijinal_ad = sirket['ad']
        domain = sirket.get('domain', '')
        kisa_ad = sirket_adini_temizle(orijinal_ad)
        hedef = belirleyici_sirket_adi(kisa_ad)
        
        sonuclar = dataforseo_arama(orijinal_ad, hedef, domain)
        tum_bulunanlar.extend(sonuclar)
    
    # CSV'ye yaz
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['sirket_adi', 'departman', 'isim', 'unvan', 'email', 'linkedin_url'])
        writer.writeheader()
        writer.writerows(tum_bulunanlar)
    
    print(f"\n{'='*60}")
    print(f"  [+] Test tamamlandı!")
    print(f"  📊 {len(sirketler)} şirket tarandı, {len(tum_bulunanlar)} yönetici bulundu")
    print(f"  💾 Sonuçlar: {output_csv}")
    print(f"  💰 Toplam maliyet: ~${len(sirketler) * 0.002:.3f}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
