using System.Text.RegularExpressions;
using HtmlAgilityPack;
using SirketVeritabani.Core.Models;
using SirketVeritabani.Core.Nlp;

namespace SirketVeritabani.Core.Scrapers;

public sealed partial class KisiCikarici
{
    private static readonly string[] UnvanKaliplari =
    [
        @"genel\s*müdür", @"ceo", @"chief\s*executive",
        @"genel\s*koordinat", @"başkan",
        @"müdür", @"direktör", @"director",
        @"yönetim\s*kurulu", @"board",
        @"kurucu", @"founder", @"partner", @"ortak",
        @"satış\s*müdür", @"sales\s*(?:manager|director)",
        @"operasyon\s*müdür", @"operations?\s*(?:manager|director)",
        @"lojistik\s*müdür", @"logistics?\s*(?:manager|director)",
        @"finans\s*müdür", @"cfo", @"coo", @"cto",
        @"pazarlama\s*müdür", @"marketing\s*(?:manager|director)",
        @"insan\s*kaynakları", @"human\s*resources", @"hr\s*(?:manager|director)",
        @"manager", @"head\s*of"
    ];

    private static readonly Regex UnvanRegex = new(
        string.Join('|', UnvanKaliplari),
        RegexOptions.IgnoreCase | RegexOptions.Compiled);

    private static readonly HashSet<string> GecersizKelimeler = new(StringComparer.OrdinalIgnoreCase)
    {
        "cookie", "quote", "mission", "vision", "policy", "human", "resources",
        "contact", "about", "team", "öneri", "talep", "başvuru", "we", "are",
        "yazın", "bize", "gönder", "formu", "form", "submit", "download", "read",
        "more", "click", "here", "view", "show", "menu", "home", "search",
        "why", "choose", "our", "get", "quick", "learn", "back", "next", "prev",
        "security", "privacy", "terms", "conditions", "suggestions", "requests",
        "united", "kingdom", "turkey", "türkiye", "istanbul", "ankara", "izmir",
        "germany", "london", "usa", "america", "almanya", "ingiltere", "birleşik",
        "mersin", "antalya", "bursa", "adana", "samsun", "eskişehir", "kayseri",
        "ltd", "şti", "ticaret", "sanayi", "company", "inc", "corp",
        "hizmetleri", "hizmetlere", "services", "service", "destek", "support",
        "lojistik", "logistics", "denizcilik", "shipping", "taşımacılık", "transport",
        "gümrük", "customs", "global", "uluslararası", "international",
        "profesyonel", "professional", "industrial", "scale", "large",
        "ana", "sayfa", "page", "araç", "takibi", "tracking",
        "ekip", "çalışması", "müşteri", "formu", "neden", "seçmelisin",
        "repair", "management", "engine", "cargo", "white", "glove",
        "incredible", "personalized", "full", "beyan", "bagaj", "kargo",
        "taşıma", "kara", "yolu", "digital", "supply", "chain", "solutions",
        "hızlı", "menü", "menu", "hizmeti", "partnerliği"
    };

    private readonly SpacyDogrulayici _spacy;

    public KisiCikarici(SpacyDogrulayici spacy) => _spacy = spacy;

    public List<KisiCikarim> Cikar(HtmlDocument doc)
    {
        var kisiler = new List<KisiCikarim>();
        var tags = new[] { "p", "li", "td", "span", "div", "h2", "h3", "h4", "h5", "strong" };

        var blocks = doc.DocumentNode.SelectNodes(
            string.Join(" | ", tags.Select(t => $"//{t}")));

        if (blocks == null)
            return [];

        var textBlocks = blocks.ToList();

        for (var i = 0; i < textBlocks.Count; i++)
        {
            var text = HtmlEntity.DeEntitize(textBlocks[i].InnerText).Trim();
            if (string.IsNullOrEmpty(text) || text.Length > 150)
                continue;

            if (!UnvanRegex.IsMatch(text))
                continue;

            var unvan = text;
            if (unvan.Length > 60 || unvan.Contains('@') || unvan.Contains("http", StringComparison.OrdinalIgnoreCase))
                continue;

            if (i > 0)
            {
                var onceki = HtmlEntity.DeEntitize(textBlocks[i - 1].InnerText).Trim();
                if (PotansiyelIsimMi(onceki) && !UnvanRegex.IsMatch(onceki))
                {
                    if (_spacy.IsimGecerliMi(onceki))
                    {
                        kisiler.Add(new KisiCikarim { Isim = onceki, Unvan = UnvanTemizle(unvan) });
                        continue;
                    }
                }
            }

            var parcalar = AyracRegex().Split(text);
            if (parcalar.Length >= 2)
            {
                var potansiyelIsim = parcalar[0].Trim();
                var potansiyelUnvan = parcalar[1].Trim();

                if (PotansiyelIsimMi(potansiyelIsim) && !UnvanRegex.IsMatch(potansiyelIsim))
                {
                    if (_spacy.IsimGecerliMi(potansiyelIsim))
                    {
                        kisiler.Add(new KisiCikarim
                        {
                            Isim = potansiyelIsim,
                            Unvan = UnvanTemizle(potansiyelUnvan)
                        });
                    }
                }
            }
        }

        return Tekillestir(kisiler);
    }

    private static bool PotansiyelIsimMi(string metin)
    {
        if (metin.Length >= 40)
            return false;

        var kelimeler = metin.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (kelimeler.Length is < 2 or > 4)
            return false;

        if (!kelimeler.All(k => k.Replace(".", "").All(char.IsLetter)))
            return false;

        if (!kelimeler.Where(k => k.Length > 1).All(k => char.IsUpper(k[0])))
            return false;

        var lower = metin.ToLowerInvariant();
        return !GecersizKelimeler.Any(g => lower.Contains(g, StringComparison.Ordinal));
    }

    private static string UnvanTemizle(string unvan)
    {
        var match = UnvanRegex.Match(unvan);
        if (!match.Success)
            return unvan;

        var temiz = unvan[match.Index..];
        temiz = KucukHarfBaslangicRegex().Replace(temiz, string.Empty).Trim();
        return string.IsNullOrEmpty(temiz) ? unvan : temiz;
    }

    private static List<KisiCikarim> Tekillestir(List<KisiCikarim> kisiler)
    {
        var gorulen = new HashSet<string>();
        var sonuc = new List<KisiCikarim>();

        foreach (var k in kisiler)
        {
            var anahtar = $"{k.Isim}|{k.Unvan}";
            if (gorulen.Add(anahtar))
                sonuc.Add(k);
        }

        return sonuc;
    }

    [GeneratedRegex(@"[\-–|/]")]
    private static partial Regex AyracRegex();

    [GeneratedRegex(@"^[a-zçğıöşü]+")]
    private static partial Regex KucukHarfBaslangicRegex();
}
