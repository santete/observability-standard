# ISC.Observability SDK

Standard Observability SDK for .NET 6 / .NET 7 / .NET 8 microservices. One line of code wires up structured logging, distributed tracing, and metrics (OpenTelemetry + Serilog) to the central OTel Collector — no sink configuration, no boilerplate.

## Features

- **Multi-targeting** — `net6.0`, `net7.0`, `net8.0`. Supports `WebApplicationBuilder`, `IHostApplicationBuilder`, and `IServiceCollection`/`Startup.cs`.
- **Tracing** — automatic W3C trace context propagation across HTTP in/out, with a composite W3C + B3 + Baggage propagator for Istio/Envoy service meshes.
- **Structured logging** — Serilog, 100% `snake_case` JSON fields, `trace_id`/`span_id` auto-attached to every log line.
- **Global exception handling** — unhandled exceptions are caught, logged at `ERROR` with full stack trace, and marked on the active span.
- **PII masking** — sensitive fields (password, token, email, phone, card number...) are masked automatically before any log leaves the process. Zero-allocation (cached per property name).
- **Business event routing to Kafka** — mark a log as a business event and pick its destination Kafka topic from code; the OTel Collector does the actual routing (see [Business Event Logging](#business-event-logging-kafka-routing)).
- **Runtime & HTTP metrics** — RPS, latency, error rate, CPU/RAM, GC, ThreadPool.
- **OTLP-only egress** — the SDK never writes to a file, Kafka, or Elasticsearch directly. Everything goes out over OTLP to the Collector.

## Supported instrumentations

All opt-in except HTTP and EF Core, toggled via config — no code changes required.

| Instrumentation | Config flag | Default |
|---|---|---|
| ASP.NET Core + HttpClient | — | always on |
| Entity Framework Core (SQL Server, Postgres, MySQL...) | `Otel:EnableEntityFramework` | `true` |
| Redis (StackExchange.Redis) | `Otel:EnableRedis` | `false` |
| MongoDB | `Otel:EnableMongo` | `false` |
| Message brokers (MassTransit / Kafka / RabbitMQ) | `Otel:EnableMassTransit` | `false` |
| Quartz.NET background jobs | `Otel:EnableQuartz` | `false` |
| gRPC client | `Otel:EnableGrpc` | `false` |

## Installation

```bash
dotnet add package ISC.Observability
```

Remove any existing `Serilog.Sinks.*` packages (`Console`, `File`...) from the project — the SDK configures its own sinks and a second one will conflict.

## Quick start

```csharp
using ISC.Observability.Extensions;

var builder = WebApplication.CreateBuilder(args);

builder.AddStandardObservability("MyService");   // 1. logging + tracing + metrics

builder.Services.AddControllers();

var app = builder.Build();

app.UseStandardObservability();                  // 2. CorrelationId + GlobalException + request logging

app.MapHealthChecks("/health").SuppressRequestLogging();
app.MapHealthChecks("/ready").SuppressRequestLogging();

app.MapControllers();
app.Run();
```

## Configuration

Everything below is read from `appsettings.json` / environment variables — no code changes.

**OTLP endpoint — two ways to configure it:**

```json
// A) Full per-signal URL (recommended — matches ISC infra, port 80)
{
  "ServiceName": "Payment.Service",
  "ServiceVersion": "1.2.0",
  "OpenTelemetry": {
    "Logs":    "http://otel-collector.internal/v1/logs",
    "Tracing": "http://otel-collector.internal/v1/traces",
    "Metrics": "http://otel-collector.internal/v1/metrics"
  },
  "Otel": { "Protocol": "http", "EnableRedis": true, "EnableMongo": true }
}
```

```json
// B) Base endpoint, SDK appends /v1/<signal> (backward-compatible with v1.3.x)
{
  "ServiceName": "Payment.Service",
  "Otel": {
    "OtlpHttpEndpoint": "http://otel-collector:4318",
    "Protocol": "http"
  }
}
```

| Key | Default | Description |
|---|---|---|
| `Otel:Protocol` | `http` | `http` or `grpc`. Default `http`: ISC infra only opens OTLP/HTTP (port 80/4318). |
| `OpenTelemetry:Logs`/`Tracing`/`Metrics` | — | Full per-signal URL, path included. Highest priority; SDK does not append anything. |
| `Otel:OtlpEndpoint` | `http://localhost:4317` | gRPC base (fallback, `Protocol=grpc`). |
| `Otel:OtlpHttpEndpoint` | `http://localhost:4318` | HTTP base (fallback, `Protocol=http`); SDK appends `/v1/<signal>`. |
| `OpenTelemetry:IngestionKey` | — | Sent as `Authorization: Bearer <key>` header, if set. |
| `Otel:TracesSampler` | `always_on` | `always_on` \| `always_off` \| `parentbased` \| a ratio `0.0`-`1.0`. |
| `Otel:CustomSources` | — | Comma-separated `ActivitySource` names. Empty → wildcard `*` (capture everything). |
| `Otel:Enable{Redis,Mongo,MassTransit,Grpc,Quartz,EntityFramework}` | see table above | Per-instrumentation toggle. |

## Logging

### Standard logging

Use `ILogger<T>` as usual — the SDK attaches `trace_id`, `span_id`, `service_name`, `environment`, `correlation_id` and masks PII automatically.

```csharp
_logger.LogInformation("Processing order {order_id} for {customer_email}", order.Id, order.Email);
// customer_email is masked in the emitted log ("n***@g***.com") — PiiMaskingEnricher runs on every event.
```

> [!IMPORTANT]
> **Field naming (`R-OBS-FIELD-001`):** every property is `snake_case` — system fields (`service_name`, `trace_id`, `request_id`...) and business fields alike (`order_id`, `customer_name`, `total_amount`). No PascalCase, no camelCase.

### Business event logging (Kafka routing)

Mark a log as a business event and name the Kafka topic it should go to — the SDK never touches Kafka directly; it only tags the log, and the OTel Collector does the actual routing.

```csharp
using ISC.Observability.Logging;

using (BusinessLog.Begin("order-events"))
{
    _logger.LogInformation(
        "Order {order_id} processed successfully, amount {total_amount}",
        order.Id, order.TotalAmount);
}
```

Everything logged inside the `using` block gets two extra fields: `log_category=business` and `kafka_topic=order-events`. Exit the block (or `Dispose()`) and subsequent logs are untagged again.

Requires SDK **v1.6.0+**. Three things to know:

1. **The topic name must exist as a declared route on the OTel Collector** (`otel-collector-config.yml`, owned by DevOps). An undeclared/misspelled topic is never silently lost — the log just stays in Elasticsearch/Kibana as a safety net instead of reaching Kafka.
2. **Routing is exclusive, not dual-write**: once a topic is declared, matching logs are removed from the Elasticsearch pipeline entirely — they are no longer searchable in Kibana by `trace_id`, only consumable from Kafka.
3. Wrap only the specific log line(s) that are the actual business event — don't leave the scope open across a whole request, or unrelated technical logs will get tagged too.

See the project root `README.md` and `otel-collector-config.yml` for how DevOps wires a topic route (this package has no control over broker addresses, clusters, or Collector config).

### Noise filtering

Third-party libraries (EF Core, HttpClient, Hangfire...) log a lot at `Information`. Override per namespace in `appsettings.json` (since v1.0.5):

```json
{
  "Serilog": {
    "MinimumLevel": {
      "Default": "Information",
      "Override": {
        "Microsoft.EntityFrameworkCore": "Warning",
        "System.Net.Http.HttpClient": "Warning",
        "MassTransit": "Warning"
      }
    }
  }
}
```

For anything a namespace override can't express (e.g. filtering by `EventId`), pass a callback:

```csharp
builder.AddStandardObservability("MyService", loggerConfig =>
{
    loggerConfig.Filter.ByExcluding(e =>
        e.Properties.TryGetValue("EventId", out var id) && id.ToString().Contains("ExecutionAttempt"));
});
```

### Suppressing noisy endpoints

Use `.SuppressRequestLogging()` on any endpoint (not just health checks) to downgrade its request log to `Verbose` — it disappears from Kibana/Console, but **errors on it are never suppressed**: HTTP ≥ 500 or an exception always logs at `Error` regardless.

```csharp
app.MapHealthChecks("/health").SuppressRequestLogging();
app.MapGet("/internal/ping", () => "pong").SuppressRequestLogging();
```

This is a type-safe endpoint metadata marker, not a URL string match — zero allocation per request (benchmarked at 0 bytes vs. 40 bytes/request for the old URL-filter approach).

### Console sink

| Environment | Console sink | Format |
|---|---|---|
| `Development` / `Local` | On by default | Plain text |
| `Production` / `Staging` / other | Off by default | — (OTel sink already covers it) |

Override either way via config:

```json
{ "Serilog": { "Console": { "Enabled": true, "RestrictedToMinimumLevel": "Warning" } } }
```

> [!CAUTION]
> **No direct external sinks.** The SDK's only egress is OTLP to the Collector — never configure `WriteTo.Kafka()`, `WriteTo.Elasticsearch()`, or `WriteTo.File()` in application code. The sanctioned way to get a log into Kafka is `BusinessLog.Begin(...)` above, routed by the Collector — not a sink in your code.

## Custom spans

For a business-logic function worth its own entry in the Kibana APM waterfall:

```csharp
private static readonly ActivitySource MyActivitySource = new("Payment.Service");

public void ProcessLargeData()
{
    using var activity = MyActivitySource.StartActivity("ProcessLargeData.CalculateHash");
    activity?.SetTag("data.size", "150MB");

    try
    {
        // ...
        activity?.SetStatus(ActivityStatusCode.Ok);
    }
    catch (Exception ex)
    {
        activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
        throw;
    }
}
```

No extra package needed — `System.Diagnostics` is built into .NET.

## QA compliance signal

On successful startup, the SDK emits a log line and the `observability.sdk.active` metric. The **QA Compliance Tracker** dashboard uses this to confirm a service is integrated before it's allowed to release to Production.
