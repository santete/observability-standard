using System.Diagnostics;
using System.Diagnostics.Metrics;

namespace MvpDemo.Service.Telemetry;

/// <summary>
/// Centralized telemetry configuration.
/// Defines ActivitySource for distributed tracing and Meter for business metrics.
/// All custom spans and metrics MUST use these instances.
/// </summary>
public static class DiagnosticsConfig
{
    public const string ServiceName = "MvpDemo.Service";

    // ==========================================
    // TRACING: ActivitySource for custom spans
    // ==========================================
    public static readonly ActivitySource ActivitySource = new(ServiceName);

    // ==========================================
    // METRICS: Meter and instruments
    // ==========================================
    public static readonly Meter Meter = new(ServiceName);

    /// <summary>
    /// Counter: Total orders created successfully.
    /// </summary>
    public static readonly Counter<long> OrdersCreatedCounter =
        Meter.CreateCounter<long>(
            "orders.created",
            unit: "{order}",
            description: "Total number of orders created successfully");

    /// <summary>
    /// Counter: Total orders that failed processing.
    /// </summary>
    public static readonly Counter<long> OrdersFailedCounter =
        Meter.CreateCounter<long>(
            "orders.failed",
            unit: "{order}",
            description: "Total number of orders that failed processing");

    /// <summary>
    /// Counter: Total orders completed successfully.
    /// </summary>
    public static readonly Counter<long> OrdersCompletedCounter =
        Meter.CreateCounter<long>(
            "orders.completed",
            unit: "{order}",
            description: "Total number of orders completed successfully");

    /// <summary>
    /// Histogram: Order processing duration in milliseconds.
    /// Used to calculate p95, p99 percentiles.
    /// </summary>
    public static readonly Histogram<double> OrderProcessingDuration =
        Meter.CreateHistogram<double>(
            "orders.processing_duration",
            unit: "ms",
            description: "Time taken to process an order in milliseconds");

    /// <summary>
    /// UpDownCounter: Number of orders currently in Pending status.
    /// </summary>
    public static readonly UpDownCounter<long> OrdersPendingGauge =
        Meter.CreateUpDownCounter<long>(
            "orders.pending_count",
            unit: "{order}",
            description: "Current number of orders in Pending status");
}
