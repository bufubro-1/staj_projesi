using System.Text.RegularExpressions;
using SirketVeritabani.Core.Nlp;

namespace SirketVeritabani.Core.Search;

public sealed partial class SerpApiBaslikParser
{
    private static readonly HashSet<string> GecersizKelimeler = new(StringComparer.OrdinalIgnoreCase)
    {
        "lojistik", "logistics", "taşımacılık", "transport", "nakliyat", "kargo",
        "gümrük", "customs", "global", "uluslararası", "international",
        "sanayi", "ticaret", "şirketi", "ltd", "şti", "a.ş", "aş", "hizmetleri",
        "linkedin", "profil"
    };

    private static readonly string[] UnvanKelimeleri =
    [
        "müdür", "manager", "ceo", "kurucu", "direktör", "şef", "head", "uzman",
        "specialist", "coordinator", "president", "vp", "chief", "smmm", "analiz",
        "sales", "operation", "ik", "hr", "yönetici"
    ];

    private readonly SpacyEntityDogrulayici _spacy;

    public SerpApiBaslikParser(SpacyEntityDogrulayici spacy) => _spacy = spacy;

    public (string? Isim, string Unvan) IsimVeUnvanCikar(string baslik)
    {
        var parcalar = BaslikAyracRegex().Split(baslik);
        if (parcalar.Length == 0)
            return (null, "Yönetici");

        var olasiIsim = parcalar[0].Trim();
        var temizIsim = IsimTemizle(olasiIsim);
        if (temizIsim == null)
            return (null, "Yönetici");

        var (isPer, isOrg) = _spacy.EntityKontrol(temizIsim);
        if (isOrg && !isPer)
            return (null, "Yönetici");

        var unvan = parcalar.Length > 1 ? parcalar[1].Trim() : "Yönetici";
        unvan = UnvanTemizle(unvan);

        if (!UnvanKelimeleri.Any(k => unvan.Contains(k, StringComparison.OrdinalIgnoreCase)))
        {
            if (parcalar.Length > 2)
            {
                var unvan2 = parcalar[2].Trim();
                if (UnvanKelimeleri.Any(k => unvan2.Contains(k, StringComparison.OrdinalIgnoreCase)))
                    unvan = unvan2;
                else
                    unvan = "Yönetici";
            }
            else
            {
                unvan = "Yönetici";
            }
        }

        if (unvan.Length > 50)
            unvan = "Yönetici";

        return (temizIsim, unvan);
    }

    private static string? IsimTemizle(string name)
    {
        name = name.Trim(".,;:|/'\"- ".ToCharArray());
        var words = name.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (words.Length is < 2 or > 4)
            return null;

        if (!words.All(w => w.Replace(".", "").All(char.IsLetter)))
            return null;

        if (words.Any(w => GecersizKelimeler.Contains(w, StringComparer.OrdinalIgnoreCase)))
            return null;

        return System.Globalization.CultureInfo.CurrentCulture.TextInfo.ToTitleCase(name.ToLowerInvariant());
    }

    private static string UnvanTemizle(string unvan)
    {
        unvan = unvan.Replace("...", "").Replace("..", "").Trim();
        unvan = AtRegex().Replace(unvan, string.Empty);
        unvan = AtSondaRegex().Replace(unvan, string.Empty);
        unvan = AtIsaretRegex().Replace(unvan, string.Empty);
        unvan = SirketindeRegex().Replace(unvan, string.Empty);
        unvan = BaglacRegex().Replace(unvan, string.Empty);
        return unvan.Trim(" -/,|".ToCharArray());
    }

    [GeneratedRegex(@"[-|·]")]
    private static partial Regex BaslikAyracRegex();

    [GeneratedRegex(@"(?i)\s+at\s+.*$")]
    private static partial Regex AtRegex();

    [GeneratedRegex(@"(?i)\s+at$")]
    private static partial Regex AtSondaRegex();

    [GeneratedRegex(@"\s+@\s+.*$")]
    private static partial Regex AtIsaretRegex();

    [GeneratedRegex(@"^.*? şirketinde ")]
    private static partial Regex SirketindeRegex();

    [GeneratedRegex(@"(?i)\s+(and|ve|&)$")]
    private static partial Regex BaglacRegex();
}
