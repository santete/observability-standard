using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using MongoDB.Driver;
using MongoDB.Bson;

namespace MvpDemo.Service;

public class MongoDBHealthCheck : IHealthCheck
{
    private readonly string _connectionString;

    public MongoDBHealthCheck(string connectionString)
    {
        _connectionString = connectionString;
    }

    public async Task<HealthCheckResult> CheckHealthAsync(HealthCheckContext context, CancellationToken cancellationToken = default)
    {
        try
        {
            var client = new MongoClient(_connectionString);
            var db = client.GetDatabase("admin");
            await db.RunCommandAsync((Command<BsonDocument>)"{ping:1}", cancellationToken: cancellationToken);
            return HealthCheckResult.Healthy();
        }
        catch (Exception ex)
        {
            return new HealthCheckResult(context.Registration.FailureStatus, exception: ex);
        }
    }
}
