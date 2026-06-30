import csv
import re

def clean_domain(url):
    if not url:
        return None
    url = url.lower().strip()
    url = re.sub(r'^https?:\/\/', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.split('/')[0]
    if len(url) < 3 or '.' not in url:
        return None
    return url

def clean_company_name(name):
    """Şirket adını küçük harfe çevirir, A.Ş., Ltd. Şti. gibi ekleri ve boşlukları atar (Kıyaslama için)."""
    if not name:
        return ""
    name = name.lower()
    name = name.replace("i̇", "i").replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
    # A.Ş. ve Ltd. gibi ekleri temizle
    name = re.sub(r'\ba\.ş\.\b|\bas\b|\banonim şirketi\b', '', name)
    name = re.sub(r'\bltd\.\s*şti\.\b|\blimited şirketi\b|\btic\.\b|\bsan\.\b|\bve\b', '', name)
    # Noktalama ve boşlukları at
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

def merge_datasets():
    master_dict = {}
    
    # UTİKAD Verilerini Oku
    try:
        with open('sirketler.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                domain = row.get('domain')
                if not domain: continue
                
                master_dict[domain] = {
                    'ad': row.get('ad', ''),
                    'domain': domain,
                    'email': row.get('email', ''),
                    'telefon': row.get('telefon', ''),
                    'sehir': row.get('sehir', ''),
                    'kaynak': ['UTIKAD']
                }
    except FileNotFoundError:
        print("sirketler.csv (UTİKAD) bulunamadı.")
        
    # UND Verilerini Oku
    try:
        with open('und_sirketler.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                domain = row.get('domain')
                ad = row.get('ad', '')
                
                if domain and domain in master_dict:
                    # Kesişen domain bulundu!
                    if 'UND' not in master_dict[domain]['kaynak']:
                        master_dict[domain]['kaynak'].append('UND')
                    # Eksik verileri doldur
                    if not master_dict[domain]['email'] and row.get('email'): master_dict[domain]['email'] = row.get('email')
                    if not master_dict[domain]['telefon'] and row.get('telefon'): master_dict[domain]['telefon'] = row.get('telefon')
                    if not master_dict[domain]['sehir'] and row.get('sehir'): master_dict[domain]['sehir'] = row.get('sehir')
                
                elif domain:
                    # Sadece UND'de olan domain
                    master_dict[domain] = {
                        'ad': ad,
                        'domain': domain,
                        'email': row.get('email', ''),
                        'telefon': row.get('telefon', ''),
                        'sehir': row.get('sehir', ''),
                        'kaynak': ['UND']
                    }
                else:
                    # Domain yoksa isme göre (fuzzy/clean name) eşleştirme dene
                    clean_target = clean_company_name(ad)
                    eslesti = False
                    for m_domain, m_data in master_dict.items():
                        if clean_company_name(m_data['ad']) == clean_target:
                            if 'UND' not in master_dict[m_domain]['kaynak']:
                                master_dict[m_domain]['kaynak'].append('UND')
                            eslesti = True
                            break
                    
                    if not eslesti:
                        # Tamamen yeni ve domainsiz şirket (Şimdilik CSV'ye domiansiz olarak ekle)
                        fake_domain = f"nodomain_{len(master_dict)}"
                        master_dict[fake_domain] = {
                            'ad': ad,
                            'domain': '',
                            'email': row.get('email', ''),
                            'telefon': row.get('telefon', ''),
                            'sehir': row.get('sehir', ''),
                            'kaynak': ['UND']
                        }
    except FileNotFoundError:
        print("und_sirketler.csv bulunamadı.")

    # Master CSV Olarak Yaz
    with open('master_sirketler.csv', mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['ad', 'domain', 'email', 'telefon', 'sehir', 'kaynak'])
        writer.writeheader()
        for data in master_dict.values():
            data['kaynak'] = " + ".join(data['kaynak'])
            writer.writerow(data)
            
    print(f"Toplam {len(master_dict)} benzersiz şirket 'master_sirketler.csv' dosyasında birleştirildi.")
    
    # Çakışma İstatistikleri
    sadece_utikad = sum(1 for d in master_dict.values() if d['kaynak'] == 'UTIKAD')
    sadece_und = sum(1 for d in master_dict.values() if d['kaynak'] == 'UND')
    ortak = sum(1 for d in master_dict.values() if 'UTIKAD + UND' in d['kaynak'] or 'UND + UTIKAD' in d['kaynak'])
    
    print(f"Sadece UTİKAD: {sadece_utikad}")
    print(f"Sadece UND: {sadece_und}")
    print(f"Ortak (Her iki derneğe üye): {ortak}")

if __name__ == "__main__":
    merge_datasets()
