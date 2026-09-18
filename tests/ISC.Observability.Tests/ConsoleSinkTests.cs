using ISC.Observability.Extensions;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.Configuration;
using Serilog;
using Serilog.Events;

namespace ISC.Observability.Tests;

public class ConsoleSinkTests : IDisposable
{
    public ConsoleSinkTests()
    {
        // Reset Serilog trước mỗi test
        Log.CloseAndFlush();
    }

    public void Dispose()
    {
        Log.CloseAndFlush();
    }

    /// <summary>
    /// Scenario 1: Environment = Development → Console sink BẬT mặc định, output plain text
    /// </summary>
    [Fact]
    public void Development_ConsoleSink_EnabledByDefault_PlainText()
    {
        // Arrange
        var config = new Dictionary<string, string?>
        {
            ["ASPNETCORE_ENVIRONMENT"] = "Development"
        };

        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            EnvironmentName = "Development"
        });
        builder.Configuration.AddInMemoryCollection(config);

        // Act — should NOT throw
        var output = CaptureConsoleOutput(() =>
        {
            builder.AddStandardObservability("test-service");
            Log.Information("Test message from Dev");
            Log.CloseAndFlush();
        });

        // Assert — plain text format, NOT JSON
        Assert.Contains("Test message from Dev", output);
        Assert.DoesNotContain("\"@t\":", output); // Không phải JSON compact format
        Assert.DoesNotContain("\"@m\":", output);
    }

    /// <summary>
    /// Scenario 2: Environment = Local → Console sink BẬT mặc định (vì isDevEnvironment = true)
    /// </summary>
    [Fact]
    public void Local_ConsoleSink_EnabledByDefault_PlainText()
    {
        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            EnvironmentName = "Local"
        });

        var output = CaptureConsoleOutput(() =>
        {
            builder.AddStandardObservability("test-service");
            Log.Information("Test message from Local");
            Log.CloseAndFlush();
        });

        Assert.Contains("Test message from Local", output);
        Assert.DoesNotContain("\"@t\":", output);
    }

    /// <summary>
    /// Scenario 3: Environment = Production → Console sink TẮT mặc định
    /// </summary>
    [Fact]
    public void Production_ConsoleSink_DisabledByDefault()
    {
        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            EnvironmentName = "Production"
        });

        var output = CaptureConsoleOutput(() =>
        {
            builder.AddStandardObservability("test-service");
            Log.Information("This should NOT appear on console");
            Log.CloseAndFlush();
        });

        // Console sink tắt → không có output nào từ Serilog
        Assert.DoesNotContain("This should NOT appear on console", output);
    }

    /// <summary>
    /// Scenario 4: Environment = Production + Config "Serilog:Console:Enabled" = true → Console sink BẬT (opt-in), format JSON
    /// </summary>
    [Fact]
    public void Production_ConsoleSink_OptIn_Json()
    {
        var config = new Dictionary<string, string?>
        {
            ["Serilog:Console:Enabled"] = "true"
        };

        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            EnvironmentName = "Production"
        });
        builder.Configuration.AddInMemoryCollection(config);

        var output = CaptureConsoleOutput(() =>
        {
            builder.AddStandardObservability("test-service");
            Log.Information("Prod opt-in message");
            Log.CloseAndFlush();
        });

        // Console sink bật với JSON format
        Assert.Contains("Prod opt-in message", output);
        Assert.Contains("\"@t\":", output); // JSON compact format
    }

    /// <summary>
    /// Scenario 5: Environment = Development + Config "Serilog:Console:Enabled" = false → Console sink TẮT (dev opt-out)
    /// </summary>
    [Fact]
    public void Development_ConsoleSink_OptOut()
    {
        var config = new Dictionary<string, string?>
        {
            ["Serilog:Console:Enabled"] = "false"
        };

        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            EnvironmentName = "Development"
        });
        builder.Configuration.AddInMemoryCollection(config);

        var output = CaptureConsoleOutput(() =>
        {
            builder.AddStandardObservability("test-service");
            Log.Information("This should NOT appear");
            Log.CloseAndFlush();
        });

        Assert.DoesNotContain("This should NOT appear", output);
    }

    /// <summary>
    /// Scenario 6: Environment = Staging → Console sink TẮT mặc định (không phải Dev/Local)
    /// </summary>
    [Fact]
    public void Staging_ConsoleSink_DisabledByDefault()
    {
        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            EnvironmentName = "Staging"
        });

        var output = CaptureConsoleOutput(() =>
        {
            builder.AddStandardObservability("test-service");
            Log.Information("Staging message");
            Log.CloseAndFlush();
        });

        Assert.DoesNotContain("Staging message", output);
    }

    private static string CaptureConsoleOutput(Action action)
    {
        var originalOut = Console.Out;
        var originalError = Console.Error;
        using var sw = new StringWriter();
        Console.SetOut(sw);
        Console.SetError(sw);
        try
        {
            action();
        }
        finally
        {
            Console.SetOut(originalOut);
            Console.SetError(originalError);
        }
        return sw.ToString();
    }
}
