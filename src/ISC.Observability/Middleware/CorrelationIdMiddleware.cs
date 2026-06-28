using System.Diagnostics;
using Serilog.Context;

using Microsoft.AspNetCore.Http;
namespace ISC.Observability.Middleware;

/// <summary>
/// Middleware that ensures every request has a correlation ID.
/// Reads X-Correlation-Id header or generates a new one.
/// Pushes TraceId, SpanId, and CorrelationId to Serilog LogContext
/// so every log entry within the request has these identifiers.
/// Compliant with spec sections 2.3 (TraceId/SpanId metadata) and 4.1 (Context Propagation).
/// </summary>
public class CorrelationIdMiddleware
{
    private const string CorrelationIdHeader = "X-Correlation-Id";
    private readonly RequestDelegate _next;

    public CorrelationIdMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        // Read or generate Correlation ID
        var correlationId = context.Request.Headers[CorrelationIdHeader].FirstOrDefault()
                           ?? Activity.Current?.TraceId.ToString()
                           ?? Guid.NewGuid().ToString("N");

        // Set response header for downstream tracing
        context.Response.Headers[CorrelationIdHeader] = correlationId;

        // Push identifiers to Serilog LogContext (SPEC 2.3)
        using (LogContext.PushProperty("CorrelationId", correlationId))
        using (LogContext.PushProperty("TraceId", Activity.Current?.TraceId.ToString() ?? "N/A"))
        using (LogContext.PushProperty("SpanId", Activity.Current?.SpanId.ToString() ?? "N/A"))
        {
            await _next(context);
        }
    }
}
