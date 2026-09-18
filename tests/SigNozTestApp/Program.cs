using System.Diagnostics;
using System.Diagnostics.Metrics;
using ISC.Observability.Extensions;
using Serilog;

var builder = WebApplication.CreateBuilder(args);

// Cấu hình OTLP Endpoint về SigNoz
builder.Configuration["ServiceName"] = "signoz-test-service";
builder.Configuration["ServiceVersion"] = "1.3.2";
builder.Configuration["Otel:OtlpEndpoint"] = "http://localhost:4317";
builder.Configuration["Otel:OtlpHttpEndpoint"] = "http://localhost:4318";

// 1. Dùng SDK ISC.Observability v1.3.2
builder.AddStandardObservability("signoz-test-service");

// Custom Meter & ActivitySource để test
var customMeter = new Meter("signoz-test-service");
var customCounter = customMeter.CreateCounter<int>("test.counter.hits", description: "Test counter for SigNoz verification");

var customActivitySource = new ActivitySource("MyCustomDevSource");

builder.Services.AddHttpClient();

var app = builder.Build();

// 2. Add middleware
app.UseStandardObservability();

// 3. Test Endpoints
app.MapGet("/", () => Results.Ok(new { status = "running", service = "signoz-test-service", version = "1.3.2" }));

// Endpoint test 1: HTTP Client & Custom Span (Tracing & Metrics)
app.MapGet("/api/test-trace", async (HttpClient httpClient, ILogger<Program> logger) =>
{
    customCounter.Add(1, new KeyValuePair<string, object?>("endpoint", "/api/test-trace"));
    logger.LogInformation("Testing Trace propagation and Custom ActivitySource...");

    // Custom Span do Dev tạo bằng Custom ActivitySource
    using (var activity = customActivitySource.StartActivity("CustomDevOperation"))
    {
        activity?.SetTag("custom.tag", "SigNozTestValue");

        // Call HTTP ngoài để sinh Client Span
        try
        {
            var response = await httpClient.GetAsync("https://httpbin.org/get");
            logger.LogInformation("Outbound HTTP GET status: {StatusCode}", response.StatusCode);
        }
        catch (Exception ex)
        {
            logger.LogWarning(ex, "Outbound HTTP failed (network offline?), continuing test");
        }
    }

    return Results.Ok(new { message = "Trace test executed successfully" });
});

// Endpoint test 2: PII Logging Test (Logging)
app.MapGet("/api/test-pii", (ILogger<Program> logger) =>
{
    logger.LogInformation("Logging user action with sensitive data: Password = {Password}, CreditCard = {CreditCard}, UserToken = {Token}",
        "Secret123!", "4532789012345678", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9");

    return Results.Ok(new { message = "PII logging test executed" });
});

// Endpoint test 3: Simulated Error Test (GlobalException & Error Span)
app.MapGet("/api/test-error", (ILogger<Program> logger) =>
{
    logger.LogError("Simulating unhandled exception for SigNoz error tracking");
    throw new InvalidOperationException("Simulated exception for SigNoz verification test");
});

Log.Information("SigNozTestApp starting on http://localhost:5150...");
app.Run("http://localhost:5150");
