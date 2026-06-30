using MassTransit;
using System.Text.Json;

namespace MvpDemo.Service.Consumers
{
    public class TestMessage
    {
        public string Content { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; }
    }

    public class KafkaMessageConsumer : IConsumer<TestMessage>
    {
        private readonly ILogger<KafkaMessageConsumer> _logger;

        public KafkaMessageConsumer(ILogger<KafkaMessageConsumer> logger)
        {
            _logger = logger;
        }

        public Task Consume(ConsumeContext<TestMessage> context)
        {
            _logger.LogInformation("Received Kafka Message: {Content} at {Timestamp}. TraceId: {TraceId}",
                context.Message.Content, context.Message.Timestamp, System.Diagnostics.Activity.Current?.TraceId.ToString());
                
            return Task.CompletedTask;
        }
    }
}
