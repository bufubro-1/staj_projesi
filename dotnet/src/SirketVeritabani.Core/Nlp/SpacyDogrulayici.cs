using System.Diagnostics;

namespace SirketVeritabani.Core.Nlp;

/// <summary>
/// spaCy PER doğrulaması için isteğe bağlı Python köprüsü.
/// Python/spaCy yoksa tüm isimler kural filtresinden geçmiş sayılır.
/// </summary>
public sealed class SpacyDogrulayici
{
    private readonly string? _pythonYolu;
    private readonly string _scriptYolu;
    private bool? _spacyKullanilabilir;

    public SpacyDogrulayici(string scriptYolu, string? pythonYolu = null)
    {
        _scriptYolu = scriptYolu;
        _pythonYolu = pythonYolu ?? Environment.GetEnvironmentVariable("PYTHON_PATH") ?? "python3";
    }

    public bool IsimGecerliMi(string metin)
    {
        if (SpacyDeneyebilirMi() && SpacySonucuAl(metin, out var spacyGecerli))
            return spacyGecerli;

        return true;
    }

    private bool SpacyDeneyebilirMi()
    {
        if (_spacyKullanilabilir.HasValue)
            return _spacyKullanilabilir.Value;

        if (!File.Exists(_scriptYolu))
        {
            _spacyKullanilabilir = false;
            return false;
        }

        _spacyKullanilabilir = true;
        return true;
    }

    private bool SpacySonucuAl(string metin, out bool gecerli)
    {
        gecerli = true;

        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = _pythonYolu!,
                Arguments = $"\"{_scriptYolu}\" \"{metin.Replace("\"", "\\\"")}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            if (process == null)
            {
                _spacyKullanilabilir = false;
                return false;
            }

            var output = process.StandardOutput.ReadToEnd().Trim();
            process.WaitForExit(TimeSpan.FromSeconds(15));

            if (process.ExitCode != 0)
            {
                _spacyKullanilabilir = false;
                return false;
            }

            gecerli = output.Equals("true", StringComparison.OrdinalIgnoreCase);
            return true;
        }
        catch
        {
            _spacyKullanilabilir = false;
            return false;
        }
    }
}
