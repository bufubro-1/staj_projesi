using System.Text.Json;

namespace SirketVeritabani.Core.SerpApi;

public sealed class SerpApiClient : IDisposable
{
    private readonly HttpClient _client = new() { Timeout = TimeSpan.FromSeconds(30) };
    private readonly string _apiKey;

    public SerpApiClient(string apiKey) => _apiKey = apiKey;

    public async Task<IReadOnlyList<SerpApiOrganikSonuc>> AraAsync(string sorgu, CancellationToken ct = default)
    {
        var url = "https://serpapi.com/search.json?" +
                  $"engine=google&q={Uri.EscapeDataString(sorgu)}&gl=tr&hl=tr&num=15&api_key={Uri.EscapeDataString(_apiKey)}";

        using var response = await _client.GetAsync(url, ct);
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync(ct);
        using var doc = JsonDocument.Parse(json);

        if (!doc.RootElement.TryGetProperty("organic_results", out var organic))
            return [];

        var sonuclar = new List<SerpApiOrganikSonuc>();
        foreach (var item in organic.EnumerateArray())
        {
            sonuclar.Add(new SerpApiOrganikSonuc
            {
                Baslik = item.TryGetProperty("title", out var t) ? t.GetString() ?? "" : "",
                Link = item.TryGetProperty("link", out var l) ? l.GetString() ?? "" : "",
                Snippet = item.TryGetProperty("snippet", out var s) ? s.GetString() ?? "" : ""
            });
        }

        return sonuclar;
    }

    public void Dispose() => _client.Dispose();
}

public sealed class SerpApiOrganikSonuc
{
    public string Baslik { get; set; } = string.Empty;
    public string Link { get; set; } = string.Empty;
    public string Snippet { get; set; } = string.Empty;
}
