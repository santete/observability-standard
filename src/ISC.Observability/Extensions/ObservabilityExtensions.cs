using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using System.Diagnostics.Metrics;
using System.Reflection;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using Serilog;
using Serilog.Events;
using Serilog.Sinks.OpenTelemetry;
using ISC.Observability.Middleware;
using ISC.Observability.Telemetry;

namespace ISC.Observability.Extensions
{
    public static class ObservabilityExtensions
    {
        public static IHostApplicationBuilder AddStandardObservability(this IHostApplicationBuilder builder, string defaultServiceName)
        {
            var serviceName = builder.Configuration["ServiceName"] ?? defaultServiceName;
            
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
            // QA COMPLIANCE TRACKING
            // ==========================================
            // Removed Log.Information from here

            var complianceMeter = new Meter("Google.Antigravity.Observability.Compliance");
            var activeCounter = complianceMeter.CreateCounter<int>("observability.sdk.active", description: "Tracks if the standard observability SDK is attached to a service.");
            activeCounter.Add(1, new KeyValuePair<string, object?>("service.name", serviceName), new KeyValuePair<string, object?>("environment", environment));


            // ==========================================
            // 1. SERILOG CONFIGURATION (Structured Logging)
            // ==========================================
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
                .Enrich.With<PiiMaskingEnricher>()
                // Cấu hình Console Sink: Production chỉ hiện Warning/Error để tiết kiệm I/O, môi trường khác hiện Information
                .WriteTo.Console(
                    formatter: new Serilog.Formatting.Compact.RenderedCompactJsonFormatter(),
                    restrictedToMinimumLevel: environment.Equals("Production", StringComparison.OrdinalIgnoreCase) 
                        ? LogEventLevel.Warning 
                        : LogEventLevel.Information)
                // Cấu hình OpenTelemetry Sink qua Sub-logger để lọc log riêng biệt
                .WriteTo.Logger(lc => lc
                    // Loại bỏ các log liên quan đến endpoint healthcheck để giảm nhiễu trên Kibana
                    .Filter.ByExcluding(logEvent => 
                    {
                        if (logEvent.Properties.TryGetValue("RequestPath", out var requestPathValue))
                        {
                            var path = requestPathValue.ToString();
                            return path.Contains("/health", StringComparison.OrdinalIgnoreCase) || 
                                   path.Contains("/ready", StringComparison.OrdinalIgnoreCase) || 
                                   path.Contains("/alive", StringComparison.OrdinalIgnoreCase) ||
                                   path.Contains("/hc", StringComparison.OrdinalIgnoreCase);
                        }
                        return false;
                    })
                    .WriteTo.OpenTelemetry(options =>
                    {
                        options.Endpoint = $"{otlpHttpEndpoint}/v1/logs";
                        options.Protocol = OtlpProtocol.HttpProtobuf;
                        options.ResourceAttributes = new Dictionary<string, object>
                        {
                            ["service.name"] = serviceName,
                            ["service.version"] = serviceVersion,
                            ["deployment.environment"] = environment
                        };
                    })
                );

            // Nếu Dev không cấu hình MinimumLevel trong appsettings.json,
            // SDK tự đặt mặc định là Information
            if (builder.Configuration.GetSection("Serilog:MinimumLevel").Value == null
                && builder.Configuration.GetSection("Serilog:MinimumLevel:Default").Value == null)
            {
                logConfig.MinimumLevel.Information();
            }

            Log.Logger = logConfig.CreateLogger();

            // ==========================================
            // QA COMPLIANCE TRACKING
            // ==========================================
            Log.Information("Standard Observability SDK initialized for {ServiceName} with Environment {Environment}. [Compliance=True]", serviceName, environment);

            builder.Services.AddSerilog();

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
                        .AddMeter("Google.Antigravity.Observability.Compliance") // QA Compliance Meter
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
