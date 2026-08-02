using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

using System.Reflection;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using Serilog;
using Serilog.Events;
using Serilog.Sinks.OpenTelemetry;
using ISC.Observability.Metadata;
using ISC.Observability.Middleware;
using ISC.Observability.Telemetry;

namespace ISC.Observability.Extensions
{
    public static class ObservabilityExtensions
    {
        public static IHostApplicationBuilder AddStandardObservability(this IHostApplicationBuilder builder, string defaultServiceName, Action<LoggerConfiguration>? configureLogger = null)
        {
            var serviceName = builder.Configuration["ServiceName"] ?? defaultServiceName;

            // Lưu serviceName đã resolve vào config để các hosted service (ComplianceMetricsService) đọc được,
            // vì hosted service không có access vào tham số defaultServiceName.
            builder.Configuration["ISC:Observability:ResolvedServiceName"] = serviceName;
            
            var assembly = Assembly.GetEntryAssembly();
            var autoVersion = assembly?.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion 
                              ?? assembly?.GetName().Version?.ToString() 
                              ?? "1.0.0";
            var serviceVersion = builder.Configuration["ServiceVersion"] ?? Environment.GetEnvironmentVariable("APP_VERSION") ?? autoVersion;
            
            var otlpGrpcEndpoint = builder.Configuration["Otel:OtlpEndpoint"] ?? "http://localhost:4317";
            var otlpHttpEndpoint = builder.Configuration["Otel:OtlpHttpEndpoint"] ?? "http://localhost:4318";
            var environment = builder.Environment.EnvironmentName;

            // Đọc cấu hình Feature Flags
            var enableRedis = builder.Configuration.GetValue<bool>("Otel:EnableRedis", false);
            var enableGrpc = builder.Configuration.GetValue<bool>("Otel:EnableGrpc", false);
            var enableQuartz = builder.Configuration.GetValue<bool>("Otel:EnableQuartz", false);
            var enableMongo = builder.Configuration.GetValue<bool>("Otel:EnableMongo", false);
            var enableMassTransit = builder.Configuration.GetValue<bool>("Otel:EnableMassTransit", false);



            // ==========================================
            // 1. SERILOG CONFIGURATION (Structured Logging)
            // ==========================================
            
            // Console Sink: Tự động điều chỉnh theo môi trường
            // - Development/Local: Bật mặc định, format plain text cho dev đọc
            // - Production/Staging: Tắt mặc định (đã có OTel Sink), opt-in qua "Serilog:Console:Enabled": true
            var consoleLevelStr = builder.Configuration["Serilog:Console:RestrictedToMinimumLevel"];
            var consoleLevel = Enum.TryParse<LogEventLevel>(consoleLevelStr, true, out var parsedLevel) 
                ? parsedLevel 
                : LogEventLevel.Information;

            var isDevEnvironment = builder.Environment.IsDevelopment() 
                || string.Equals(environment, "Local", StringComparison.OrdinalIgnoreCase);
            var consoleSinkEnabled = builder.Configuration["Serilog:Console:Enabled"] is { } enabledStr
                && bool.TryParse(enabledStr, out var enabledParsed)
                ? enabledParsed
                : isDevEnvironment;

            // SDK đặt mặc định hợp lý, Dev có thể override qua appsettings.json section "Serilog"
            var logConfig = new LoggerConfiguration()
                .ReadFrom.Configuration(builder.Configuration)  // Cho phép Dev override từ appsettings.json
                .MinimumLevel.Override("Microsoft", LogEventLevel.Warning)
                .MinimumLevel.Override("Microsoft.Hosting.Lifetime", LogEventLevel.Information)
                .MinimumLevel.Override("System", LogEventLevel.Warning)
                .Enrich.FromLogContext()
                .Enrich.WithProperty("Environment", environment)
                .Enrich.WithProperty("ServiceName", serviceName)
                .Enrich.WithProperty("ApplicationVersion", serviceVersion)
                .Enrich.WithMachineName()
                .Enrich.WithThreadId()
                .Enrich.With<PiiMaskingEnricher>();

            // Console Sink: Chỉ bật khi cần
            if (consoleSinkEnabled)
            {
                if (isDevEnvironment)
                {
                    // Dev: Format plain text cho mắt người
                    logConfig.WriteTo.Console(
                        outputTemplate: "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj}{NewLine}{Exception}",
                        restrictedToMinimumLevel: consoleLevel);
                }
                else
                {
                    // Non-Dev (opt-in): JSON cho container log scraping
                    logConfig.WriteTo.Console(
                        formatter: new Serilog.Formatting.Compact.RenderedCompactJsonFormatter(),
                        restrictedToMinimumLevel: consoleLevel);
                }
            }

            // OpenTelemetry Sink: Luôn bắn log qua OTLP về OTel Collector
            logConfig.WriteTo.OpenTelemetry(options =>
            {
                options.Endpoint = $"{otlpHttpEndpoint}/v1/logs";
                options.Protocol = OtlpProtocol.HttpProtobuf;
                options.ResourceAttributes = new Dictionary<string, object>
                {
                    ["service.name"] = serviceName,
                    ["service.version"] = serviceVersion,
                    ["deployment.environment"] = environment
                };
            });

            // Nếu Dev không cấu hình MinimumLevel trong appsettings.json,
            // SDK tự đặt mặc định là Information
            if (builder.Configuration.GetSection("Serilog:MinimumLevel").Value == null
                && builder.Configuration.GetSection("Serilog:MinimumLevel:Default").Value == null)
            {
                logConfig.MinimumLevel.Information();
            }

            // Gọi Callback để Dev có thể tự custom Filter (nếu có truyền vào)
            configureLogger?.Invoke(logConfig);

            Log.Logger = logConfig.CreateLogger();

            // ==========================================
            // QA COMPLIANCE TRACKING
            // ==========================================
            Log.Information("Standard Observability SDK initialized for {ServiceName} with Environment {Environment}. [Compliance=True]", serviceName, environment);

            builder.Services.AddSerilog();

            // ==========================================
            // QA COMPLIANCE TRACKING (Hosted Service)
            // ==========================================
            // Registered as IHostedService so Counter.Add() runs AFTER MeterProvider is initialized.
            // This fixes the no-op bug where metrics were lost because Add() was called before Build().
            builder.Services.AddHostedService<ComplianceMetricsService>();

            // Configure Propagators (W3C + B3 for Istio/Envoy mesh compatibility)
            OpenTelemetry.Sdk.SetDefaultTextMapPropagator(new OpenTelemetry.Context.Propagation.CompositeTextMapPropagator(new OpenTelemetry.Context.Propagation.TextMapPropagator[]
            {
                new OpenTelemetry.Context.Propagation.TraceContextPropagator(),
                new OpenTelemetry.Context.Propagation.B3Propagator(),
                new OpenTelemetry.Context.Propagation.BaggagePropagator()
            }));

            // ==========================================
            // 2. OPENTELEMETRY CONFIGURATION (Traces & Metrics)
            // ==========================================
            var resourceBuilder = ResourceBuilder.CreateDefault()
                .AddService(serviceName, serviceVersion: serviceVersion)
                .AddAttributes(new[]
                {
                    new KeyValuePair<string, object>("deployment.environment", environment)
                });

            builder.Services.AddOpenTelemetry()
                .WithTracing(tracing =>
                {
                    tracing
                        .SetResourceBuilder(resourceBuilder)
                        .AddAspNetCoreInstrumentation(options =>
                        {
                            options.RecordException = true;
                        })
                        .AddHttpClientInstrumentation()
                        .AddSqlClientInstrumentation(options =>
                        {
                            options.RecordException = true;
                        })
                        .AddEntityFrameworkCoreInstrumentation();

                    // Cấu hình linh hoạt qua Feature Flags
                    if (enableRedis) tracing.AddRedisInstrumentation();
                    if (enableGrpc) tracing.AddGrpcClientInstrumentation();
                    if (enableQuartz) tracing.AddQuartzInstrumentation();
                    if (enableMongo) tracing.AddSource("MongoDB.Driver.Core.Extensions.DiagnosticSources");
                    if (enableMassTransit) tracing.AddSource("MassTransit");

                    tracing
                        .AddSource(serviceName)
                        .AddSource("*") // Wildcard: Capture all custom ActivitySources created by Devs
                        .AddOtlpExporter(opt =>
                        {
                            opt.Endpoint = new Uri(otlpGrpcEndpoint);
                        });
                })
                .WithMetrics(metrics =>
                {
                    metrics
                        .SetResourceBuilder(resourceBuilder)
                        .AddAspNetCoreInstrumentation()
                        .AddHttpClientInstrumentation()
                        .AddRuntimeInstrumentation()
                        .AddMeter(serviceName)
                        .AddMeter("ISC.Observability.Compliance") // QA Compliance Meter
                        .AddOtlpExporter(opt =>
                        {
                            opt.Endpoint = new Uri(otlpGrpcEndpoint);
                        });
                });

            return builder;
        }

        public static IApplicationBuilder UseStandardObservability(this IApplicationBuilder app)
        {
            app.UseMiddleware<CorrelationIdMiddleware>();
            app.UseMiddleware<GlobalExceptionMiddleware>();
            app.UseSerilogRequestLogging(options =>
            {
                // Type-safe log level control: Hạ cấp log thay vì xóa sổ
                options.GetLevel = (httpContext, elapsed, ex) =>
                {
                    // Lỗi luôn phải báo động, bất kể endpoint nào
                    if (ex != null || httpContext.Response.StatusCode >= 500)
                        return LogEventLevel.Error;

                    // Kiểm tra TYPE metadata (compile-time safe, zero string comparison)
                    var endpoint = httpContext.GetEndpoint();
                    if (endpoint?.Metadata.GetMetadata<SuppressRequestLoggingMetadata>() != null)
                        return LogEventLevel.Verbose; // Hạ cấp, không xóa sổ

                    return LogEventLevel.Information;
                };

                options.EnrichDiagnosticContext = (diagnosticContext, httpContext) =>
                {
                    diagnosticContext.Set("RequestHost", httpContext.Request.Host.Value);
                    diagnosticContext.Set("UserAgent", httpContext.Request.Headers["User-Agent"]!.ToString());
                };
            });

            return app;
        }
    }
}
