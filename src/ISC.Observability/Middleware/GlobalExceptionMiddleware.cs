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
/// and returns RFC 7807 Problem Details response.
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

            // Return RFC 7807 Problem Details
            context.Response.StatusCode = (int)HttpStatusCode.InternalServerError;
            context.Response.ContentType = "application/problem+json";

            var problemDetails = new
            {
                type = "https://httpstatuses.com/500",
                title = "Internal Server Error",
                status = 500,
                detail = "An unexpected error occurred. Please use the TraceId to investigate.",
                traceId = Activity.Current?.TraceId.ToString(),
                instance = context.Request.Path.ToString()
            };

            var json = JsonSerializer.Serialize(problemDetails, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });

            await context.Response.WriteAsync(json);
        }
    }
}
