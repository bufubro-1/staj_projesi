using SirketVeritabani.Core.Helpers;
using SirketVeritabani.Core.Models;
using SirketVeritabani.Core.Search;

namespace SirketVeritabani.Core.Scrapers;

public sealed class DdgDiscoveryScraper
{
    private readonly DuckDuckGoArama _ddg = new();
    private readonly Random _random = new();

    public async Task CalistirAsync(
        string inputCsv,
        int? limit = null,
        bool sadeceEksikDomain = false,
        CancellationToken ct = default)
    {
        if (!File.Exists(inputCsv))
        {
            Console.WriteLine($"[-] {inputCsv} bulunamadı!");
            return;
        }

        var sirketler = CsvYardimci.Oku<SirketKayit>(inputCsv).ToList();

        if (sadeceEksikDomain)
            sirketler = sirketler.Where(s => string.IsNullOrWhiteSpace(s.Domain)).ToList();

        if (limit.HasValue)
            sirketler = sirketler.Take(limit.Value).ToList();

        if (sirketler.Count == 0)
        {
            Console.WriteLine("[!] Aranacak şirket bulunamadı.");
            return;
        }

        Console.WriteLine($"[i] DuckDuckGo ile {sirketler.Count} şirket aranacak...\n");

        var sonuclar = new List<DdgSonucKayit>();
        var i = 0;

        foreach (var sirket in sirketler)
        {
            ct.ThrowIfCancellationRequested();
            i++;
            Console.WriteLine($"[{i}/{sirketler.Count}] {sirket.Ad}");

            var sorgular = DuckDuckGoArama.SorguOlustur(sirket.Ad).ToList();
            var (url, domain, kullanilanSorgu) = await _ddg.IlkGecerliSonucBulAsync(sorgular, ct);

            string durum;
            if (domain == null)
            {
                durum = "BULUNAMADI";
                Console.WriteLine($"  -> Sonuç yok (sorgu: {kullanilanSorgu})");
            }
            else if (!string.IsNullOrWhiteSpace(sirket.Domain)
                     && domain.Equals(sirket.Domain, StringComparison.OrdinalIgnoreCase))
            {
                durum = "ESLESME";
                Console.WriteLine($"  -> Eşleşme: {domain} (sorgu: {kullanilanSorgu})");
            }
            else if (!string.IsNullOrWhiteSpace(sirket.Domain))
            {
                durum = "FARKLI";
                Console.WriteLine($"  -> Farklı: mevcut={sirket.Domain}, bulunan={domain}");
            }
            else
            {
                durum = "YENI";
                Console.WriteLine($"  -> Yeni domain: {domain} (sorgu: {kullanilanSorgu})");
            }

            sonuclar.Add(new DdgSonucKayit
            {
                Ad = sirket.Ad,
                MevcutDomain = sirket.Domain,
                BulunanDomain = domain ?? string.Empty,
                BulunanUrl = url ?? string.Empty,
                Sorgu = kullanilanSorgu,
                Sira = 1,
                Durum = durum
            });

            if (i < sirketler.Count)
                await Task.Delay(TimeSpan.FromMilliseconds(_random.Next(2000, 4000)), ct);
        }

        CsvYardimci.Yaz(ProjeYollari.DdgSonuclarCsv, sonuclar);

        var bulunan = sonuclar.Count(s => s.Durum != "BULUNAMADI");
        Console.WriteLine($"\n[+] {bulunan}/{sonuclar.Count} şirket için sonuç bulundu.");
        Console.WriteLine($"[+] Detay: '{ProjeYollari.DdgSonuclarCsv}'");
    }
}
