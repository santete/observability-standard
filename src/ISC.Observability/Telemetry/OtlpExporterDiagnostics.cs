using System.Diagnostics.Tracing;
using Serilog;

namespace ISC.Observability.Telemetry
{
    /// <summary>
    /// Lỗi 5 (CAO): self-diagnostics cho OTel exporter.
    ///
    /// Trước đây exporter traces/metrics hỏng hoàn toàn im lặng — không log, không counter,
    /// không health signal — nên APM trống mà không ai phát hiện suốt 18 ngày. Lớp này subscribe
    /// các EventSource "OpenTelemetry-Exporter-*" do OTel SDK phát ra và ghi log Warning qua Serilog
    /// mỗi khi có sự kiện export thất bại, phá vỡ sự im lặng.
    ///
    /// EventListener được giữ static để không bị GC thu dọn và duy trì subscription suốt vòng đời app.
    /// </summary>
    internal sealed class OtlpExporterDiagnostics : EventListener
    {
        private static OtlpExporterDiagnostics? _instance;
        private static readonly object _lock = new();
        private int _failureCount;

        // Ngưỡng ghi log: không spam, chỉ log mỗi khi chạm mốc (1, 10, 100, 1000...).
        private const int LogThresholdPower = 10;

        private OtlpExporterDiagnostics() { }

        /// <summary>
        /// Tạo và giữ duy nhất một instance EventListener. Phải gọi sớm (trước Build) để kịp
        /// subscribe EventSource ngay khi chúng được tạo bởi OTel SDK.
        /// </summary>
        public static void Start()
        {
            lock (_lock)
            {
                _instance ??= new OtlpExporterDiagnostics();
            }
        }

        protected override void OnEventSourceCreated(EventSource eventSource)
        {
            // Chỉ quan tâm EventSource của OTel exporter (OpenTelemetry-Exporter-*).
            if (eventSource.Name.StartsWith("OpenTelemetry-Exporter", StringComparison.Ordinal))
            {
                EnableEvents(eventSource, EventLevel.Warning);
            }
            base.OnEventSourceCreated(eventSource);
        }

        protected override void OnEventWritten(EventWrittenEventArgs eventData)
        {
            // Bỏ qua sự kiện không liên quan lỗi (vd counters định kỳ).
            if (eventData.Level != EventLevel.Warning && eventData.Level != EventLevel.Error)
                return;

            var message = eventData.Message ?? eventData.EventName ?? "(no message)";
            Interlocked.Increment(ref _failureCount);

            // Log ngay lần đầu, sau đó chỉ log khi chạm mốc lũy thừa 10 (1, 10, 100, 1000...).
            var count = _failureCount;
            if (count == 1 || (count % LogThresholdPower == 0 && count / LogThresholdPower <= 1000000000))
            {
                Log.Warning("OTel exporter failure #{Count}: {Message} (source={Source}, event={Event})",
                    count, message, eventData.EventSource?.Name, eventData.EventName);
            }
        }
    }
}
