namespace SirketVeritabani.Core.Http;

public sealed class ScraperHttpClient : IDisposable
{
    private static readonly string UserAgent =
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

    private readonly HttpClient _client;

    public ScraperHttpClient()
    {
        _client = new HttpClient
        {
            Timeout = TimeSpan.FromSeconds(10)
        };
        _client.DefaultRequestHeaders.TryAddWithoutValidation("User-Agent", UserAgent);
        _client.DefaultRequestHeaders.TryAddWithoutValidation("Accept-Language", "tr-TR,tr;q=0.9,en;q=0.8");
    }

    public async Task<string?> SayfaAlAsync(string url, CancellationToken ct = default)
    {
        try
        {
            using var response = await _client.GetAsync(url, ct);
            if (response.IsSuccessStatusCode)
                return await response.Content.ReadAsStringAsync(ct);
        }
        catch
        {
            // Tek kayıt hatası — devam
        }

        return null;
    }

    public void Dispose() => _client.Dispose();
}
