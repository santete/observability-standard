using Serilog.Core;
using Serilog.Events;

namespace ISC.Observability.Telemetry;

/// <summary>
/// Enriches log events with snake_case system properties according to R-OBS-FIELD-001.
/// Runs alongside default Serilog enrichers (MachineName, ThreadId) to ensure 100% backward compatibility.
/// </summary>
internal sealed class SnakeCaseSystemEnricher : ILogEventEnricher
{
    private static readonly string MachineName = Environment.MachineName;

    public void Enrich(LogEvent logEvent, ILogEventPropertyFactory propertyFactory)
    {
        logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty("machine_name", MachineName));
        logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty("thread_id", Environment.CurrentManagedThreadId));
    }
}
