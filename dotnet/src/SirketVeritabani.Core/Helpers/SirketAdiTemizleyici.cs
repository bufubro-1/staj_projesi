using System.Text.RegularExpressions;

namespace SirketVeritabani.Core.Helpers;

public static partial class SirketAdiTemizleyici
{
    public static string Temizle(string? name)
    {
        if (string.IsNullOrWhiteSpace(name))
            return string.Empty;

        name = name.ToLowerInvariant();
        name = name
            .Replace("i̇", "i")
            .Replace("ı", "i")
            .Replace("ş", "s")
            .Replace("ğ", "g")
            .Replace("ü", "u")
            .Replace("ö", "o")
            .Replace("ç", "c");

        name = AsRegex().Replace(name, string.Empty);
        name = LtdRegex().Replace(name, string.Empty);
        name = NoktalamaRegex().Replace(name, string.Empty);

        return name;
    }

    [GeneratedRegex(@"\ba\.ş\.\b|\bas\b|\banonim şirketi\b")]
    private static partial Regex AsRegex();

    [GeneratedRegex(@"\bltd\.\s*şti\.\b|\blimited şirketi\b|\btic\.\b|\bsan\.\b|\bve\b")]
    private static partial Regex LtdRegex();

    [GeneratedRegex(@"[^a-z0-9]")]
    private static partial Regex NoktalamaRegex();
}
