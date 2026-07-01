using CsvHelper.Configuration.Attributes;

namespace SirketVeritabani.Core.Models;

public sealed class TarananSirketKayit
{
    [Name("ad")]
    public string Ad { get; set; } = string.Empty;

    [Name("domain")]
    public string Domain { get; set; } = string.Empty;

    [Name("durum")]
    public string Durum { get; set; } = string.Empty;

    [Name("bulunan_kisi")]
    public int BulunanKisi { get; set; }

    [Name("bulunan_mail")]
    public int BulunanMail { get; set; }
}
