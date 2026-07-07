using System.Diagnostics;
using System.Net;
using System.Text.Json;
using OpenTelemetry.Trace;

using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
namespace ISC.Observability.Middleware;

/// <summary>
/// Global exception handling middleware.
/// Catches unhandled exceptions, logs them with full Exception object
/// (compliant with spec section 2.3), marks the current Activity as Error,
/// and rethrows the exception to allow the application to handle the response.
/// </summary>
public class GlobalExceptionMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<GlobalExceptionMiddleware> _logger;

    public GlobalExceptionMiddleware(RequestDelegate next, ILogger<GlobalExceptionMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            // SPEC 2.3: Log ERROR with full Exception object, not just Message
            _logger.LogError(ex,
                "Unhandled exception occurred. RequestPath: {RequestPath}, Method: {RequestMethod}, TraceId: {TraceId}",
                context.Request.Path,
                context.Request.Method,
                Activity.Current?.TraceId.ToString() ?? "N/A");

            // Mark current Activity/Span as Error (SPEC 4.2)
            var activity = Activity.Current;
            if (activity != null)
            {
                activity.SetStatus(ActivityStatusCode.Error, ex.Message);
                activity.AddException(ex);
            }

            // Rethrow the exception so the application can handle it normally
            throw;
        }
    }
}
