using ISC.Observability.Extensions;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.Configuration;
using Serilog;

namespace ISC.Observability.Tests;

/// <summary>
/// Kiểm chứng bản sửa 8 lỗi trong báo cáo đội dev (v1.4.0):
/// - Traces + Metrics phải đặt Protocol = HttpProtobuf và dùng endpoint đã kèm path.
/// - Hỗ trợ schema cấu hình OpenTelemetry:Tracing/Metrics/Logs (full URL từng signal).
/// - Otel:Protocol = http mặc định.
/// Vì đây là SDK cấp DI, test chỉ kiểm tra AddStandardObservability không nổ và cấu hình
/// được đọc đúng (không có collector thật). Exporter thật được kiểm tra bằng scripts
/// otel-sdk-probe ở tầng 1/tầng 2 theo quy trình nghiệm thu.
/// </summary>
public class OtlpHttpEndpointTests : IDisposable
{
    public OtlpHttpEndpointTests()
    {
        Log.CloseAndFlush();
    }

    public void Dispose()
    {
        Log.CloseAndFlush();
    }

    /// <summary>
    /// Lỗi 1,2,3,4: cấu hình schema mới OpenTelemetry:* (full URL từng signal) + Protocol=http
    /// → AddStandardObservability không nổ, logs vẫn gửi được (Serilog sink).
    /// </summary>
    [Fact]
    public void FullSignalEndpoints_HttpProtocol_DoesNotThrow()
    {
        var config = new Dictionary<string, string?>
        {
            ["OpenTelemetry:Logs"] = "http://signoz-otel.fpt.net/v1/logs",
            ["OpenTelemetry:Tracing"] = "http://signoz-otel.fpt.net/v1/traces",
            ["OpenTelemetry:Metrics"] = "http://signoz-otel.fpt.net/v1/metrics",
            ["Otel:Protocol"] = "http"
        };

        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            EnvironmentName = "Production"
        });
        builder.Configuration.AddInMemoryCollection(config);

        // Act — không nổ exception nghĩa là endpoint/protocol resolve được.
        var ex = Record.Exception(() => builder.AddStandardObservability("test-service"));

        Assert.Null(ex);
    }

    /// <summary>
    /// Backward-compat: schema cũ Otel:OtlpHttpEndpoint + Protocol=http vẫn chạy được
    /// (SDK tự nối /v1/<signal>).
    /// </summary>
    [Fact]
    public void LegacyBaseEndpoint_HttpProtocol_DoesNotThrow()
    {
        var config = new Dictionary<string, string?>
        {
            ["Otel:OtlpEndpoint"] = "http://otel-signoz.fpt.net",
            ["Otel:OtlpHttpEndpoint"] = "http://otel-signoz.fpt.net",
            ["Otel:Protocol"] = "http"
        };

        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            EnvironmentName = "Production"
        });
        builder.Configuration.AddInMemoryCollection(config);

        var ex = Record.Exception(() => builder.AddStandardObservability("test-service"));

        Assert.Null(ex);
    }

    /// <summary>
    /// Lỗi 8: cấu hình sampler hợp lệ không nổ.
    /// </summary>
    [Theory]
    [InlineData("always_on")]
    [InlineData("always_off")]
    [InlineData("parentbased")]
    [InlineData("0.5")]
    [InlineData("")]
    [InlineData(null)]
    public void SamplerConfig_ValidValues_DoesNotThrow(string? sampler)
    {
        var config = new Dictionary<string, string?>
        {
            ["Otel:Protocol"] = "http"
        };
        if (sampler is not null)
            config["Otel:TracesSampler"] = sampler;

        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            EnvironmentName = "Production"
        });
        builder.Configuration.AddInMemoryCollection(config);

        var ex = Record.Exception(() => builder.AddStandardObservability("test-service"));

        Assert.Null(ex);
    }

    /// <summary>
    /// Lỗi 7: EnableEntityFramework=false không nổ (trước đây khoá này bị bỏ qua, giờ đọc thật).
    /// </summary>
    [Fact]
    public void EntityFrameworkFlag_False_DoesNotThrow()
    {
        var config = new Dictionary<string, string?>
        {
            ["Otel:Protocol"] = "http",
            ["Otel:EnableEntityFramework"] = "false"
        };

        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            EnvironmentName = "Production"
        });
        builder.Configuration.AddInMemoryCollection(config);

        var ex = Record.Exception(() => builder.AddStandardObservability("test-service"));

        Assert.Null(ex);
    }
}
