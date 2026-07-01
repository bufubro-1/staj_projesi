using System.Text.RegularExpressions;

namespace SirketVeritabani.Core.Helpers;

public static partial class DomainTemizleyici
{
    public static string? Temizle(string? url)
    {
        if (string.IsNullOrWhiteSpace(url))
            return null;

        url = url.ToLowerInvariant().Trim();
        url = HttpRegex().Replace(url, string.Empty);
        url = WwwRegex().Replace(url, string.Empty);
        url = url.Split('/')[0];

        if (url.Length < 3 || !url.Contains('.'))
            return null;

        return url;
    }

    [GeneratedRegex(@"^https?:\/\/", RegexOptions.IgnoreCase)]
    private static partial Regex HttpRegex();

    [GeneratedRegex(@"^www\.", RegexOptions.IgnoreCase)]
    private static partial Regex WwwRegex();
}
