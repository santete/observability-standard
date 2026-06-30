using Serilog;
using MvpDemo.Service.Services;
using ISC.Observability.Extensions;
using System.Text.Json.Serialization;
using StackExchange.Redis;
using MongoDB.Driver;
using MongoDB.Bson;
using MassTransit;
using MvpDemo.Service.Consumers;

var builder = WebApplication.CreateBuilder(args);

// ==========================================
// 1 & 2. OBSERVABILITY CONFIGURATION
// ==========================================
// This single line sets up Serilog, OpenTelemetry Traces & Metrics perfectly
builder.AddStandardObservability("mvp-demo-service");

// ==========================================
// 3. SERVICES REGISTRATION
// ==========================================
builder.Services.AddSingleton<OrderService>();
builder.Services.AddHealthChecks()
    .AddRedis(builder.Configuration.GetConnectionString("Redis") ?? "redis:6379", name: "redis")
    .AddKafka(setup => {
        setup.BootstrapServers = builder.Configuration.GetConnectionString("Kafka") ?? "kafka:9092";
    }, name: "kafka-broker")
    .AddCheck("mongodb", new MongoDBHealthCheck(builder.Configuration.GetConnectionString("MongoDb") ?? "mongodb://mongo:27017"));
builder.Services.AddHttpClient();

// MassTransit Kafka
builder.Services.AddMassTransit(x =>
{
    x.UsingInMemory((context, cfg) => cfg.ConfigureEndpoints(context));

    x.AddRider(rider =>
    {
        rider.AddConsumer<KafkaMessageConsumer>();
        rider.AddProducer<string, TestMessage>("test-topic");

        rider.UsingKafka((context, k) =>
        {
            k.Host(builder.Configuration.GetConnectionString("Kafka") ?? "kafka:9092");
            k.TopicEndpoint<TestMessage>("test-topic", "demo-group", e =>
            {
                e.ConfigureConsumer<KafkaMessageConsumer>(context);
            });
        });
    });
});

// Polyglot Testing Dependencies
builder.Services.AddSingleton<IConnectionMultiplexer>(sp => 
    ConnectionMultiplexer.Connect(builder.Configuration.GetConnectionString("Redis") ?? "localhost:6379"));
builder.Services.AddSingleton<IMongoClient>(sp => 
{
    var settings = MongoClientSettings.FromConnectionString(builder.Configuration.GetConnectionString("Mongo") ?? "mongodb://localhost:27017");
    settings.ClusterConfigurator = cb => cb.Subscribe(new MongoDB.Driver.Core.Extensions.DiagnosticSources.DiagnosticsActivityEventSubscriber());
    return new MongoClient(settings);
});
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter());
        options.JsonSerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase;
    });
builder.Services.AddEndpointsApiExplorer();

// ==========================================
// BUILD APP
// ==========================================
var app = builder.Build();

// ==========================================
// 4. MIDDLEWARE PIPELINE
// ==========================================
// This single line adds CorrelationId, GlobalException, and Serilog Request Logging
app.UseStandardObservability();

// ==========================================
// 5. ENDPOINTS
// ==========================================
app.MapHealthChecks("/healthz", new Microsoft.AspNetCore.Diagnostics.HealthChecks.HealthCheckOptions
{
    ResponseWriter = HealthChecks.UI.Client.UIResponseWriter.WriteHealthCheckUIResponse
});  // Liveness probe
app.MapHealthChecks("/ready", new Microsoft.AspNetCore.Diagnostics.HealthChecks.HealthCheckOptions
{
    ResponseWriter = HealthChecks.UI.Client.UIResponseWriter.WriteHealthCheckUIResponse
});    // Readiness probe

// Root endpoint - service info
app.MapGet("/", () => Results.Ok(new
{
    service = "mvp-demo-service",
    version = "1.0.0",
    environment = app.Environment.EnvironmentName,
    status = "running",
    endpoints = new
    {
        health = "/healthz",
        ready = "/ready",
        orders = "/api/orders",
        simulateError = "/api/orders/simulate-error",
        demoPii = "/api/orders/demo-pii",
        polyglotTest = "/api/polyglot-test"
    }
}));

app.MapGet("/api/polyglot-test", async (IConnectionMultiplexer redis, IMongoClient mongo, ILogger<Program> logger, HttpClient httpClient, [Microsoft.AspNetCore.Mvc.FromServices] ITopicProducer<string, TestMessage> producer) => 
{
    logger.LogInformation("Bắt đầu test đa nền tảng (Polyglot Tracing Test)");
    
    // 1. Redis Test
    var db = redis.GetDatabase();
    await db.StringSetAsync("PolyglotTest", "OK", TimeSpan.FromMinutes(1));
    var redisValue = await db.StringGetAsync("PolyglotTest");

    // 2. Mongo Test
    var mongoDb = mongo.GetDatabase("observability_demo");
    var collection = mongoDb.GetCollection<BsonDocument>("test_logs");
    await collection.InsertOneAsync(new BsonDocument { { "timestamp", DateTime.UtcNow }, { "message", "Test from polyglot API" } });
    
    // 3. HTTP Test
    try {
        var response = await httpClient.GetAsync("https://jsonplaceholder.typicode.com/todos/1");
        response.EnsureSuccessStatusCode();
    } catch { }

    // 4. Kafka Test
    await producer.Produce("test-key", new TestMessage { Content = "Hello from Polyglot API", Timestamp = DateTime.UtcNow });

    return Results.Ok(new { message = "Integration test completed successfully!", redis = redisValue.ToString() });
});

app.MapControllers();

// ==========================================
// 6. RUN
// ==========================================
try
{
    Log.Information("{ServiceName} is ready. Listening on {Urls}",
        "mvp-demo-service", string.Join(", ", app.Urls));
    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "{ServiceName} terminated unexpectedly", "mvp-demo-service");
}
finally
{
    Log.CloseAndFlush();
}

public class MongoDBHealthCheck : Microsoft.Extensions.Diagnostics.HealthChecks.IHealthCheck
{
    private readonly string _connectionString;

    public MongoDBHealthCheck(string connectionString)
    {
        _connectionString = connectionString;
    }

    public async System.Threading.Tasks.Task<Microsoft.Extensions.Diagnostics.HealthChecks.HealthCheckResult> CheckHealthAsync(Microsoft.Extensions.Diagnostics.HealthChecks.HealthCheckContext context, System.Threading.CancellationToken cancellationToken = default)
    {
        try
        {
            var client = new MongoDB.Driver.MongoClient(_connectionString);
            var db = client.GetDatabase("admin");
            await db.RunCommandAsync((MongoDB.Driver.Command<MongoDB.Bson.BsonDocument>)"{ping:1}", cancellationToken: cancellationToken);
            return Microsoft.Extensions.Diagnostics.HealthChecks.HealthCheckResult.Healthy();
        }
        catch (System.Exception ex)
        {
            return new Microsoft.Extensions.Diagnostics.HealthChecks.HealthCheckResult(context.Registration.FailureStatus, exception: ex);
        }
    }
}
