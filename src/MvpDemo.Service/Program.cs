using Serilog;
using MvpDemo.Service.Services;
using ISC.Observability.Extensions;
using System.Text.Json.Serialization;

var builder = WebApplication.CreateBuilder(args);

// ==========================================
// 1 & 2. OBSERVABILITY CONFIGURATION
// ==========================================
// This single line sets up Serilog, OpenTelemetry Traces & Metrics perfectly
builder.AddStandardObservability("mvp-demo-service");

// ==========================================
// 3. SERVICES REGISTRATION
// ==========================================
builder.Services.AddSingleton<OrderService>();
builder.Services.AddHealthChecks();
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter());
        options.JsonSerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase;
    });
builder.Services.AddEndpointsApiExplorer();

// ==========================================
// BUILD APP
// ==========================================
var app = builder.Build();

// ==========================================
// 4. MIDDLEWARE PIPELINE
// ==========================================
// This single line adds CorrelationId, GlobalException, and Serilog Request Logging
app.UseStandardObservability();

// ==========================================
// 5. ENDPOINTS
// ==========================================
app.MapHealthChecks("/healthz");  // Liveness probe
app.MapHealthChecks("/ready");    // Readiness probe

// Root endpoint - service info
app.MapGet("/", () => Results.Ok(new
{
    service = "mvp-demo-service",
    version = "1.0.0",
    environment = app.Environment.EnvironmentName,
    status = "running",
    endpoints = new
    {
        health = "/healthz",
        ready = "/ready",
        orders = "/api/orders",
        simulateError = "/api/orders/simulate-error",
        demoPii = "/api/orders/demo-pii"
    }
}));

app.MapControllers();

// ==========================================
// 6. RUN
// ==========================================
try
{
    Log.Information("{ServiceName} is ready. Listening on {Urls}",
        "mvp-demo-service", string.Join(", ", app.Urls));
    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "{ServiceName} terminated unexpectedly", "mvp-demo-service");
}
finally
{
    Log.CloseAndFlush();
}
