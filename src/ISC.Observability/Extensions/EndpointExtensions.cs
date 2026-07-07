using ISC.Observability.Metadata;
using Microsoft.AspNetCore.Builder;

namespace ISC.Observability.Extensions
{
    public static class EndpointExtensions
    {
        /// <summary>
        /// Đánh dấu endpoint này để SDK tự động hạ cấp log request xuống mức Verbose.
        /// Các Sink (Console, OpenTelemetry/Kibana) mặc định chỉ hiển thị từ Information trở lên,
        /// nên các request đến endpoint này sẽ tự động "biến mất" khỏi dashboard.
        /// 
        /// Lưu ý: Log lỗi (HTTP >= 500 hoặc có Exception) vẫn được giữ nguyên mức Error,
        /// đảm bảo không bao giờ bỏ sót sự cố hệ thống.
        /// 
        /// Ví dụ sử dụng:
        /// <code>
        /// app.MapHealthChecks("/health").SuppressRequestLogging();
        /// app.MapHealthChecks("/ready").SuppressRequestLogging();
        /// app.MapGet("/internal/ping", () => "pong").SuppressRequestLogging();
        /// </code>
        /// </summary>
        public static TBuilder SuppressRequestLogging<TBuilder>(this TBuilder builder)
            where TBuilder : IEndpointConventionBuilder
        {
            builder.WithMetadata(new SuppressRequestLoggingMetadata());
            return builder;
        }
    }
}
