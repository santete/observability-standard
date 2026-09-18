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

public class SnakeCaseAndBackwardCompatibilityTests : IDisposable
{
    public SnakeCaseAndBackwardCompatibilityTests()
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
    public void StandardObservability_Enriches_Both_SnakeCase_And_PascalCase_SystemProperties()
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

        // 1. Verify snake_case properties exist (R-OBS-FIELD-001)
        Assert.True(evt.Properties.ContainsKey("service_name"), "Missing snake_case: service_name");
        Assert.Equal("\"order-svc\"", evt.Properties["service_name"].ToString());

        Assert.True(evt.Properties.ContainsKey("environment"), "Missing snake_case: environment");
        Assert.Equal("\"Development\"", evt.Properties["environment"].ToString());

        Assert.True(evt.Properties.ContainsKey("application_version"), "Missing snake_case: application_version");
        Assert.True(evt.Properties.ContainsKey("machine_name"), "Missing snake_case: machine_name");
        Assert.True(evt.Properties.ContainsKey("thread_id"), "Missing snake_case: thread_id");

        // 2. Verify PascalCase properties STILL exist (Backward Compatibility)
        Assert.True(evt.Properties.ContainsKey("ServiceName"), "Missing PascalCase: ServiceName");
        Assert.Equal("\"order-svc\"", evt.Properties["ServiceName"].ToString());

        Assert.True(evt.Properties.ContainsKey("Environment"), "Missing PascalCase: Environment");
        Assert.Equal("\"Development\"", evt.Properties["Environment"].ToString());

        Assert.True(evt.Properties.ContainsKey("ApplicationVersion"), "Missing PascalCase: ApplicationVersion");
        Assert.True(evt.Properties.ContainsKey("MachineName"), "Missing PascalCase: MachineName");
        Assert.True(evt.Properties.ContainsKey("ThreadId"), "Missing PascalCase: ThreadId");
    }

    [Fact]
    public async Task CorrelationIdMiddleware_Pushes_Both_SnakeCase_And_PascalCase_To_LogContext()
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

        // Verify snake_case
        Assert.True(evt.Properties.ContainsKey("correlation_id"), "Missing snake_case: correlation_id");
        Assert.Equal("\"test-corr-12345\"", evt.Properties["correlation_id"].ToString());

        Assert.True(evt.Properties.ContainsKey("request_id"), "Missing snake_case: request_id");
        Assert.Equal("\"test-corr-12345\"", evt.Properties["request_id"].ToString());

        Assert.True(evt.Properties.ContainsKey("trace_id"), "Missing snake_case: trace_id");
        Assert.True(evt.Properties.ContainsKey("span_id"), "Missing snake_case: span_id");

        // Verify PascalCase backward compatibility
        Assert.True(evt.Properties.ContainsKey("CorrelationId"), "Missing PascalCase: CorrelationId");
        Assert.Equal("\"test-corr-12345\"", evt.Properties["CorrelationId"].ToString());

        Assert.True(evt.Properties.ContainsKey("TraceId"), "Missing PascalCase: TraceId");
        Assert.True(evt.Properties.ContainsKey("SpanId"), "Missing PascalCase: SpanId");
    }
}
