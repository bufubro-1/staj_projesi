# Sirket Veritabani — .NET CLI

CSV dosyaları **repo kök dizininde** (`../master_sirketler.csv`).

## Kurulum

```bash
cd dotnet
dotnet restore
dotnet build
```

`.env` dosyasını **repo köküne** koyun (`SERPAPI_KEY=...`).

## Komutlar (repo kökünden)

```bash
dotnet run --project dotnet/src/SirketVeritabani.Cli -- merge
dotnet run --project dotnet/src/SirketVeritabani.Cli -- website --limit 10
dotnet run --project dotnet/src/SirketVeritabani.Cli -- serpapi --limit 5
dotnet run --project dotnet/src/SirketVeritabani.Cli -- ddg --limit 5
```

| Komut | Açıklama | Çıktı |
|-------|----------|-------|
| `und` | UND üye listesi | `und_sirketler.csv` |
| `utikad` | UTIKAD üye listesi | `sirketler.csv` |
| `merge` | CSV birleştirme | `master_sirketler.csv` |
| `website` | Site crawl → yönetici | `yoneticiler.csv` |
| `serpapi` | LinkedIn snippet arama | `yoneticiler_final.csv` |
| `ddg` | DuckDuckGo domain arama | `ddg_sonuclar.csv` |

## spaCy köprüleri (isteğe bağlı)

```bash
pip install spacy
python -m spacy download xx_ent_wiki_sm
```

- `dotnet/tools/spacy_validate.py` — website isim filtresi
- `dotnet/tools/spacy_entity_check.py` — SerpAPI başlık PER/ORG kontrolü

## Python karşılıkları

→ [../python/README.md](../python/README.md)
