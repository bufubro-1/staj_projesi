using SirketVeritabani.Core.Helpers;
using SirketVeritabani.Core.Models;

namespace SirketVeritabani.Core.Scrapers;

public sealed class MergeService
{
    private sealed class MasterKayit
    {
        public string Ad { get; set; } = string.Empty;
        public string Domain { get; set; } = string.Empty;
        public string Email { get; set; } = string.Empty;
        public string Telefon { get; set; } = string.Empty;
        public string Sehir { get; set; } = string.Empty;
        public List<string> Kaynak { get; } = [];
    }

    public void Calistir()
    {
        var masterDict = new Dictionary<string, MasterKayit>();

        if (File.Exists(ProjeYollari.SirketlerCsv))
        {
            foreach (var row in CsvYardimci.Oku<SirketKayit>(ProjeYollari.SirketlerCsv))
            {
                if (string.IsNullOrWhiteSpace(row.Domain))
                    continue;

                masterDict[row.Domain] = new MasterKayit
                {
                    Ad = row.Ad,
                    Domain = row.Domain,
                    Email = row.Email,
                    Telefon = row.Telefon,
                    Sehir = row.Sehir,
                    Kaynak = { "UTIKAD" }
                };
            }
        }
        else
        {
            Console.WriteLine("sirketler.csv (UTİKAD) bulunamadı.");
        }

        if (File.Exists(ProjeYollari.UndSirketlerCsv))
        {
            foreach (var row in CsvYardimci.Oku<SirketKayit>(ProjeYollari.UndSirketlerCsv))
            {
                var domain = row.Domain;
                var ad = row.Ad;

                if (!string.IsNullOrWhiteSpace(domain) && masterDict.TryGetValue(domain, out var mevcut))
                {
                    if (!mevcut.Kaynak.Contains("UND"))
                        mevcut.Kaynak.Add("UND");

                    if (string.IsNullOrEmpty(mevcut.Email) && !string.IsNullOrEmpty(row.Email))
                        mevcut.Email = row.Email;
                    if (string.IsNullOrEmpty(mevcut.Telefon) && !string.IsNullOrEmpty(row.Telefon))
                        mevcut.Telefon = row.Telefon;
                    if (string.IsNullOrEmpty(mevcut.Sehir) && !string.IsNullOrEmpty(row.Sehir))
                        mevcut.Sehir = row.Sehir;
                }
                else if (!string.IsNullOrWhiteSpace(domain))
                {
                    masterDict[domain] = new MasterKayit
                    {
                        Ad = ad,
                        Domain = domain,
                        Email = row.Email,
                        Telefon = row.Telefon,
                        Sehir = row.Sehir,
                        Kaynak = { "UND" }
                    };
                }
                else
                {
                    var cleanTarget = SirketAdiTemizleyici.Temizle(ad);
                    var eslesti = false;

                    foreach (var (mDomain, mData) in masterDict)
                    {
                        if (SirketAdiTemizleyici.Temizle(mData.Ad) == cleanTarget)
                        {
                            if (!mData.Kaynak.Contains("UND"))
                                mData.Kaynak.Add("UND");
                            eslesti = true;
                            break;
                        }
                    }

                    if (!eslesti)
                    {
                        var fakeDomain = $"nodomain_{masterDict.Count}";
                        masterDict[fakeDomain] = new MasterKayit
                        {
                            Ad = ad,
                            Domain = string.Empty,
                            Email = row.Email,
                            Telefon = row.Telefon,
                            Sehir = row.Sehir,
                            Kaynak = { "UND" }
                        };
                    }
                }
            }
        }
        else
        {
            Console.WriteLine("und_sirketler.csv bulunamadı.");
        }

        var cikti = masterDict.Values.Select(d => new SirketKayit
        {
            Ad = d.Ad,
            Domain = d.Domain,
            Email = d.Email,
            Telefon = d.Telefon,
            Sehir = d.Sehir,
            Kaynak = string.Join(" + ", d.Kaynak)
        }).ToList();

        CsvYardimci.Yaz(ProjeYollari.MasterSirketlerCsv, cikti);

        var sadeceUtikad = cikti.Count(d => d.Kaynak == "UTIKAD");
        var sadeceUnd = cikti.Count(d => d.Kaynak == "UND");
        var ortak = cikti.Count(d => d.Kaynak.Contains("UTIKAD") && d.Kaynak.Contains("UND"));

        Console.WriteLine($"Toplam {cikti.Count} benzersiz şirket '{ProjeYollari.MasterSirketlerCsv}' dosyasında birleştirildi.");
        Console.WriteLine($"Sadece UTİKAD: {sadeceUtikad}");
        Console.WriteLine($"Sadece UND: {sadeceUnd}");
        Console.WriteLine($"Ortak (Her iki derneğe üye): {ortak}");
    }
}
