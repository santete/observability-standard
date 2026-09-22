using System.Diagnostics.Metrics;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Hosting;

namespace ISC.Observability.Telemetry
{
    /// <summary>
    /// Hosted service that emits QA Compliance metrics AFTER the MeterProvider has been initialized.
    /// This ensures Counter.Add() is not a no-op (which happens when called before Build()).
    /// The Meter instance is kept alive for the entire application lifetime to prevent GC disposal.
    /// </summary>
    internal sealed class ComplianceMetricsService : IHostedService, IDisposable
    {
        private readonly Meter _meter;
        private readonly Counter<int> _activeCounter;
        private readonly string _serviceName;
        private readonly string _environment;

        public ComplianceMetricsService(IConfiguration configuration, IHostEnvironment hostEnvironment)
        {
            _serviceName = configuration["ISC:Observability:ResolvedServiceName"]
                        ?? configuration["ServiceName"]
                        ?? "unknown";
            _environment = hostEnvironment.EnvironmentName;

            _meter = new Meter("ISC.Observability.Compliance");
            _activeCounter = _meter.CreateCounter<int>(
                "observability.sdk.active",
                unit: "{count}",
                description: "Tracks if the standard observability SDK is attached to a service.");
        }

        public Task StartAsync(CancellationToken cancellationToken)
        {
            // At this point MeterProvider is fully initialized and subscribed to this Meter.
            // Counter.Add() will actually record the measurement.
            var sdkVersion = typeof(ComplianceMetricsService).Assembly.GetName().Version?.ToString(3) ?? "1.4.3";

            _activeCounter.Add(1,
                new KeyValuePair<string, object?>("service_name", _serviceName),
                new KeyValuePair<string, object?>("environment", _environment),
                new KeyValuePair<string, object?>("sdk_version", sdkVersion));

            return Task.CompletedTask;
        }

        public Task StopAsync(CancellationToken cancellationToken) => Task.CompletedTask;

        public void Dispose()
        {
            _meter.Dispose();
        }
    }
}
