# staj_projesi

Lojistik şirket veritabanı — Python ve .NET ayrı klasörlerde.

## Klasör yapısı

```
sirket-veritabani/
├── python/                 # Python scrapers
├── dotnet/                 # .NET CLI
├── master_sirketler.csv    # Paylaşılan CSV verileri (repo kökü)
├── und_sirketler.csv
└── .env                    # API anahtarları (repo kökü)
```

## .NET

```bash
dotnet run --project dotnet/src/SirketVeritabani.Cli -- merge
dotnet run --project dotnet/src/SirketVeritabani.Cli -- serpapi --limit 5
```

→ [dotnet/README.md](dotnet/README.md)

## Python

```bash
python python/scrapers/merge_and_dedup.py
```

→ [python/README.md](python/README.md)
