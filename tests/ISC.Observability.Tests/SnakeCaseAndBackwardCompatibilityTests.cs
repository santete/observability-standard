using ISC.Observability.Extensions;
using ISC.Observability.Middleware;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Serilog;
using Serilog.Core;
using Serilog.Events;
using System.Diagnostics;
using Xunit;

namespace ISC.Observability.Tests;

public class SnakeCaseStandardLoggingTests : IDisposable
{
    public SnakeCaseStandardLoggingTests()
    {
        Log.CloseAndFlush();
    }

    public void Dispose()
    {
        Log.CloseAndFlush();
    }

    private class TestSink : ILogEventSink
    {
        public List<LogEvent> Events { get; } = new();
        public void Emit(LogEvent logEvent) => Events.Add(logEvent);
    }

    [Fact]
    public void StandardObservability_Enriches_Only_SnakeCase_SystemProperties()
    {
        var testSink = new TestSink();
        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            EnvironmentName = "Development"
        });

        builder.AddStandardObservability("order-svc", configureLogger: cfg =>
        {
            cfg.WriteTo.Sink(testSink);
        });

        Log.Information("Test message for convention verification");
        Log.CloseAndFlush();

        Assert.NotEmpty(testSink.Events);
        var evt = testSink.Events.Last();

        // 1. Verify 100% snake_case properties exist (R-OBS-FIELD-001)
        Assert.True(evt.Properties.ContainsKey("service_name"), "Missing snake_case: service_name");
        Assert.Equal("\"order-svc\"", evt.Properties["service_name"].ToString());

        Assert.True(evt.Properties.ContainsKey("environment"), "Missing snake_case: environment");
        Assert.Equal("\"Development\"", evt.Properties["environment"].ToString());

        Assert.True(evt.Properties.ContainsKey("application_version"), "Missing snake_case: application_version");
        Assert.True(evt.Properties.ContainsKey("machine_name"), "Missing snake_case: machine_name");
        Assert.True(evt.Properties.ContainsKey("thread_id"), "Missing snake_case: thread_id");

        // 2. Verify legacy PascalCase properties are REMOVED (Zero duplicate pollution)
        Assert.False(evt.Properties.ContainsKey("ServiceName"), "Polluted with PascalCase: ServiceName");
        Assert.False(evt.Properties.ContainsKey("Environment"), "Polluted with PascalCase: Environment");
        Assert.False(evt.Properties.ContainsKey("ApplicationVersion"), "Polluted with PascalCase: ApplicationVersion");
        Assert.False(evt.Properties.ContainsKey("MachineName"), "Polluted with PascalCase: MachineName");
        Assert.False(evt.Properties.ContainsKey("ThreadId"), "Polluted with PascalCase: ThreadId");
    }

    [Fact]
    public async Task CorrelationIdMiddleware_Pushes_Only_SnakeCase_To_LogContext()
    {
        var testSink = new TestSink();
        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            EnvironmentName = "Development"
        });

        builder.AddStandardObservability("order-svc", configureLogger: cfg =>
        {
            cfg.WriteTo.Sink(testSink);
        });

        var middleware = new CorrelationIdMiddleware(async ctx =>
        {
            Log.Information("Inside request processing");
            await Task.CompletedTask;
        });

        var context = new DefaultHttpContext();
        context.Request.Headers["X-Correlation-Id"] = "test-corr-12345";

        await middleware.InvokeAsync(context);
        Log.CloseAndFlush();

        Assert.NotEmpty(testSink.Events);
        var evt = testSink.Events.Last();

        // Verify snake_case properties
        Assert.True(evt.Properties.ContainsKey("correlation_id"), "Missing snake_case: correlation_id");
        Assert.Equal("\"test-corr-12345\"", evt.Properties["correlation_id"].ToString());

        Assert.True(evt.Properties.ContainsKey("request_id"), "Missing snake_case: request_id");
        Assert.Equal("\"test-corr-12345\"", evt.Properties["request_id"].ToString());

        Assert.True(evt.Properties.ContainsKey("trace_id"), "Missing snake_case: trace_id");
        Assert.True(evt.Properties.ContainsKey("span_id"), "Missing snake_case: span_id");

        // Verify legacy PascalCase properties are REMOVED (Zero duplicate pollution)
        Assert.False(evt.Properties.ContainsKey("CorrelationId"), "Polluted with PascalCase: CorrelationId");
        Assert.False(evt.Properties.ContainsKey("TraceId"), "Polluted with PascalCase: TraceId");
        Assert.False(evt.Properties.ContainsKey("SpanId"), "Polluted with PascalCase: SpanId");
    }
}
