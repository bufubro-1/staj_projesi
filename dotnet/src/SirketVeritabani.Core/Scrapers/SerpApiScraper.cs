using SirketVeritabani.Core.Helpers;
using SirketVeritabani.Core.Models;
using SirketVeritabani.Core.Nlp;
using SirketVeritabani.Core.Search;
using SirketVeritabani.Core.SerpApi;

namespace SirketVeritabani.Core.Scrapers;

public sealed class SerpApiScraper
{
    private static readonly string[] KontrolKelimeleri =
    [
        "genel müdür", "ceo", "kurucu", "direktör", "manager", "müdür", "yönetici", "şef", "head"
    ];

    private readonly SerpApiBaslikParser _baslikParser;

    public SerpApiScraper()
    {
        var spacy = new SpacyEntityDogrulayici(ProjeYollari.SpacyEntityScript);
        _baslikParser = new SerpApiBaslikParser(spacy);
    }

    public async Task CalistirAsync(string inputCsv, int? limit = null, CancellationToken ct = default)
    {
        OrtamDegiskenleri.Yukle();
        var apiKey = OrtamDegiskenleri.Al("SERPAPI_KEY");

        if (string.IsNullOrWhiteSpace(apiKey) || apiKey == "buraya_api_anahtarinizi_yaziniz")
        {
            Console.WriteLine("[-] SERPAPI_KEY bulunamadı. .env dosyasına anahtarınızı ekleyin.");
            return;
        }

        if (!File.Exists(inputCsv))
        {
            Console.WriteLine($"[-] {inputCsv} bulunamadı!");
            return;
        }

        var sirketler = CsvYardimci.Oku<SirketKayit>(inputCsv)
            .Where(s => !string.IsNullOrWhiteSpace(s.Ad))
            .ToList();

        if (limit.HasValue)
            sirketler = sirketler.Take(limit.Value).ToList();

        Console.WriteLine($"[i] SerpAPI LinkedIn araması — {sirketler.Count} şirket\n");

        var kayitlar = new List<YoneticiFinalKayit>();

        using var client = new SerpApiClient(apiKey);

        foreach (var sirket in sirketler)
        {
            ct.ThrowIfCancellationRequested();
            var orijinalAd = sirket.Ad;
            var domain = sirket.Domain;
            var kisaAd = SerpApiSirketAdiHelper.Temizle(orijinalAd);
            var hedefKelime = SerpApiSirketAdiHelper.BelirleyiciAd(kisaAd);

            Console.WriteLine($"[{orijinalAd}] Taranıyor...");

            var sorgu =
                $"site:linkedin.com/in (\"Genel Müdür\" OR \"CEO\" OR \"Kurucu\" OR \"Müdür\" OR \"Manager\" OR \"Yönetici\" OR \"Direktör\" OR \"Şef\") \"{hedefKelime}\"";

            try
            {
                var sonuclar = await client.AraAsync(sorgu, ct);
                if (sonuclar.Count == 0)
                {
                    Console.WriteLine("  -> [YOK] Sonuç dönmedi.");
                    continue;
                }

                var bulunanIsimler = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                var bulunan = 0;

                foreach (var result in sonuclar)
                {
                    if (!SirketGeciyorMu(result, hedefKelime))
                        continue;

                    var (isim, unvan) = _baslikParser.IsimVeUnvanCikar(result.Baslik);
                    if (isim == null)
                        continue;

                    var isimAscii = AsciiYardimci.TurkceAscii(isim.ToLowerInvariant());
                    if (!bulunanIsimler.Add(isimAscii))
                        continue;

                    if (!KontrolKelimeleri.Any(k =>
                            unvan.Contains(k, StringComparison.OrdinalIgnoreCase) ||
                            result.Snippet.Contains(k, StringComparison.OrdinalIgnoreCase)))
                        continue;

                    var email = TahminiMailOlustur(isim, domain);
                    Console.WriteLine($"  -> [BULUNDU] {unvan}: {isim} | {result.Link}");

                    kayitlar.Add(new YoneticiFinalKayit
                    {
                        SirketAdi = orijinalAd,
                        Departman = "Yönetici",
                        Isim = isim,
                        Unvan = unvan,
                        Email = email,
                        LinkedinUrl = result.Link
                    });
                    bulunan++;
                }

                if (bulunan == 0)
                    Console.WriteLine("  -> [YOK] Filtreleri geçen uygun bir yönetici adayı bulunamadı.");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"  [-] Hata: {ex.Message}");
            }
        }

        CsvYardimci.Yaz(ProjeYollari.YoneticilerFinalCsv, kayitlar);
        Console.WriteLine($"\n[+] İşlem tamamlandı. {kayitlar.Count} kayıt → '{ProjeYollari.YoneticilerFinalCsv}'");
    }

    private static bool SirketGeciyorMu(SerpApiOrganikSonuc result, string hedefKelime)
    {
        var baslikLower = result.Baslik.ToLowerInvariant();
        var snippetLower = result.Snippet.ToLowerInvariant();

        var kelimeler = hedefKelime.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        var hedef3 = kelimeler.Length >= 3 ? string.Join(' ', kelimeler.Take(3)) : hedefKelime;
        if (baslikLower.Contains(hedef3) || snippetLower.Contains(hedef3))
            return true;

        var hedef2 = kelimeler.Length >= 2 ? string.Join(' ', kelimeler.Take(2)) : hedefKelime;
        var ilkKelime = kelimeler.FirstOrDefault() ?? string.Empty;
        if (!ilkKelime.All(char.IsDigit))
        {
            if (baslikLower.Contains(hedef2) || snippetLower.Contains(hedef2))
                return true;
        }

        return false;
    }

    private static string TahminiMailOlustur(string isim, string domain)
    {
        if (string.IsNullOrWhiteSpace(domain))
            return string.Empty;

        var temiz = AsciiYardimci.TurkceAscii(isim.ToLowerInvariant()).Replace(' ', '.');
        return $"{temiz}@{domain} (Tahmini)";
    }
}
