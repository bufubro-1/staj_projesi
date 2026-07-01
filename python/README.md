# Python scrapers

CSV dosyaları **repo kök dizininde** kalır (`../master_sirketler.csv`).

## Kurulum

```bash
cd python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download xx_ent_wiki_sm
cp .env.example ../.env   # SERPAPI_KEY vb.
```

## Çalıştırma (repo kökünden)

```bash
cd ..   # sirket-veritabani/
python python/scrapers/und_scraper.py
python python/scrapers/utikad_scraper.py
python python/scrapers/merge_and_dedup.py
python python/scrapers/final_serpapi_scraper.py
```

## Yapı

```
python/
├── scrapers/          # Kazıma scriptleri
├── database/          # SQLAlchemy (isteğe bağlı)
├── requirements.txt
├── .env.example
└── proje_kok.py       # CSV yolları → repo kökü
```

.NET karşılıkları için: [`../dotnet/README.md`](../dotnet/README.md)
