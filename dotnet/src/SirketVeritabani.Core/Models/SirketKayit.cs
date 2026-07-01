using CsvHelper.Configuration.Attributes;

namespace SirketVeritabani.Core.Models;

public sealed class SirketKayit
{
    [Name("ad")]
    public string Ad { get; set; } = string.Empty;

    [Name("domain")]
    public string Domain { get; set; } = string.Empty;

    [Name("email")]
    public string Email { get; set; } = string.Empty;

    [Name("telefon")]
    public string Telefon { get; set; } = string.Empty;

    [Name("sehir")]
    public string Sehir { get; set; } = string.Empty;

    [Name("kaynak")]
    public string Kaynak { get; set; } = string.Empty;
}
