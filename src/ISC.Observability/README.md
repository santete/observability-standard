# 📦 ISC.Observability SDK

> **Gói SDK Tiêu chuẩn (Official Standard SDK) dành cho các dịch vụ Backend (.NET) thuộc hệ sinh thái Microservices.** 
> Tự động hóa toàn bộ quá trình thu thập Logs, Metrics, và Traces (OpenTelemetry) theo tiêu chuẩn vận hành tập trung mà không yêu cầu thay đổi logic code của ứng dụng.

---

## ✨ Tính năng nổi bật (Features)

Chỉ với **1 dòng code tích hợp**, ứng dụng của bạn sẽ lập tức sở hữu:

- 🔗 **Auto-Instrumentation (Tracing):** Tự động theo dõi toàn bộ HTTP Requests (In/Out), gán `TraceId` xuyên suốt qua các Microservices (W3C TraceContext).
- 📝 **Structured Logging:** Ghi log có cấu trúc (JSON) thông qua Serilog, tự động đính kèm `TraceId` vào mỗi dòng log.
- 🛡️ **Global Exception Handling:** Tự động "bắt" toàn bộ các lỗi (Crash/Exception) chưa được xử lý, chụp StackTrace và ghi log mức `ERROR` tránh lọt lỗi.
- 🕵️ **PII Masking (Bảo mật & Hiệu năng cao):** Thuật toán tự động quét và làm mờ (Mask) các thông tin nhạy cảm của người dùng (SĐT, Email, Số thẻ) bằng `***`. Được thiết kế tối ưu với **Zero-Allocation Caching** đảm bảo không sinh rác (GC Pressure) khi chịu tải cao.
- 📊 **Runtime & HTTP Metrics:** Thu thập liên tục các chỉ số sinh tồn của ứng dụng: RAM, CPU, Garbage Collection (GC), ThreadPool, Request Per Second (RPS), Latency.
- 🚀 **OTLP Exporting:** Tuân thủ chuẩn OpenTelemetry Protocol (OTLP), xuất dữ liệu trực tiếp về OTel Collector. Hoàn toàn không ghi đè ra file vật lý, không kết nối trực tiếp vào Kafka/Elasticsearch gây phình ứng dụng.

## 🔌 Các công nghệ được hỗ trợ (Instrumentations)

SDK hiện tại đã tích hợp sẵn thư viện để theo dõi (trace) các thành phần sau. Bạn chỉ cần bật/tắt chúng trong cấu hình mà không cần code thêm:

1. **HTTP (ASP.NET Core & HttpClient):** Mặc định bật. Thu thập các request HTTP đi vào API và các request gọi ra ngoài qua HttpClient.
2. **Entity Framework Core (SQL Server, Postgres, MySQL, v.v.):** Tự động trace các câu lệnh SQL và thời gian thực thi DB.
3. **Redis (StackExchange.Redis):** Tự động trace các câu lệnh Cache (GET, SET, MGET, v.v.)
4. **MongoDB (MongoDB.Driver.Core.Extensions.DiagnosticSources):** Tự động trace các lệnh truy vấn NoSQL (Insert, Find, Update).
5. **Message Broker (MassTransit / Kafka / RabbitMQ):** Tự động nối Trace Context xuyên qua hệ thống queue/message bus.
6. **Background Jobs (Quartz.NET):** Tự động trace các chu trình chạy ngầm.
7. **gRPC (GrpcNetClient):** Tự động trace các cuộc gọi gRPC.

## 📥 Cài đặt (Installation)

Cài đặt package thông qua NuGet Package Manager hoặc .NET CLI:

```bash
dotnet add package ISC.Observability
```

*(Lưu ý: Bạn **NÊN GỠ BỎ** các package liên quan đến Serilog cũ như `Serilog.Sinks.Console`, `Serilog.Sinks.File`, v.v. để tránh xung đột cấu hình, vì SDK đã bao bọc đầy đủ bên trong).*

## 🚀 Hướng dẫn sử dụng (Quick Start)

### 1. Khởi tạo trong `Program.cs`

Mở file `Program.cs` của ứng dụng và thêm **duy nhất 1 dòng lệnh** `builder.AddStandardObservability(...)` trước khi gọi `builder.Build()`.

```csharp
using ISC.Observability.Extensions; // 👈 Thêm thư viện

var builder = WebApplication.CreateBuilder(args);

// 1. Tích hợp SDK Tiêu chuẩn Observability
// Cấu hình tên mặc định của Service (ưu tiên lấy từ appsettings.json nếu có)
builder.AddStandardObservability("MyDemoService");

builder.Services.AddControllers();

var app = builder.Build();

// 2. Kích hoạt các Middleware (Bắt lỗi & TraceId)
app.UseStandardObservability();

app.MapControllers();
app.Run();
```

### 2. Bật / Tắt Các Instrumentations Bằng `appsettings.json`

Bạn không cần can thiệp vào code để kích hoạt các tính năng theo dõi database hay redis. Chỉ cần cấu hình file `appsettings.json` (hoặc Environment Variables). Mặc định nếu không cấu hình, các instrument bên ngoài (Redis, Mongo, Kafka...) sẽ tắt để tiết kiệm tài nguyên.

```json
{
  "ServiceName": "Payment.Service",
  "ServiceVersion": "1.2.0",
  "Otel": {
    "OtlpEndpoint": "http://otel-collector:4317",
    "OtlpHttpEndpoint": "http://otel-collector:4318",
    "EnableRedis": true,          // Bật auto-trace cho Redis
    "EnableMongo": true,          // Bật auto-trace cho MongoDB
    "EnableMassTransit": true,    // Bật auto-trace cho Message Brokers (Kafka, RabbitMQ) qua MassTransit
    "EnableGrpc": false,          // Bật/tắt gRPC
    "EnableQuartz": false,        // Bật/tắt theo dõi Job của Quartz.NET
    "EnableEntityFramework": true // Bật auto-trace truy vấn SQL (EF Core)
  }
}
```

### 3. Ghi Log Nghiệp Vụ (Business Logging)

Code nghiệp vụ của bạn **không cần thay đổi**. Vẫn tiếp tục sử dụng `ILogger<T>` mặc định của .NET. SDK sẽ tự động format và đẩy log đi kèm với `TraceId`.

```csharp
public class OrdersController : ControllerBase
{
    private readonly ILogger<OrdersController> _logger;

    public OrdersController(ILogger<OrdersController> logger)
    {
        _logger = logger;
    }

    [HttpPost]
    public IActionResult CreateOrder([FromBody] Order order)
    {
        // Ghi log bình thường, tự động được đính kèm TraceId hiện tại!
        _logger.LogInformation("Bắt đầu xử lý đơn hàng {OrderId} cho user {UserEmail}", order.Id, order.Email);
        
        // Trình Masking PII của SDK sẽ tự động che mờ Email thành "n***@g***.com" trong log text.
        return Ok();
    }
}
```

### 4. Custom Tracing (Theo dõi sâu hơn bên trong phương thức)

Trong trường hợp bạn có một hàm xử lý rất nặng (ví dụ: chạy thuật toán tính toán phức tạp, hoặc parse file lớn) và muốn tách nó thành 1 Span riêng biệt hiển thị trên biểu đồ thác nước (Waterfall) của Kibana APM, bạn có thể tự tạo **Custom Span** bằng `System.Diagnostics.ActivitySource`:

```csharp
using System.Diagnostics;

public class ComplexService
{
    // 1. Định nghĩa ActivitySource với cùng tên Service Name của ứng dụng
    private static readonly ActivitySource MyActivitySource = new ActivitySource("Payment.Service");

    public void ProcessLargeData()
    {
        // 2. Bắt đầu tạo 1 Span mới bao bọc logic này
        using var activity = MyActivitySource.StartActivity("ProcessLargeData.CalculateHash");

        // (Tùy chọn) Gắn thêm Tag / Thuộc tính để dễ tìm kiếm trên Kibana
        activity?.SetTag("data.size", "150MB");
        activity?.SetTag("algorithm", "SHA256");

        try
        {
            // Thực thi logic nghiệp vụ nặng...
            Thread.Sleep(2000); 
            
            activity?.SetStatus(ActivityStatusCode.Ok);
        }
        catch (Exception ex)
        {
            // Nếu có lỗi, đánh dấu Span là lỗi và ghi lại Exception
            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            throw;
        }
    }
}
```
*Lưu ý: Bạn không cần cài package gì thêm để code đoạn này vì `System.Diagnostics` là hàm built-in của .NET Core.*

## 🛡️ Tích hợp luồng QA Compliance

Khi ứng dụng của bạn khởi chạy thành công với SDK này, hệ thống sẽ tự động phát đi một sự kiện Log (Event) và Metric báo hiệu: `[Compliance=True]`. 
QA Team và Dashboard **QA Compliance Tracker (Lớp 4)** sẽ tự động nhận diện ứng dụng của bạn là ĐẠT CHUẨN để sẵn sàng Release lên môi trường Production.

---
*© 2026. Tuân thủ Kiến trúc Microservices Tiêu Chuẩn.*
