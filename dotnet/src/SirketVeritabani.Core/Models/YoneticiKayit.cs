using CsvHelper.Configuration.Attributes;

namespace SirketVeritabani.Core.Models;

public sealed class YoneticiKayit
{
    [Name("sirket_adi")]
    public string SirketAdi { get; set; } = string.Empty;

    [Name("domain")]
    public string Domain { get; set; } = string.Empty;

    [Name("isim")]
    public string Isim { get; set; } = string.Empty;

    [Name("unvan")]
    public string Unvan { get; set; } = string.Empty;

    [Name("email")]
    public string Email { get; set; } = string.Empty;

    [Name("kaynak")]
    public string Kaynak { get; set; } = string.Empty;
}
