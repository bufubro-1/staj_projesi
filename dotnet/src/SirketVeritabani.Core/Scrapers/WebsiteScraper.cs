using System.Text.RegularExpressions;
using HtmlAgilityPack;
using SirketVeritabani.Core.Helpers;
using SirketVeritabani.Core.Http;
using SirketVeritabani.Core.Models;
using SirketVeritabani.Core.Nlp;

namespace SirketVeritabani.Core.Scrapers;

public sealed partial class WebsiteScraper
{
    private static readonly string[] YonetimSayfalari =
    [
        "/hakkimizda", "/hakkinda", "/about", "/about-us",
        "/ekibimiz", "/ekip", "/team", "/our-team",
        "/yonetim", "/yonetim-kurulu", "/management", "/board",
        "/kurumsal", "/corporate", "/biz-kimiz",
        "/iletisim", "/contact", "/contact-us",
        "/kadromuz", "/organizasyon"
    ];

    private static readonly Regex GenelMailFiltre = new(
        @"^(info|destek|support|contact|iletisim|muhasebe|finans|sales|satis|halkla|hr|ik|kvkk|bilgi|admin|webmaster|noreply|no-reply)@",
        RegexOptions.IgnoreCase | RegexOptions.Compiled);

    private readonly ScraperHttpClient _http = new();
    private readonly KisiCikarici _kisiCikarici;
    private readonly Random _random = new();

    public WebsiteScraper()
    {
        var spacy = new SpacyDogrulayici(ProjeYollari.SpacyValidatorScript);
        _kisiCikarici = new KisiCikarici(spacy);
    }

    public async Task CalistirAsync(string inputCsv, int? limit = null, CancellationToken ct = default)
    {
        if (!File.Exists(inputCsv))
        {
            Console.WriteLine($"[-] {inputCsv} bulunamadı!");
            return;
        }

        var sirketler = CsvYardimci.Oku<SirketKayit>(inputCsv)
            .Where(s => !string.IsNullOrWhiteSpace(s.Domain))
            .ToList();

        if (limit.HasValue)
            sirketler = sirketler.Take(limit.Value).ToList();

        var erisilmezSiteler = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        if (File.Exists(ProjeYollari.TarananSirketlerCsv))
        {
            foreach (var row in CsvYardimci.Oku<TarananSirketKayit>(ProjeYollari.TarananSirketlerCsv))
            {
                if (row.Durum.Equals("ERISILEMEDI", StringComparison.OrdinalIgnoreCase))
                    erisilmezSiteler.Add(row.Domain);
            }

            if (erisilmezSiteler.Count > 0)
                Console.WriteLine($"[*] Önceki taramada erişilemeyen {erisilmezSiteler.Count} site atlanacak.");
        }

        Console.WriteLine($"[i] Toplam {sirketler.Count} şirketin websitesi taranacak...");
        Console.WriteLine($"[i] Her şirket için ~{YonetimSayfalari.Length} farklı sayfa denenecek.\n");

        var yoneticiler = new List<YoneticiKayit>();
        var taranan = new List<TarananSirketKayit>();
        var bulunduSayisi = 0;
        var bulunamadiSayisi = 0;
        var erisimYokSayisi = 0;

        var i = 0;
        foreach (var sirket in sirketler)
        {
            ct.ThrowIfCancellationRequested();
            i++;
            Console.WriteLine($"[{i}/{sirketler.Count}] {sirket.Ad} ({sirket.Domain})");

            if (erisilmezSiteler.Contains(sirket.Domain))
            {
                erisimYokSayisi++;
                taranan.Add(new TarananSirketKayit
                {
                    Ad = sirket.Ad,
                    Domain = sirket.Domain,
                    Durum = "ERISILEMEDI",
                    BulunanKisi = 0,
                    BulunanMail = 0
                });
                continue;
            }

            var (kisiler, mailler, erisilebildi) = await SirketSitesiniTaraAsync(sirket.Domain, ct);

            if (!erisilebildi)
            {
                erisimYokSayisi++;
                taranan.Add(new TarananSirketKayit
                {
                    Ad = sirket.Ad,
                    Domain = sirket.Domain,
                    Durum = "ERİŞİLEMEDİ",
                    BulunanKisi = 0,
                    BulunanMail = 0
                });
                continue;
            }

            string durum;
            if (kisiler.Count > 0)
            {
                bulunduSayisi++;
                durum = "BULUNDU";

                foreach (var kisi in kisiler)
                {
                    yoneticiler.Add(new YoneticiKayit
                    {
                        SirketAdi = sirket.Ad,
                        Domain = sirket.Domain,
                        Isim = kisi.Isim,
                        Unvan = kisi.Unvan,
                        Email = string.Empty,
                        Kaynak = "websitesi"
                    });
                }
            }
            else
            {
                bulunamadiSayisi++;
                durum = "BULUNAMADI";
            }

            taranan.Add(new TarananSirketKayit
            {
                Ad = sirket.Ad,
                Domain = sirket.Domain,
                Durum = durum,
                BulunanKisi = kisiler.Count,
                BulunanMail = mailler.Count
            });

            await Task.Delay(TimeSpan.FromMilliseconds(_random.Next(500, 1500)), ct);
        }

        CsvYardimci.Yaz(ProjeYollari.YoneticilerCsv, yoneticiler);
        CsvYardimci.Yaz(ProjeYollari.TarananSirketlerCsv, taranan);

        Console.WriteLine($"\n{new string('=', 50)}");
        Console.WriteLine("İşlem Tamamlandı!");
        Console.WriteLine($"{new string('=', 50)}");
        Console.WriteLine($"Yönetici/Mail Bulunan Şirket : {bulunduSayisi}");
        Console.WriteLine($"Bulunamayan Şirket           : {bulunamadiSayisi}");
        Console.WriteLine($"Erişilemeyen Site            : {erisimYokSayisi}");
        Console.WriteLine($"Toplam                       : {sirketler.Count}");
        Console.WriteLine($"\n[+] Sonuçlar '{ProjeYollari.YoneticilerCsv}' dosyasına kaydedildi.");
        Console.WriteLine($"[+] Tarama raporu '{ProjeYollari.TarananSirketlerCsv}' dosyasına kaydedildi.");
    }

    private async Task<(List<KisiCikarim> Kisiler, List<string> Mailler, bool Erisilebildi)> SirketSitesiniTaraAsync(
        string domain,
        CancellationToken ct)
    {
        var bulunanKisiler = new List<KisiCikarim>();
        var bulunanMailler = new List<string>();

        var baseUrls = new[]
        {
            $"https://www.{domain}",
            $"https://{domain}",
            $"http://www.{domain}",
            $"http://{domain}"
        };

        string? calisanUrl = null;
        foreach (var baseUrl in baseUrls)
        {
            var html = await _http.SayfaAlAsync(baseUrl, ct);
            if (html == null)
                continue;

            calisanUrl = baseUrl;
            bulunanMailler.AddRange(EmailCikar(html, domain));
            break;
        }

        if (calisanUrl == null)
            return ([], [], false);

        foreach (var sayfaYolu in YonetimSayfalari)
        {
            ct.ThrowIfCancellationRequested();
            var url = calisanUrl + sayfaYolu;
            var html = await _http.SayfaAlAsync(url, ct);
            if (html == null)
                continue;

            var doc = new HtmlDocument();
            doc.LoadHtml(html);

            bulunanMailler.AddRange(EmailCikar(html, domain));
            bulunanKisiler.AddRange(_kisiCikarici.Cikar(doc));

            await Task.Delay(TimeSpan.FromMilliseconds(_random.Next(300, 800)), ct);
        }

        var tekilKisiler = bulunanKisiler
            .GroupBy(k => k.Isim.ToLowerInvariant().Replace(" ", string.Empty))
            .Select(g => g.First())
            .ToList();

        var tekilMailler = bulunanMailler.Distinct(StringComparer.OrdinalIgnoreCase).ToList();

        return (tekilKisiler, tekilMailler, true);
    }

    private static List<string> EmailCikar(string html, string domain)
    {
        var mailler = EmailRegex().Matches(html)
            .Select(m => m.Value.ToLowerInvariant().Trim())
            .Where(m => m.Contains(domain, StringComparison.OrdinalIgnoreCase))
            .Where(m => !GenelMailFiltre.IsMatch(m))
            .Distinct()
            .ToList();

        return mailler;
    }

    [GeneratedRegex(@"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")]
    private static partial Regex EmailRegex();
}
