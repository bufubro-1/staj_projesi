using System.Globalization;

namespace SirketVeritabani.Core.Helpers;

public static class SerpApiSirketAdiHelper
{
    private static readonly HashSet<string> Silinecekler =
    [
        "sanayi", "ticaret", "hizmetleri", "ltd.", "şti.", "ltd", "şti", "a.ş.", "aş.", "a.s.", "aş",
        "tic.", "san.", "ve", "danışmanlık", "müşavirliği", "yayıncılık", "turizm",
        "dış", "iç", "ithalat", "ihracat", "pazarlama", "uluslararası", "global",
        "nakliyat", "taşımacılık", "gıda", "dan.", "tic", "san", "dan"
    ];

    public static string Temizle(string ad)
    {
        var adLower = ad.ToLowerInvariant();
        var kelimeler = adLower.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        var yeni = new List<string>();

        foreach (var k in kelimeler)
        {
            var kTemiz = k.Trim(".,;:|/'\"-".ToCharArray());
            if (!Silinecekler.Contains(kTemiz))
                yeni.Add(kTemiz);
        }

        var temizAd = string.Join(' ', yeni);
        if (string.IsNullOrWhiteSpace(temizAd) || temizAd.Length < 2)
            return ad.Split(' ', StringSplitOptions.RemoveEmptyEntries).FirstOrDefault() ?? ad;

        return CultureInfo.CurrentCulture.TextInfo.ToTitleCase(temizAd);
    }

    public static string BelirleyiciAd(string kisaAd)
    {
        var kelimeler = kisaAd.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (kelimeler.Length >= 3)
            return string.Join(' ', kelimeler.Take(3)).ToLowerInvariant();
        return kisaAd.ToLowerInvariant();
    }
}
