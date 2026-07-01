using CsvHelper.Configuration.Attributes;

namespace SirketVeritabani.Core.Models;

public sealed class DdgSonucKayit
{
    [Name("ad")]
    public string Ad { get; set; } = string.Empty;

    [Name("mevcut_domain")]
    public string MevcutDomain { get; set; } = string.Empty;

    [Name("bulunan_domain")]
    public string BulunanDomain { get; set; } = string.Empty;

    [Name("bulunan_url")]
    public string BulunanUrl { get; set; } = string.Empty;

    [Name("sorgu")]
    public string Sorgu { get; set; } = string.Empty;

    [Name("sira")]
    public int Sira { get; set; }

    [Name("durum")]
    public string Durum { get; set; } = string.Empty;
}
