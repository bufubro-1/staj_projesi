using HtmlAgilityPack;
using SirketVeritabani.Core.Helpers;
using SirketVeritabani.Core.Http;
using SirketVeritabani.Core.Models;

namespace SirketVeritabani.Core.Scrapers;

public sealed class UtikadScraper
{
    private const string Url = "https://www.utikad.org.tr/UTIKAD-Uye-Listesi";
    private readonly ScraperHttpClient _http = new();

    public async Task CalistirAsync(CancellationToken ct = default)
    {
        Console.WriteLine("UTİKAD Üye Listesi taranıyor...");

        var html = await _http.SayfaAlAsync(Url, ct);
        if (html == null)
        {
            Console.WriteLine("Hata! Sayfaya erişilemedi.");
            return;
        }

        var doc = new HtmlDocument();
        doc.LoadHtml(html);

        var sirketBloklari = doc.DocumentNode.SelectNodes("//div[contains(@class,'Uyeler')]");
        if (sirketBloklari == null || sirketBloklari.Count == 0)
        {
            Console.WriteLine("HTML'de 'Uyeler' div'leri bulunamadı. Yapı değişmiş olabilir.");
            return;
        }

        var sirketlerDict = new Dictionary<string, SirketKayit>();

        foreach (var blok in sirketBloklari)
        {
            var isimTag = blok.SelectSingleNode(".//div[contains(@class,'col-sm-12')]");
            if (isimTag == null)
                continue;

            var aTag = isimTag.SelectSingleNode(".//a");
            var isim = aTag != null ? aTag.InnerText.Trim() : isimTag.InnerText.Trim();
            var website = aTag?.GetAttributeValue("href", string.Empty) ?? string.Empty;
            var domain = DomainTemizleyici.Temizle(website);

            var emailTag = blok.SelectSingleNode(".//a[starts-with(@href,'mailto:')]");
            var email = emailTag?.GetAttributeValue("href", string.Empty)
                .Replace("mailto:", string.Empty, StringComparison.OrdinalIgnoreCase)
                .Trim();

            string? telefon = null;
            var telefonTag = blok.SelectSingleNode(".//span[contains(@class,'glyphicon-earphone')]");
            if (telefonTag != null)
            {
                var telI = telefonTag.SelectSingleNode("following-sibling::i[1]");
                if (telI != null)
                    telefon = telI.InnerText.Trim();
            }

            string? sehir = null;
            var adresTag = blok.SelectSingleNode(".//span[contains(@class,'glyphicon-map-marker')]");
            if (adresTag != null)
            {
                var adresI = adresTag.SelectSingleNode("following-sibling::i[1]");
                if (adresI != null)
                {
                    var parcalar = adresI.InnerText.Trim().Split('/')
                        .Select(p => p.Trim())
                        .Where(p => !string.IsNullOrEmpty(p))
                        .ToArray();
                    sehir = parcalar.Length > 1 ? parcalar[^1] : adresI.InnerText.Trim();
                }
            }

            if (string.IsNullOrEmpty(domain))
                continue;

            if (sirketlerDict.TryGetValue(domain, out var mevcut))
            {
                if (string.IsNullOrEmpty(mevcut.Email) && !string.IsNullOrEmpty(email))
                    mevcut.Email = email;
                if (string.IsNullOrEmpty(mevcut.Telefon) && !string.IsNullOrEmpty(telefon))
                    mevcut.Telefon = telefon!;
            }
            else
            {
                sirketlerDict[domain] = new SirketKayit
                {
                    Ad = isim,
                    Domain = domain,
                    Email = email ?? string.Empty,
                    Telefon = telefon ?? string.Empty,
                    Sehir = sehir ?? string.Empty
                };
            }
        }

        Console.WriteLine($"Toplam {sirketlerDict.Count} adet benzersiz şirket bulundu.");

        CsvYardimci.Yaz(ProjeYollari.SirketlerCsv, sirketlerDict.Values);
        Console.WriteLine($"Veriler '{ProjeYollari.SirketlerCsv}' dosyasına kaydedildi.");
    }
}
