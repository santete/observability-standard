using ISC.Observability.Extensions;
using ISC.Observability.Logging;
using Microsoft.AspNetCore.Builder;
using Serilog;
using Serilog.Core;
using Serilog.Events;
using Xunit;

namespace ISC.Observability.Tests;

public class BusinessLogTests : IDisposable
{
    public BusinessLogTests()
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

    private static WebApplicationBuilder BuildWithSink(TestSink sink)
    {
        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            EnvironmentName = "Development"
        });

        builder.AddStandardObservability("order-svc", configureLogger: cfg =>
        {
            cfg.WriteTo.Sink(sink);
        });

        return builder;
    }

    [Fact]
    public void Begin_Tags_LogEvent_With_BusinessCategory_And_RequestedTopic()
    {
        var testSink = new TestSink();
        BuildWithSink(testSink);

        using (BusinessLog.Begin("order-events"))
        {
            Log.Information("Order processed successfully");
        }

        Log.CloseAndFlush();

        Assert.NotEmpty(testSink.Events);
        var evt = testSink.Events.Last();

        Assert.True(evt.Properties.ContainsKey(BusinessLog.CategoryProperty));
        Assert.Equal($"\"{BusinessLog.CategoryValue}\"", evt.Properties[BusinessLog.CategoryProperty].ToString());

        Assert.True(evt.Properties.ContainsKey(BusinessLog.TopicProperty));
        Assert.Equal("\"order-events\"", evt.Properties[BusinessLog.TopicProperty].ToString());
    }

    [Fact]
    public void Dispose_Stops_Tagging_Subsequent_LogEvents()
    {
        var testSink = new TestSink();
        BuildWithSink(testSink);

        using (BusinessLog.Begin("order-events"))
        {
            Log.Information("Inside business scope");
        }

        Log.Information("Outside business scope");
        Log.CloseAndFlush();

        var outsideEvent = testSink.Events.Last();
        Assert.False(outsideEvent.Properties.ContainsKey(BusinessLog.CategoryProperty));
        Assert.False(outsideEvent.Properties.ContainsKey(BusinessLog.TopicProperty));
    }

    [Theory]
    [InlineData("")]
    [InlineData("   ")]
    [InlineData(null)]
    public void Begin_Rejects_Empty_TopicName(string? topic)
    {
        Assert.Throws<ArgumentException>(() => BusinessLog.Begin(topic!));
    }
}
