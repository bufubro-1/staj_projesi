import csv
import time
from scrapers.website_scraper import scrape_company_website

def run_test():
    # Önceden taranıp 'BULUNDU' olarak işaretlenenleri al
    try:
        with open('taranan_sirketler.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            test_sirketler = [row for row in reader if row.get('durum') == 'BULUNDU']
    except FileNotFoundError:
        print("[-] taranan_sirketler.csv bulunamadı!")
        return
        
    print(f"\n[i] Toplam {len(test_sirketler)} başarılı şirket yeniden (düzeltilmiş filtrelerle) test edilecek...\n")
    
    # Test sonuçlarını ayrı bir dosyaya yazalım ki asıl veriyi bozmasın
    with open('yoneticiler_test.csv', 'w', newline='', encoding='utf-8') as out_f:
        writer = csv.DictWriter(out_f, fieldnames=['sirket_adi', 'domain', 'isim', 'unvan', 'email', 'kaynak'])
        writer.writeheader()
        
        for sirket in test_sirketler:
            domain = sirket['domain']
            ad = sirket['ad']
            
            print(f"[*] Test ediliyor: {domain}")
            kisiler, mailler, erisilebildi = scrape_company_website(domain)
            
            if kisiler:
                for kisi in kisiler:
                    print(f"  -> İSİM: {kisi['isim']} | UNVAN: {kisi['unvan']}")
                    writer.writerow({
                        'sirket_adi': ad, 'domain': domain, 'isim': kisi['isim'], 
                        'unvan': kisi['unvan'], 'email': '', 'kaynak': 'websitesi_test'
                    })
                out_f.flush()  # Her şirketten sonra diske yaz!
                    
            print("-" * 50)
            
if __name__ == "__main__":
    run_test()
