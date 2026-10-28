using Serilog.Context;

namespace ISC.Observability.Logging
{
    /// <summary>
    /// Cho phép Dev chủ động đánh dấu một khối log là "business event" và chỉ định luôn
    /// topic Kafka mà Dev muốn log đó được đẩy sang (ngoài đường đi mặc định tới Elasticsearch).
    ///
    /// SDK chỉ gắn 2 property snake_case chuẩn (<see cref="CategoryProperty"/>, <see cref="TopicProperty"/>)
    /// vào LogContext — KHÔNG tự kết nối hay gửi message vào Kafka. Việc đọc 2 attribute này và
    /// quyết định route log sang topic nào là trách nhiệm của OTel Collector (DevOps), đúng tinh
    /// thần "Dev không code logic chia Topic trong ứng dụng" của <c>docs/OBSERVABILITY_STANDARD.md</c> §4.4.
    ///
    /// Cách sử dụng:
    /// <code>
    /// using (BusinessLog.Begin("order-events"))
    /// {
    ///     _logger.LogInformation("Order {order_id} created successfully", order.Id);
    /// }
    /// </code>
    /// </summary>
    public static class BusinessLog
    {
        /// <summary>Tên property đánh dấu log là business event (R-OBS-FIELD-001, snake_case).</summary>
        public const string CategoryProperty = "log_category";

        /// <summary>Giá trị cố định của <see cref="CategoryProperty"/> khi log là business event.</summary>
        public const string CategoryValue = "business";

        /// <summary>Tên property chứa tên topic Kafka đích do Dev chỉ định (R-OBS-FIELD-001, snake_case).</summary>
        public const string TopicProperty = "kafka_topic";

        /// <summary>
        /// Mở một scope: mọi dòng log ghi bên trong scope này sẽ được gắn thêm
        /// <c>log_category=business</c> và <c>kafka_topic=&lt;kafkaTopic&gt;</c>.
        /// Dispose scope (hết khối <c>using</c>) để ngừng đánh dấu.
        /// </summary>
        /// <param name="kafkaTopic">
        /// Tên topic Kafka đích do Dev tự chọn (vd "order-events"). Không được rỗng.
        /// Collector sẽ dùng đúng chuỗi này làm tên topic khi export — Dev chịu trách nhiệm
        /// đặt tên nhất quán (khuyến nghị kebab-case, hậu tố "-events") và đảm bảo topic tồn tại
        /// ở hạ tầng Kafka (một số môi trường production tắt auto-create-topic).
        /// </param>
        public static IDisposable Begin(string kafkaTopic)
        {
            if (string.IsNullOrWhiteSpace(kafkaTopic))
                throw new ArgumentException("Kafka topic name không được để rỗng.", nameof(kafkaTopic));

            return new Scope(
                LogContext.PushProperty(CategoryProperty, CategoryValue),
                LogContext.PushProperty(TopicProperty, kafkaTopic));
        }

        private sealed class Scope : IDisposable
        {
            private readonly IDisposable _category;
            private readonly IDisposable _topic;
            private bool _disposed;

            public Scope(IDisposable category, IDisposable topic)
            {
                _category = category;
                _topic = topic;
            }

            public void Dispose()
            {
                if (_disposed) return;
                _disposed = true;
                // Thứ tự đóng ngược lại thứ tự mở, giữ đúng ngữ nghĩa stack của LogContext.
                _topic.Dispose();
                _category.Dispose();
            }
        }
    }
}
