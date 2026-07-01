using System.Net;
using System.Text;
using System.Text.RegularExpressions;
using HtmlAgilityPack;
using SirketVeritabani.Core.Helpers;

namespace SirketVeritabani.Core.Search;

public sealed partial class DuckDuckGoArama
{
    private static readonly string[] HaricDomainParcalari =
    [
        "facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com",
        "youtube.com", "tiktok.com", "wikipedia.org", "cybo.com", "yoys.com",
        "fretador.com", "sahibinden.com", "yellowpages", "tripadvisor",
        "duckduckgo.com", "google.com", "bing.com"
    ];

    private readonly HttpClient _client;
    private readonly Random _random = new();

    public DuckDuckGoArama()
    {
        _client = new HttpClient
        {
            Timeout = TimeSpan.FromSeconds(15)
        };
        _client.DefaultRequestHeaders.TryAddWithoutValidation(
            "User-Agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36");
    }

    public async Task<IReadOnlyList<string>> AraAsync(string sorgu, int maxSonuc = 5, CancellationToken ct = default)
    {
        var html = await HtmlAlAsync(sorgu, ct);
        if (html == null)
            return [];

        var doc = new HtmlDocument();
        doc.LoadHtml(html);

        var linkler = doc.DocumentNode.SelectNodes("//a[contains(@class,'result__a')]");
        if (linkler == null)
            return [];

        var sonuclar = new List<string>();

        foreach (var link in linkler)
        {
            var href = link.GetAttributeValue("href", string.Empty);
            var url = UrlCoz(href);
            if (string.IsNullOrEmpty(url))
                continue;

            var domain = DomainTemizleyici.Temizle(url);
            if (domain == null || HaricDomainMi(domain))
                continue;

            if (!sonuclar.Contains(url, StringComparer.OrdinalIgnoreCase))
                sonuclar.Add(url);

            if (sonuclar.Count >= maxSonuc)
                break;
        }

        return sonuclar;
    }

    public async Task<(string? Url, string? Domain, string KullanilanSorgu)> IlkGecerliSonucBulAsync(
        IEnumerable<string> sorgular,
        CancellationToken ct = default)
    {
        foreach (var sorgu in sorgular)
        {
            ct.ThrowIfCancellationRequested();
            var sonuclar = await AraAsync(sorgu, maxSonuc: 3, ct);

            if (sonuclar.Count > 0)
            {
                var url = sonuclar[0];
                return (url, DomainTemizleyici.Temizle(url), sorgu);
            }

            await Task.Delay(TimeSpan.FromMilliseconds(_random.Next(1500, 3000)), ct);
        }

        return (null, null, sorgular.LastOrDefault() ?? string.Empty);
    }

    public static IEnumerable<string> SorguOlustur(string sirketAdi)
    {
        var kisa = SirketAdiKisalt(sirketAdi);

        yield return $"\"{kisa}\" lojistik website";
        yield return $"\"{kisa}\" lojistik iletişim site:.com.tr";
        yield return $"{kisa} lojistik resmi site";
    }

    private static string SirketAdiKisalt(string ad)
    {
        var ekler = new[] { "Tic. Ltd. Şti.", "Ltd. Şti.", "A.Ş.", "Ticaret", "Hizmetleri", "Sanayi" };
        var sonuc = ad.Trim();
        foreach (var ek in ekler)
            sonuc = sonuc.Replace(ek, string.Empty, StringComparison.OrdinalIgnoreCase);

        sonuc = Regex.Replace(sonuc, @"\s+", " ").Trim();
        return sonuc;
    }

    private async Task<string?> HtmlAlAsync(string sorgu, CancellationToken ct)
    {
        try
        {
            var content = new FormUrlEncodedContent(new Dictionary<string, string>
            {
                ["q"] = sorgu
            });

            using var response = await _client.PostAsync("https://html.duckduckgo.com/html/", content, ct);
            if (!response.IsSuccessStatusCode)
                return null;

            return await response.Content.ReadAsStringAsync(ct);
        }
        catch
        {
            return null;
        }
    }

    private static string? UrlCoz(string href)
    {
        if (string.IsNullOrWhiteSpace(href))
            return null;

        if (href.Contains("uddg=", StringComparison.OrdinalIgnoreCase))
        {
            var match = UddgRegex().Match(href);
            if (match.Success)
                href = WebUtility.UrlDecode(match.Groups[1].Value);
        }

        if (href.StartsWith("//"))
            href = "https:" + href;

        if (!href.StartsWith("http", StringComparison.OrdinalIgnoreCase))
            return null;

        return href;
    }

    private static bool HaricDomainMi(string domain)
    {
        return HaricDomainParcalari.Any(h =>
            domain.Contains(h, StringComparison.OrdinalIgnoreCase));
    }

    [GeneratedRegex(@"uddg=([^&]+)", RegexOptions.IgnoreCase)]
    private static partial Regex UddgRegex();
}
