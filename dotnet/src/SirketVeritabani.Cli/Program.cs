using SirketVeritabani.Core.Helpers;
using SirketVeritabani.Core.Scrapers;

namespace SirketVeritabani.Cli;

internal static class Program
{
    public static async Task<int> Main(string[] args)
    {
        if (args.Length == 0)
        {
            YardimYaz();
            return 1;
        }

        var kokArg = args.FirstOrDefault(a => a.StartsWith("--kok=", StringComparison.OrdinalIgnoreCase));
        if (kokArg != null)
        {
            var yol = kokArg["--kok=".Length..];
            ProjeYollari.KokDizinAyarla(Path.GetFullPath(yol));
        }

        OrtamDegiskenleri.Yukle();
        Console.WriteLine($"[*] Proje kök dizini: {ProjeYollari.KokDizin}");

        var komut = args[0].ToLowerInvariant();
        var filtreliArgs = args.Where(a => !a.StartsWith("--kok=", StringComparison.OrdinalIgnoreCase)).ToArray();

        try
        {
            switch (komut)
            {
                case "und":
                    await new UndScraper().CalistirAsync();
                    return 0;

                case "utikad":
                    await new UtikadScraper().CalistirAsync();
                    return 0;

                case "merge":
                    new MergeService().Calistir();
                    return 0;

                case "website":
                    var input = ProjeYollari.MasterSirketlerCsv;
                    int? limit = null;

                    for (var i = 1; i < filtreliArgs.Length; i++)
                    {
                        if (filtreliArgs[i].Equals("--input", StringComparison.OrdinalIgnoreCase) && i + 1 < filtreliArgs.Length)
                        {
                            input = Path.IsPathRooted(filtreliArgs[i + 1])
                                ? filtreliArgs[i + 1]
                                : ProjeYollari.Csv(filtreliArgs[i + 1]);
                            i++;
                        }
                        else if (filtreliArgs[i].Equals("--limit", StringComparison.OrdinalIgnoreCase) && i + 1 < filtreliArgs.Length
                                 && int.TryParse(filtreliArgs[i + 1], out var n))
                        {
                            limit = n;
                            i++;
                        }
                    }

                    await new WebsiteScraper().CalistirAsync(input, limit);
                    return 0;

                case "ddg":
                    var ddgInput = ProjeYollari.MasterSirketlerCsv;
                    int? ddgLimit = null;
                    var sadeceEksikDomain = false;

                    for (var i = 1; i < filtreliArgs.Length; i++)
                    {
                        if (filtreliArgs[i].Equals("--input", StringComparison.OrdinalIgnoreCase) && i + 1 < filtreliArgs.Length)
                        {
                            ddgInput = Path.IsPathRooted(filtreliArgs[i + 1])
                                ? filtreliArgs[i + 1]
                                : ProjeYollari.Csv(filtreliArgs[i + 1]);
                            i++;
                        }
                        else if (filtreliArgs[i].Equals("--limit", StringComparison.OrdinalIgnoreCase) && i + 1 < filtreliArgs.Length
                                 && int.TryParse(filtreliArgs[i + 1], out var n))
                        {
                            ddgLimit = n;
                            i++;
                        }
                        else if (filtreliArgs[i].Equals("--eksik-domain", StringComparison.OrdinalIgnoreCase))
                        {
                            sadeceEksikDomain = true;
                        }
                    }

                    await new DdgDiscoveryScraper().CalistirAsync(ddgInput, ddgLimit, sadeceEksikDomain);
                    return 0;

                case "serpapi":
                    var serpInput = ProjeYollari.MasterSirketlerCsv;
                    int? serpLimit = null;

                    for (var i = 1; i < filtreliArgs.Length; i++)
                    {
                        if (filtreliArgs[i].Equals("--input", StringComparison.OrdinalIgnoreCase) && i + 1 < filtreliArgs.Length)
                        {
                            serpInput = Path.IsPathRooted(filtreliArgs[i + 1])
                                ? filtreliArgs[i + 1]
                                : ProjeYollari.Csv(filtreliArgs[i + 1]);
                            i++;
                        }
                        else if (filtreliArgs[i].Equals("--limit", StringComparison.OrdinalIgnoreCase) && i + 1 < filtreliArgs.Length
                                 && int.TryParse(filtreliArgs[i + 1], out var n))
                        {
                            serpLimit = n;
                            i++;
                        }
                    }

                    await new SerpApiScraper().CalistirAsync(serpInput, serpLimit);
                    return 0;

                default:
                    Console.WriteLine($"Bilinmeyen komut: {komut}");
                    YardimYaz();
                    return 1;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[-] Hata: {ex.Message}");
            return 1;
        }
    }

    private static void YardimYaz()
    {
        Console.WriteLine("""
            Sirket Veritabani CLI (.NET)

            Kullanim:
              dotnet run --project dotnet/src/SirketVeritabani.Cli -- <komut> [secenekler]

            Komutlar:
              und       UND uye listesini tarar -> und_sirketler.csv
              utikad    UTIKAD uye listesini tarar -> sirketler.csv
              merge     CSV'leri birlestirir -> master_sirketler.csv
              website   Sirket sitelerinden yonetici bilgisi cikar -> yoneticiler.csv
              ddg       DuckDuckGo ile domain/website arar -> ddg_sonuclar.csv
              serpapi   SerpAPI ile LinkedIn yonetici aramasi -> yoneticiler_final.csv

            Secenekler:
              --kok=<yol>           Proje kok dizini (CSV dosyalari burada)
              --input <dosya>       girdi CSV (varsayilan: master_sirketler.csv)
              --limit <n>           max sirket sayisi
              --eksik-domain        ddg: yalnizca domain bos olan sirketler

            Ornekler:
              dotnet run --project dotnet/src/SirketVeritabani.Cli -- merge
              dotnet run --project dotnet/src/SirketVeritabani.Cli -- website --limit 10
              dotnet run --project dotnet/src/SirketVeritabani.Cli -- serpapi --limit 5
            """);
    }
}
