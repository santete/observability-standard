namespace ISC.Observability.Metadata
{
    /// <summary>
    /// Marker metadata class. Gắn lên bất kỳ endpoint nào mà bạn muốn SDK 
    /// hạ cấp log request xuống mức Verbose (không hiển thị trên Kibana/Console).
    /// 
    /// Lưu ý quan trọng: Nếu endpoint trả về lỗi (HTTP >= 500 hoặc có Exception), 
    /// log sẽ vẫn được giữ nguyên mức Error để đảm bảo không bỏ sót sự cố.
    /// 
    /// Cách sử dụng:
    /// <code>
    /// app.MapHealthChecks("/health").SuppressRequestLogging();
    /// </code>
    /// </summary>
    public sealed class SuppressRequestLoggingMetadata { }
}
