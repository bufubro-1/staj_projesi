using System.Globalization;
using CsvHelper;
using CsvHelper.Configuration;

namespace SirketVeritabani.Core.Helpers;

public static class CsvYardimci
{
    private static CsvConfiguration Config => new(CultureInfo.InvariantCulture)
    {
        HasHeaderRecord = true,
        MissingFieldFound = null,
        BadDataFound = null
    };

    public static List<T> Oku<T>(string dosyaYolu)
    {
        if (!File.Exists(dosyaYolu))
            return [];

        using var reader = new StreamReader(dosyaYolu);
        using var csv = new CsvReader(reader, Config);
        return csv.GetRecords<T>().ToList();
    }

    public static void Yaz<T>(string dosyaYolu, IEnumerable<T> kayitlar)
    {
        var dir = Path.GetDirectoryName(dosyaYolu);
        if (!string.IsNullOrEmpty(dir))
            Directory.CreateDirectory(dir);

        using var writer = new StreamWriter(dosyaYolu, false);
        using var csv = new CsvWriter(writer, Config);
        csv.WriteRecords(kayitlar);
    }
}
