import os
import csv
import re
import sys
import spacy
from pathlib import Path
from unidecode import unidecode
from dotenv import load_dotenv
from serpapi import GoogleSearch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from proje_kok import csv_yol, proje_kok

load_dotenv(proje_kok() / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
API_KEY = os.getenv("SERPAPI_KEY")

try:
    nlp = spacy.load("xx_ent_wiki_sm")
    print("[*] Spacy modeli yüklendi (Çift Güvenlik).")
except Exception:
    print("[-] Spacy yüklenemedi.")
    exit(1)

INPUT_CSV = str(csv_yol("master_sirketler.csv"))
OUTPUT_CSV = str(csv_yol("yoneticiler_final.csv"))

KONTROL_KELIMELERI = ["genel müdür", "ceo", "kurucu", "direktör", "manager", "müdür", "yönetici", "şef", "head"]

GECERSIZ_KELIMELER = {
    'lojistik', 'logistics', 'taşımacılık', 'transport', 'nakliyat', 'kargo',
    'gümrük', 'customs', 'global', 'uluslararası', 'international',
    'sanayi', 'ticaret', 'şirketi', 'ltd', 'şti', 'a.ş', 'aş', 'hizmetleri',
    'linkedin', 'profil'
}

def sirket_adini_temizle(ad):
    # Şirket isminin içindeki sektörel ve yasal uzantıları silip 'Core Brand Name'i bulur
    ad_lower = ad.lower()
    
    silinecekler = [
        "sanayi", "ticaret", "hizmetleri", "ltd.", "şti.", "ltd", "şti", "a.ş.", "aş.", "a.s.", "aş",
        "tic.", "san.", "ve", "danışmanlık", "müşavirliği", "yayıncılık", "turizm",
        "dış", "iç", "ithalat", "ihracat", "pazarlama", "uluslararası", "global",
        "nakliyat", "taşımacılık", "gıda", "dan.", "lojistik", "tic", "san", "dan"
    ]
    
    # "Lojistik" kelimesini silip silmemeye karar ver: 
    # Eğer "3K Lojistik" ise lojistik kalsın. Ama uzunsa gitsin. (Bunu basitleştirelim, lojistik kalsın ama diğerleri gitsin)
    silinecekler.remove("lojistik")
    
    kelimeler = ad_lower.split()
    yeni_kelimeler = []
    
    for k in kelimeler:
        k_temiz = k.strip(".,;:|/'\"-")
        if k_temiz not in silinecekler:
            yeni_kelimeler.append(k_temiz)
            
    # Temizlenmiş hali çok kısaysa (1 kelime) orijinali (veya ilk 2 kelimeyi) kullanmak daha güvenlidir
    temiz_ad = " ".join(yeni_kelimeler)
    if not temiz_ad or len(temiz_ad) < 2:
        return ad.split()[0] if ad.split() else ad
        
    return temiz_ad.title()

def belirleyici_sirket_adi(kisa_ad):
    # Temizlenmiş ismin sadece ilk 2 kelimesini 'Core Brand' olarak kabul et.
    # Örn: "9 ekim gümrük lojistik" -> "9 ekim"
    # Örn: "2h gümrük lojistik" -> "2h gümrük"
    kelimeler = kisa_ad.split()
    return " ".join(kelimeler[:2]).lower() if len(kelimeler) >= 2 else kisa_ad.lower()

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
        
    # Unvan genelde 2. parçada yer alır (İsim - Unvan - Şirket)
    unvan = parcalar[1].strip() if len(parcalar) > 1 else "Yönetici"
    
    # Yarıda kesilmiş ve kirli unvanları temizleme (Cosmetic Cleanup)
    unvan = unvan.replace("...", "").replace("..", "").strip()
    unvan = re.sub(r'(?i)\s+at\s+.*$', '', unvan)       # " at CompanyName" kısmını at
    unvan = re.sub(r'(?i)\s+at$', '', unvan)           # Sonda kalan " at" kelimesini at
    unvan = re.sub(r'\s+@\s+.*$', '', unvan)           # " @ CompanyName" kısmını at
    unvan = re.sub(r'^.*? şirketinde ', '', unvan)     # "X şirketinde Y Müdürü" -> "Y Müdürü"
    unvan = re.sub(r'(?i)\s+(and|ve|&)$', '', unvan)   # Sonda kalan bağlaçları sil
    unvan = unvan.strip(" -/,|")
    
    # Unvanın gerçekten bir unvan olup olmadığını kontrol et (Şirket adı veya Üniversite adı çıkmasını engelle)
    unvan_kelimeleri = ["müdür", "manager", "ceo", "kurucu", "direktör", "şef", "head", "uzman", "specialist", "coordinator", "president", "vp", "chief", "smmm", "analiz", "sales", "operation", "ik", "hr", "yönetici"]
    is_valid = any(k in unvan.lower() for k in unvan_kelimeleri)
    
    if not is_valid:
        # Belki 3. parçadadır (İsim - Şirket - Unvan)
        if len(parcalar) > 2:
            unvan_2 = parcalar[2].strip()
            if any(k in unvan_2.lower() for k in unvan_kelimeleri):
                unvan = unvan_2
            else:
                unvan = "Yönetici"
        else:
            unvan = "Yönetici"
            
    # Eğer çok uzunsa (LinkedIn vs karıştıysa) kısalt
    if len(unvan) > 50: unvan = "Yönetici"
    
    return temiz_isim, unvan

def tahmini_mail_olustur(isim, domain):
    if not domain: return ""
    temiz_isim = unidecode(isim.lower()).replace(" ", ".")
    return f"{temiz_isim}@{domain} (Tahmini)"

def belirleyici_sirket_adi(kisa_ad):
    # Google'da arama yaparken çok uzun stringleri engellemek için, temiz ismin en fazla ilk 3 kelimesini al (Örn: "9 Ekim Gümrük")
    kelimeler = kisa_ad.split()
    return " ".join(kelimeler[:3]).lower() if len(kelimeler) >= 3 else kisa_ad.lower()

def main():
    if not API_KEY or API_KEY == "buraya_api_anahtarinizi_yaziniz":
        print("[-] Lütfen API bilginizi giriniz!")
        return

    sirketler = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        sirketler = [row for row in reader if row.get('ad')]
        
    basarili_sirketler = [
        "2H Gümrük ve Lojistik Hizmetleri Tic. Ltd. Şti.",
        "3K Lojistik Hizmetleri Tic. Ltd. Şti.",
        "AB Gümrük Müşavirliği ve Danışmanlık A.Ş.",
        "Access World Turkey Lojistik Depolama A.Ş.",
        "Ada Global Lojistik Sanayi ve Ticaret Ltd. Şti.",
        "Agila Lojistik A.Ş.",
        "AIT Worldwide Logistics Transport Ltd. Şti."
    ]
    sirketler = [s for s in sirketler if s['ad'] in basarili_sirketler]
    print(f"[i] Hibrit Arama (Kapsamlı Filtre) başlatılıyor... (Sadece başarılı {len(sirketler)} şirket)")
    
    # Her çalıştığında test amaçlı dosyayı sıfırlıyoruz, böylece 10 şirketin 3 departmanı alt alta derli toplu duracak.
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as out_f:
        writer = csv.DictWriter(out_f, fieldnames=['sirket_adi', 'departman', 'isim', 'unvan', 'email', 'linkedin_url'])
        writer.writeheader()
        
        for sirket in sirketler:
            orijinal_ad = sirket['ad']
            domain = sirket.get('domain', '')
            kisa_ad = sirket_adini_temizle(orijinal_ad)
            hedef_sirket_kelimesi = belirleyici_sirket_adi(kisa_ad)
            
            print(f"\n[{orijinal_ad}] Taranıyor...")
            
            # Tüm yöneticiler için tek bir güçlü arama
            query = f'site:linkedin.com/in ("Genel Müdür" OR "CEO" OR "Kurucu" OR "Müdür" OR "Manager" OR "Yönetici" OR "Direktör" OR "Şef") "{hedef_sirket_kelimesi}"'
            
            params = {
              "engine": "google",
              "q": query,
              "gl": "tr",
              "hl": "tr",
              "api_key": API_KEY,
              "num": 15
            }
            
            try:
                search = GoogleSearch(params)
                results = search.get_dict()
                
                if "organic_results" in results:
                    bulunanlar = 0
                    bulunan_isimler = set()
                    
                    for result in results["organic_results"]:
                        baslik = result.get('title', '')
                        link = result.get('link', '')
                        snippet = result.get('snippet', '')
                        
                        baslik_lower = baslik.lower()
                        snippet_lower = snippet.lower()
                        
                        sirket_geciyor = False
                        
                        # Kontrol 1: Temizlenmiş ismin ilk 3 kelimesi geçiyor mu? (Örn: "9 ekim gümrük")
                        hedef_3 = " ".join(hedef_sirket_kelimesi.split()[:3]) if len(hedef_sirket_kelimesi.split()) >=3 else hedef_sirket_kelimesi
                        if hedef_3 in baslik_lower or hedef_3 in snippet_lower:
                            sirket_geciyor = True
                            
                        # Kontrol 2: Temizlenmiş ismin ilk 2 kelimesi geçiyor mu? (Örn: "2h gümrük", "3k lojistik")
                        hedef_2 = " ".join(hedef_sirket_kelimesi.split()[:2]) if len(hedef_sirket_kelimesi.split()) >=2 else hedef_sirket_kelimesi
                        if not sirket_geciyor and not hedef_2.split()[0].isdigit():
                            if hedef_2 in baslik_lower or hedef_2 in snippet_lower:
                                sirket_geciyor = True

                        if not sirket_geciyor:
                            continue
                            
                        # Filtre 2: Başlıktaki ismi ve unvanı Spacy + Regex ile analiz et
                        isim, linkedin_unvan = ismini_ve_unvanini_basliktan_cikar(baslik)
                        if not isim:
                            continue
                            
                        # Tekrar Kontrolü: Aynı kişiyi (İngilizce profili vs) 2 kez eklememek için
                        isim_temiz = unidecode(isim.lower())
                        if isim_temiz in bulunan_isimler:
                            continue
                            
                        # Filtre 3: Yanlışlıkla alakasız profilleri almamak için temel unvan kontrolü (isteğe bağlı ama güvenli)
                        if not any(k in linkedin_unvan.lower() or k in snippet_lower for k in KONTROL_KELIMELERI):
                            continue
                            
                        # TÜM FİLTRELERİ GEÇTİ! Doğru kişiyi bulduk.
                        bulunan_isimler.add(isim_temiz)
                        email = tahmini_mail_olustur(isim, domain)
                        
                        print(f"  -> [BULUNDU] {linkedin_unvan}: {isim} | {link}")
                        writer.writerow({
                            'sirket_adi': orijinal_ad,
                            'departman': 'Yönetici',
                            'isim': isim,
                            'unvan': linkedin_unvan,
                            'email': email,
                            'linkedin_url': link
                        })
                        out_f.flush()
                        bulunanlar += 1
                        
                    if bulunanlar == 0:
                        print(f"  -> [YOK] Filtreleri geçen uygun bir yönetici adayı bulunamadı.")
                else:
                    print(f"  -> [YOK] Sonuç dönmedi.")
                    
            except Exception as e:
                print(f"  [-] Hata: {e}")
                    
    print(f"\n[+] İşlem tamamlandı. Sonuçlar {OUTPUT_CSV} dosyasına kaydedildi.")

if __name__ == "__main__":
    main()
