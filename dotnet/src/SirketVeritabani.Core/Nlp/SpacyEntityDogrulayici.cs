using System.Diagnostics;
using System.Text.Json;

namespace SirketVeritabani.Core.Nlp;

public sealed class SpacyEntityDogrulayici
{
    private readonly string _scriptYolu;
    private readonly string? _pythonYolu;
    private bool? _kullanilabilir;

    public SpacyEntityDogrulayici(string scriptYolu, string? pythonYolu = null)
    {
        _scriptYolu = scriptYolu;
        _pythonYolu = pythonYolu ?? Environment.GetEnvironmentVariable("PYTHON_PATH") ?? "python3";
    }

    public (bool IsPer, bool IsOrg) EntityKontrol(string metin)
    {
        if (!DeneyebilirMi() || !SonucAl(metin, out var isPer, out var isOrg))
            return (false, false);

        return (isPer, isOrg);
    }

    private bool DeneyebilirMi()
    {
        if (_kullanilabilir.HasValue)
            return _kullanilabilir.Value;

        _kullanilabilir = File.Exists(_scriptYolu);
        return _kullanilabilir.Value;
    }

    private bool SonucAl(string metin, out bool isPer, out bool isOrg)
    {
        isPer = false;
        isOrg = false;

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
                _kullanilabilir = false;
                return false;
            }

            var output = process.StandardOutput.ReadToEnd().Trim();
            process.WaitForExit(TimeSpan.FromSeconds(15));

            if (process.ExitCode != 0)
            {
                _kullanilabilir = false;
                return false;
            }

            using var doc = JsonDocument.Parse(output);
            isPer = doc.RootElement.GetProperty("is_per").GetBoolean();
            isOrg = doc.RootElement.GetProperty("is_org").GetBoolean();
            return true;
        }
        catch
        {
            _kullanilabilir = false;
            return false;
        }
    }
}
