import time
import ssl
import urllib.request
ssl._create_default_https_context = ssl._create_unverified_context
import csv
import pickle
import os
import random
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

COOKIE_FILE = "linkedin_cookies.pkl"
INPUT_CSV = "master_sirketler.csv"
OUTPUT_CSV = "yoneticiler.csv"

def get_driver():
    """Undetected Chromedriver ayarlarını başlatır."""
    import undetected_chromedriver as uc
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled') # Bot tespiti zorlaştırır
    
    # Chrome yolunu zorunlu atama yerine otomatik bulmaya bırakalım
    try:
        # Önce sade haliyle deniyoruz (Binary yolunu kendi bulsun)
        driver = uc.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"Uyarı: UC otomatik başlatma başarısız oldu ({e}). Alternatif deneniyor...")
        
        try:
            # UC patlarsa standart Selenium ile devam et (Düşük riskli test için)
            std_options = webdriver.ChromeOptions()
            std_options.add_argument('--no-sandbox')
            std_options.add_argument('--disable-dev-shm-usage')
            std_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            std_options.add_experimental_option('useAutomationExtension', False)
            driver = webdriver.Chrome(options=std_options)
            return driver
        except Exception as e2:
            print(f"Hata: Standart Chrome da başlatılamadı: {e2}")
            return None

def save_cookies(driver, filepath):
    with open(filepath, 'wb') as file:
        pickle.dump(driver.get_cookies(), file)
    print(f"[+] Oturum çerezleri {filepath} dosyasına kaydedildi.")

def load_cookies(driver, filepath):
    if os.path.exists(filepath):
        with open(filepath, 'rb') as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    pass
        print(f"[+] Oturum çerezleri yüklendi.")
        return True
    return False

def linkedin_login(driver):
    """LinkedIn girişi yapar. Cookie yoksa kullanıcıdan giriş yapmasını bekler."""
    driver.get("https://www.linkedin.com/login")
    time.sleep(3)
    
    if load_cookies(driver, COOKIE_FILE):
        driver.refresh()
        time.sleep(5)
        # Login olmuş mu kontrol et
        if "feed" in driver.current_url or "mynetwork" in driver.current_url or len(driver.find_elements(By.CLASS_NAME, "global-nav__me")) > 0:
            print("[+] Otomatik giriş başarılı!")
            return True
        else:
            print("[-] Çerezlerin süresi dolmuş olabilir. Yeniden giriş gerekli.")
    
    print("\n" + "="*50)
    print(" LÜTFEN AÇILAN TARAYICIDA LİNKEDİN'E GİRİŞ YAPIN")
    print(" (Hesabınızın güvenliği için sahte/fake hesap kullanın!)")
    print("="*50 + "\n")
    
    # Kullanıcının manuel giriş yapmasını bekle (Max 3 dakika)
    wait_time = 180
    start_time = time.time()
    
    while time.time() - start_time < wait_time:
        if "feed" in driver.current_url or len(driver.find_elements(By.CLASS_NAME, "global-nav__me")) > 0:
            print("\n[+] Başarıyla giriş yapıldı!")
            time.sleep(5) # Sayfanın tam yüklenmesini bekle
            save_cookies(driver, COOKIE_FILE)
            return True
        time.sleep(2)
        print(".", end="", flush=True)
        
    print("\n[-] Giriş süresi doldu. Lütfen scripti tekrar çalıştırın.")
    return False

def human_delay(min_s=3, max_s=8):
    """Banlanmamak için rastgele bekleme süresi"""
    time.sleep(random.uniform(min_s, max_s))

def scrape_linkedin():
    # Şirketleri oku
    sirketler = []
    if os.path.exists(INPUT_CSV):
        with open(INPUT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            sirketler = list(reader)
    else:
        print(f"[-] {INPUT_CSV} bulunamadı!")
        return

    # Sadece ilk 5 şirketi test edelim (Güvenlik için)
    sirketler = sirketler[:5]
    print(f"[i] Toplam {len(sirketler)} şirket aranacak.")

    driver = get_driver()
    
    if not linkedin_login(driver):
        driver.quit()
        return

    # Çıktı dosyasını hazırla
    file_exists = os.path.exists(OUTPUT_CSV)
    with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['sirket_adi', 'domain', 'isim', 'unvan', 'profil_linki'])
        if not file_exists:
            writer.writeheader()
            
        for sirket in sirketler:
            sirket_adi = sirket.get('ad', '')
            domain = sirket.get('domain', '')
            
            if not sirket_adi:
                continue
                
            print(f"\n[*] Aranıyor: {sirket_adi}")
            
            # İnsan gibi arama URL'sine git
            # Hedef: Genel Müdür, Lojistik Müdürü, Operasyon Müdürü, CEO vs.
            search_url = f"https://www.linkedin.com/search/results/people/?keywords=%22{sirket_adi}%22%20%22Genel%20Müdür%22"
            driver.get(search_url)
            human_delay(5, 10)
            
            # Sayfayı biraz aşağı kaydır (İnsan taklidi)
            driver.execute_script("window.scrollTo(0, 500);")
            human_delay(2, 4)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Arama sonuçlarındaki profilleri bul (LinkedIn yapısı sürekli değişir, en genel olanı bulalım)
            # Genellikle .reusable-search__result-container class'ı altındadır
            results = soup.find_all('li', class_='reusable-search__result-container')
            
            kisi_sayisi = 0
            for res in results[:3]: # Sadece ilk 3 kişiyi al (Yönetici genelde üsttedir)
                # İsim ve profil linki
                name_tag = res.find('span', dir='ltr')
                link_tag = res.find('a', class_='app-aware-link')
                
                # Unvan
                title_tag = res.find('div', class_='entity-result__primary-subtitle')
                
                if name_tag and title_tag:
                    isim = name_tag.get_text(strip=True)
                    unvan = title_tag.get_text(strip=True)
                    profil_linki = link_tag['href'].split('?')[0] if link_tag else ''
                    
                    writer.writerow({
                        'sirket_adi': sirket_adi,
                        'domain': domain,
                        'isim': isim,
                        'unvan': unvan,
                        'profil_linki': profil_linki
                    })
                    print(f"  -> Bulundu: {isim} - {unvan}")
                    kisi_sayisi += 1
            
            if kisi_sayisi == 0:
                print("  -> Uygun kişi bulunamadı veya bağlantı derecesi dışı (LinkedIn kısıtlaması).")
                
            # Şirketler arası uzun bekleme
            human_delay(10, 20)

    print(f"\n[+] İşlem tamamlandı. Sonuçlar '{OUTPUT_CSV}' dosyasına eklendi.")
    driver.quit()

if __name__ == "__main__":
    scrape_linkedin()
