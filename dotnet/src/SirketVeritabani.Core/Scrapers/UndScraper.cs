using System.Text.RegularExpressions;
using HtmlAgilityPack;
using SirketVeritabani.Core.Helpers;
using SirketVeritabani.Core.Http;
using SirketVeritabani.Core.Models;
using SirketVeritabani.Core.Nlp;

namespace SirketVeritabani.Core.Scrapers;

public sealed class UndScraper
{
    private const string BaseUrl = "https://www.und.org.tr/uyelerimiz";
    private readonly ScraperHttpClient _http = new();

    public async Task CalistirAsync(CancellationToken ct = default)
    {
        Console.WriteLine("UND Üye Listesi taranıyor...");

        var sirketLinkleri = new List<(string Href, string Ad)>();

        for (var page = 1; ; page++)
        {
            ct.ThrowIfCancellationRequested();
            var url = page > 1 ? $"{BaseUrl}?p={page}" : BaseUrl;
            var html = await _http.SayfaAlAsync(url, ct);
            if (html == null)
                break;

            var doc = new HtmlDocument();
            doc.LoadHtml(html);

            var links = doc.DocumentNode.SelectNodes("//a[contains(@href,'/firma-bilgileri/')]");
            if (links == null || links.Count == 0)
                break;

            var yeniLink = 0;
            foreach (var link in links)
            {
                var href = link.GetAttributeValue("href", string.Empty);
                var ad = link.InnerText.Trim();
                if (string.IsNullOrEmpty(href) || string.IsNullOrEmpty(ad))
                    continue;

                if (sirketLinkleri.Any(x => x.Href == href))
                    continue;

                sirketLinkleri.Add((href, ad));
                yeniLink++;
            }

            if (yeniLink == 0)
                break;

            Console.WriteLine($"Sayfa {page} tarandı, şu ana kadar {sirketLinkleri.Count} şirket bulundu...");
            await Task.Delay(1000, ct);
        }

        Console.WriteLine($"Toplam {sirketLinkleri.Count} adet UND üyesi detay sayfası bulundu. Detaylar çekiliyor...");

        var sirketler = new List<SirketKayit>();
        var i = 0;

        foreach (var (href, ad) in sirketLinkleri)
        {
            ct.ThrowIfCancellationRequested();
            i++;
            if (i % 50 == 0)
                Console.WriteLine($"  {i}/{sirketLinkleri.Count}...");

            var detayUrl = href.StartsWith("http", StringComparison.OrdinalIgnoreCase)
                ? href
                : "https://www.und.org.tr" + href;

            try
            {
                var html = await _http.SayfaAlAsync(detayUrl, ct);
                if (html == null)
                    continue;

                var doc = new HtmlDocument();
                doc.LoadHtml(html);

                string? website = null;
                string? telefon = null;
                string? sehir = null;

                var tds = doc.DocumentNode.SelectNodes("//td");
                if (tds != null)
                {
                    for (var j = 0; j < tds.Count; j++)
                    {
                        var text = tds[j].InnerText.Trim();
                        if (text.Contains("Website") && j + 2 < tds.Count)
                        {
                            var a = tds[j + 2].SelectSingleNode(".//a");
                            if (a != null)
                                website = a.GetAttributeValue("href", null);
                        }
                        else if (text.Contains("Telefon") && j + 2 < tds.Count)
                        {
                            telefon = tds[j + 2].InnerText.Trim();
                        }
                        else if (text.Contains("İl / Ülke") && j + 2 < tds.Count)
                        {
                            var sehirMetin = tds[j + 2].InnerText.Trim();
                            sehir = sehirMetin.Contains('/')
                                ? sehirMetin.Split('/')[0].Trim()
                                : sehirMetin;
                        }
                    }
                }

                var domain = DomainTemizleyici.Temizle(website);

                sirketler.Add(new SirketKayit
                {
                    Ad = ad,
                    Domain = domain ?? string.Empty,
                    Email = string.Empty,
                    Telefon = telefon ?? string.Empty,
                    Sehir = sehir ?? string.Empty
                });
            }
            catch
            {
                // Tek kayıt hatası — devam
            }

            await Task.Delay(500, ct);
        }

        CsvYardimci.Yaz(ProjeYollari.UndSirketlerCsv, sirketler);
        Console.WriteLine($"\nUND işlemi tamamlandı! {sirketler.Count} şirket '{ProjeYollari.UndSirketlerCsv}' dosyasına yazıldı.");
    }
}
