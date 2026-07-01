namespace SirketVeritabani.Core.Helpers;

/// <summary>
/// CSV dosyaları proje kök dizininde (dotnet/ üst klasör) tutulur.
/// </summary>
public static class ProjeYollari
{
    public static string KokDizin { get; private set; } = BulKokDizin();

    public static void KokDizinAyarla(string yol) => KokDizin = yol;

    public static string Csv(string dosyaAdi) => Path.Combine(KokDizin, dosyaAdi);

    public static string SirketlerCsv => Csv("sirketler.csv");
    public static string UndSirketlerCsv => Csv("und_sirketler.csv");
    public static string MasterSirketlerCsv => Csv("master_sirketler.csv");
    public static string YoneticilerCsv => Csv("yoneticiler.csv");
    public static string TarananSirketlerCsv => Csv("taranan_sirketler.csv");
    public static string DdgSonuclarCsv => Csv("ddg_sonuclar.csv");
    public static string YoneticilerFinalCsv => Csv("yoneticiler_final.csv");
    public static string SpacyValidatorScript => Path.Combine(KokDizin, "dotnet", "tools", "spacy_validate.py");
    public static string SpacyEntityScript => Path.Combine(KokDizin, "dotnet", "tools", "spacy_entity_check.py");

    private static string BulKokDizin()
    {
        var env = Environment.GetEnvironmentVariable("SIRKET_PROJE_KOKU");
        if (!string.IsNullOrWhiteSpace(env) && Directory.Exists(env))
            return Path.GetFullPath(env);

        var current = Directory.GetCurrentDirectory();
        if (File.Exists(Path.Combine(current, "master_sirketler.csv"))
            || File.Exists(Path.Combine(current, "und_sirketler.csv")))
            return current;

        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir != null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "master_sirketler.csv"))
                || File.Exists(Path.Combine(dir.FullName, "dotnet", "SirketVeritabani.sln"))
                || File.Exists(Path.Combine(dir.FullName, "python", "requirements.txt")))
                return dir.FullName;
            dir = dir.Parent;
        }

        return current;
    }
}
