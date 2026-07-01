using System.Globalization;
using System.Text;

namespace SirketVeritabani.Core.Helpers;

public static class AsciiYardimci
{
    public static string TurkceAscii(string metin)
    {
        var normalized = metin.Normalize(NormalizationForm.FormD);
        var sb = new StringBuilder();
        foreach (var c in normalized)
        {
            if (CharUnicodeInfo.GetUnicodeCategory(c) != UnicodeCategory.NonSpacingMark)
                sb.Append(c);
        }
        return sb.ToString().Normalize(NormalizationForm.FormC);
    }
}
