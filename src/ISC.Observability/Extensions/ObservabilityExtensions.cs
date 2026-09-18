using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

using System.Globalization;
using System.Reflection;
using OpenTelemetry;
using OpenTelemetry.Exporter;
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
            
            var environment = builder.Environment.EnvironmentName;

            // Đọc cấu hình Feature Flags
            var enableRedis = builder.Configuration.GetValue<bool>("Otel:EnableRedis", false);
            var enableGrpc = builder.Configuration.GetValue<bool>("Otel:EnableGrpc", false);
            var enableQuartz = builder.Configuration.GetValue<bool>("Otel:EnableQuartz", false);
            var enableMongo = builder.Configuration.GetValue<bool>("Otel:EnableMongo", false);
            var enableMassTransit = builder.Configuration.GetValue<bool>("Otel:EnableMassTransit", false);
            // Lỗi 7: EF Core giờ thật sự đọc feature flag (trước đây bật vô điều kiện, README nói dối).
            var enableEntityFramework = builder.Configuration.GetValue<bool>("Otel:EnableEntityFramework", true);

            // Lỗi 3: chọn protocol. Mặc định http vì hạ tầng ISC chỉ mở OTLP/HTTP cổng 80.
            var protocolStr = builder.Configuration["Otel:Protocol"] ?? "http";
            var useHttp = protocolStr.Equals("http", StringComparison.OrdinalIgnoreCase);

            // Lỗi 6: cho lọc ActivitySource thay vì AddSource("*") vô điều kiện.
            var customSourcesRaw = builder.Configuration["Otel:CustomSources"];

            // Lỗi 8: chọn sampler.
            var samplerStr = builder.Configuration["Otel:TracesSampler"];

            // Ingestion key (tuỳ chọn, dùng làm header auth cho exporter nếu khác rỗng).
            var ingestionKey = builder.Configuration["OpenTelemetry:IngestionKey"];

            // Giải quyết endpoint cho từng signal.
            // Ưu tiên 1: OpenTelemetry:<Signal> — full URL đã kèm path (vd http://host/v1/traces).
            //            Khi đó SDK KHÔNG hardcode path → OTel đổi keyword (/v2/traces...) vẫn dùng được.
            // Ưu tiên 2 (fallback, protocol=http): Otel:OtlpHttpEndpoint + "/v1/<signal>".
            // Ưu tiên 3 (fallback, protocol=grpc): Otel:OtlpEndpoint (base, gRPC tự nối path).
            var (tracesEndpoint, tracesHttp) = ResolveOtlpEndpoint(builder.Configuration, "OpenTelemetry:Tracing", "v1/traces", useHttp);
            var (metricsEndpoint, metricsHttp) = ResolveOtlpEndpoint(builder.Configuration, "OpenTelemetry:Metrics", "v1/metrics", useHttp);
            var (logsEndpoint, _) = ResolveOtlpEndpoint(builder.Configuration, "OpenTelemetry:Logs", "v1/logs", useHttp);


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
                // 100% snake_case chuẩn R-OBS-FIELD-001 duy nhất, không nhân đôi thuộc tính
                .Enrich.WithProperty("environment", environment)
                .Enrich.WithProperty("service_name", serviceName)
                .Enrich.WithProperty("application_version", serviceVersion)
                .Enrich.With<SnakeCaseSystemEnricher>()
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

            // OpenTelemetry Sink: Luôn bắn log qua OTLP về OTel Collector (HTTP).
            logConfig.WriteTo.OpenTelemetry(options =>
            {
                options.Endpoint = logsEndpoint;        // full URL đã kèm path /v1/logs
                options.Protocol = OtlpProtocol.HttpProtobuf;
                options.ResourceAttributes = new Dictionary<string, object>
                {
                    ["service.name"] = serviceName,
                    ["service.version"] = serviceVersion,
                    ["deployment.environment"] = environment
                };
                if (!string.IsNullOrWhiteSpace(ingestionKey))
                    options.Headers = new Dictionary<string, string> { ["Authorization"] = $"Bearer {ingestionKey}" };
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

            // Lỗi 5: self-diagnostics — exporter không còn "chết câm".
            // EventListener này lắng nghe EventSource của OTel exporter và log Warning ra Serilog
            // mỗi khi export thất bại. Phải tạo sớm (trước Build) để kịp subscribe EventSource.
            OtlpExporterDiagnostics.Start();

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
                        // Lỗi 8: sampler cấu hình được; mặc định AlwaysOn để APM xuất hiện ngay
                        // kể cả khi ingress gắn traceparent sampled=00.
                        .SetSampler(ParseSampler(samplerStr))
                        .AddAspNetCoreInstrumentation(options =>
                        {
                            options.RecordException = true;
                        })
                        .AddHttpClientInstrumentation()
                        .AddSqlClientInstrumentation(options =>
                        {
                            options.RecordException = true;
                        });

                    // Lỗi 7: EF Core chỉ bật khi feature flag = true (mặc định true).
                    if (enableEntityFramework)
                        tracing.AddEntityFrameworkCoreInstrumentation();

                    // Cấu hình linh hoạt qua Feature Flags
                    if (enableRedis) tracing.AddRedisInstrumentation();
                    if (enableGrpc) tracing.AddGrpcClientInstrumentation();
                    if (enableQuartz) tracing.AddQuartzInstrumentation();
                    if (enableMongo) tracing.AddSource("MongoDB.Driver.Core.Extensions.DiagnosticSources");
                    if (enableMassTransit) tracing.AddSource("MassTransit");

                    tracing.AddSource(serviceName);

                    // Lỗi 6: cho khai danh sách source qua Otel:CustomSources;
                    // chỉ dùng wildcard "*" khi không cấu hình (giữ mặc định cũ).
                    if (!string.IsNullOrWhiteSpace(customSourcesRaw))
                    {
                        foreach (var src in customSourcesRaw.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
                            tracing.AddSource(src);
                    }
                    else
                    {
                        tracing.AddSource("*"); // Wildcard: Capture all custom ActivitySources created by Devs
                    }

                    // Lỗi 1 & 4: traces đặt Protocol tường minh + dùng endpoint đã kèm path khi HTTP.
                    // Lỗi bẫy options name: dùng name riêng "otlp-traces" để delegate không bị metrics ghi đè.
                    tracing.AddOtlpExporter(name: "otlp-traces", opt =>
                    {
                        opt.Endpoint = new Uri(tracesEndpoint);
                        opt.Protocol = tracesHttp ? OtlpExportProtocol.HttpProtobuf : OtlpExportProtocol.Grpc;
                        if (!string.IsNullOrWhiteSpace(ingestionKey))
                            opt.Headers = $"Authorization=Bearer {ingestionKey}";
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
                        .AddMeter("ISC.Observability.Compliance"); // QA Compliance Meter

                    // Lỗi 2 & 4: metrics đặt Protocol tường minh + dùng endpoint đã kèm path khi HTTP.
                    // Bẫy options name: name riêng "otlp-metrics" — cùng name thì delegate sau ghi đè endpoint trước.
                    metrics.AddOtlpExporter(name: "otlp-metrics", opt =>
                    {
                        opt.Endpoint = new Uri(metricsEndpoint);
                        opt.Protocol = metricsHttp ? OtlpExportProtocol.HttpProtobuf : OtlpExportProtocol.Grpc;
                        if (!string.IsNullOrWhiteSpace(ingestionKey))
                            opt.Headers = $"Authorization=Bearer {ingestionKey}";
                    });
                });

            return builder;
        }

        /// <summary>
        /// Giải quyết endpoint OTLP cho một signal, theo thứ tự ưu tiên:
        /// 1) <paramref name="fullEndpointKey"/> (vd "OpenTelemetry:Tracing") — full URL đã kèm path.
        ///    Khi dùng full URL, protocol = HttpProtobuf (đây là HTTP URL có path).
        ///    KHÔNG hardcode path → OTel đổi keyword (/v2/traces...) vẫn dùng được.
        /// 2) Otel:OtlpHttpEndpoint + "/{signalPath}" khi protocol = http (fallback, backward-compat).
        /// 3) Otel:OtlpEndpoint (base gRPC, gRPC tự nối path) khi protocol = grpc.
        /// Trả về (endpoint URL string, isHttp).
        /// </summary>
        private static (string endpoint, bool isHttp) ResolveOtlpEndpoint(IConfiguration config, string fullEndpointKey, string signalPath, bool useHttp)
        {
            // Ưu tiên 1: full endpoint từng signal (schema mới OpenTelemetry:*).
            var full = config[fullEndpointKey];
            if (!string.IsNullOrWhiteSpace(full))
                return (full!.TrimEnd('/'), true); // full HTTP URL đã kèm path → HttpProtobuf

            // Fallback theo protocol.
            if (useHttp)
            {
                var httpBase = config["Otel:OtlpHttpEndpoint"] ?? "http://localhost:4318";
                return ($"{httpBase.TrimEnd('/')}/{signalPath}", true);
            }
            else
            {
                var grpcBase = config["Otel:OtlpEndpoint"] ?? "http://localhost:4317";
                return (grpcBase, false); // gRPC: OTel tự nối /<signal> (vì base không có path)
            }
        }

        /// <summary>
        /// Lỗi 8: parse sampler từ cấu hình Otel:TracesSampler.
        /// Giá trị: always_on | always_off | parentbased | <tỉ lệ 0..1>
        /// Mặc định (không khai) = AlwaysOnSampler để APM xuất hiện ngay cả khi ingress
        /// gắn traceparent cờ sampled=00 (tránh ParentBased bỏ span).
        /// </summary>
        private static Sampler ParseSampler(string? value)
        {
            if (string.IsNullOrWhiteSpace(value))
                return new AlwaysOnSampler();

            var v = value.Trim();
            if (v.Equals("always_on", StringComparison.OrdinalIgnoreCase))
                return new AlwaysOnSampler();
            if (v.Equals("always_off", StringComparison.OrdinalIgnoreCase))
                return new AlwaysOffSampler();
            if (v.StartsWith("parentbased", StringComparison.OrdinalIgnoreCase))
                return new ParentBasedSampler(new AlwaysOnSampler());
            // Dạng số → TraceIdRatioBasedSampler (0.0 .. 1.0)
            if (double.TryParse(v, NumberStyles.Float, CultureInfo.InvariantCulture, out var ratio))
                return new TraceIdRatioBasedSampler(Math.Clamp(ratio, 0.0, 1.0));

            // Giá trị không nhận dạng được → mặc định an toàn.
            return new AlwaysOnSampler();
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
                    var host = httpContext.Request.Host.Value;
                    var userAgent = httpContext.Request.Headers.UserAgent.ToString();
                    if (string.IsNullOrEmpty(userAgent))
                        userAgent = httpContext.Request.Headers["User-Agent"].ToString();

                    // snake_case chuẩn R-OBS-FIELD-001
                    diagnosticContext.Set("request_host", host);
                    diagnosticContext.Set("user_agent", userAgent);
                };
            });

            return app;
        }
    }
}
