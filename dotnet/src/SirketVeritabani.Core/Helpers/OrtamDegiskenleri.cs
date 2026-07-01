namespace SirketVeritabani.Core.Helpers;

public static class OrtamDegiskenleri
{
    private static bool _yuklendi;

    public static void Yukle()
    {
        if (_yuklendi)
            return;

        _yuklendi = true;
        var envDosyasi = Path.Combine(ProjeYollari.KokDizin, ".env");
        if (!File.Exists(envDosyasi))
            return;

        foreach (var satir in File.ReadAllLines(envDosyasi))
        {
            var trimmed = satir.Trim();
            if (trimmed.Length == 0 || trimmed.StartsWith('#'))
                continue;

            var eq = trimmed.IndexOf('=');
            if (eq <= 0)
                continue;

            var anahtar = trimmed[..eq].Trim();
            var deger = trimmed[(eq + 1)..].Trim().Trim('"');
            Environment.SetEnvironmentVariable(anahtar, deger);
        }
    }

    public static string? Al(string anahtar) => Environment.GetEnvironmentVariable(anahtar);
}
