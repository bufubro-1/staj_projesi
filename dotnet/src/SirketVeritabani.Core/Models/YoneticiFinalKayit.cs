using CsvHelper.Configuration.Attributes;

namespace SirketVeritabani.Core.Models;

public sealed class YoneticiFinalKayit
{
    [Name("sirket_adi")]
    public string SirketAdi { get; set; } = string.Empty;

    [Name("departman")]
    public string Departman { get; set; } = "Yönetici";

    [Name("isim")]
    public string Isim { get; set; } = string.Empty;

    [Name("unvan")]
    public string Unvan { get; set; } = string.Empty;

    [Name("email")]
    public string Email { get; set; } = string.Empty;

    [Name("linkedin_url")]
    public string LinkedinUrl { get; set; } = string.Empty;
}
