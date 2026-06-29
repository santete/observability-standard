# 📦 ISC.Observability SDK

> **Gói SDK Tiêu chuẩn (Official Standard SDK) dành cho các dịch vụ Backend (.NET) thuộc hệ sinh thái Microservices.** 
> Tự động hóa toàn bộ quá trình thu thập Logs, Metrics, và Traces (OpenTelemetry) theo tiêu chuẩn vận hành tập trung mà không yêu cầu thay đổi logic code của ứng dụng.

---

## ✨ Tính năng nổi bật (Features)

Chỉ với **1 dòng code tích hợp**, ứng dụng của bạn sẽ lập tức sở hữu:

- 🔗 **Auto-Instrumentation (Tracing):** Tự động theo dõi toàn bộ HTTP Requests (In/Out), gán `TraceId` xuyên suốt qua các Microservices (W3C TraceContext).
- 📝 **Structured Logging:** Ghi log có cấu trúc (JSON) thông qua Serilog, tự động đính kèm `TraceId` vào mỗi dòng log.
- 🛡️ **Global Exception Handling:** Tự động "bắt" toàn bộ các lỗi (Crash/Exception) chưa được xử lý, chụp StackTrace và ghi log mức `ERROR` tránh lọt lỗi.
- 🕵️ **PII Masking (Bảo mật):** Thuật toán tự động quét và làm mờ (Mask) các thông tin nhạy cảm của người dùng (SĐT, Email, Số thẻ, SSN) trong log text bằng `***`.
- 📊 **Runtime & HTTP Metrics:** Thu thập liên tục các chỉ số sinh tồn của ứng dụng: RAM, CPU, Garbage Collection (GC), ThreadPool, Request Per Second (RPS), Latency.
- 🚀 **OTLP Exporting:** Tuân thủ chuẩn OpenTelemetry Protocol (OTLP), xuất dữ liệu trực tiếp về OTel Collector. Hoàn toàn không ghi đè ra file vật lý, không kết nối trực tiếp vào Kafka/Elasticsearch gây phình ứng dụng.

## ⚙️ Yêu cầu hệ thống

- **.NET SDK:** `.NET 6.0`, `.NET 7.0`, hoặc `.NET 8.0+`
- Môi trường chạy có khả năng kết nối tới OpenTelemetry Collector.

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
// Truyền vào tên mặc định của Service (nếu file config không có)
builder.AddStandardObservability("MyDemoService");

builder.Services.AddControllers();

var app = builder.Build();

// 2. Kích hoạt các Middleware (Bắt lỗi & TraceId)
app.UseStandardObservability();

app.MapControllers();
app.Run();
```

### 2. Ghi Log Nghiệp Vụ (Business Logging)

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
        // Ghi log bình thường, tự động có TraceId!
        _logger.LogInformation("Bắt đầu xử lý đơn hàng {OrderId} cho user {UserEmail}", order.Id, order.Email);
        
        // SDK sẽ tự động che mờ Email thành "n***@g***.com" trên Kibana
        
        return Ok();
    }
}
```

## 🔧 Cấu hình (Configuration)

SDK tự động đọc các cấu hình từ `appsettings.json` hoặc **Environment Variables**. 
Dưới đây là các biến môi trường quan trọng bạn cần (hoặc cấu hình DevOps sẽ) truyền vào khi deploy:

| Biến cấu hình (JSON / Env) | Kiểu | Mô tả | Mặc định (Fallback) |
| :--- | :--- | :--- | :--- |
| `ServiceName` | String | Tên định danh của ứng dụng trên Dashboard | Tham số truyền vào code |
| `ServiceVersion` | String | Phiên bản của ứng dụng | `1.0.0` |
| `Otel:OtlpEndpoint` | URL | Địa chỉ gRPC của OTel Collector (dành cho Traces/Metrics) | `http://localhost:4317` |
| `Otel:OtlpHttpEndpoint` | URL | Địa chỉ HTTP của OTel Collector (dành cho Logs) | `http://localhost:4318` |

**Ví dụ cấu hình trong `appsettings.json`:**

```json
{
  "ServiceName": "Payment.Service",
  "ServiceVersion": "1.2.0",
  "Otel": {
    "OtlpEndpoint": "http://otel-collector:4317",
    "OtlpHttpEndpoint": "http://localhost:4318",
    "EnableRedis": true,        // (Tùy chọn) Bật auto-trace cho Redis
    "EnableGrpc": true,         // (Tùy chọn) Bật auto-trace cho gRPC
    "EnableMongo": false,       // (Tùy chọn) Bật auto-trace cho MongoDB
    "EnableMassTransit": false, // (Tùy chọn) Bật auto-trace cho MassTransit
    "EnableQuartz": false       // (Tùy chọn) Bật auto-trace cho Quartz.NET
  }
}
```

## 🛡️ Tích hợp luồng QA Compliance

Khi ứng dụng của bạn khởi chạy thành công với SDK này, hệ thống sẽ tự động phát đi một sự kiện Log (Event) và Metric báo hiệu: `[Compliance=True]`. 
QA Team và Dashboard **QA Compliance Tracker (Lớp 4)** sẽ tự động nhận diện ứng dụng của bạn là ĐẠT CHUẨN để sẵn sàng Release lên môi trường Production.

---
*© 2026. Tuân thủ Kiến trúc Microservices Tiêu Chuẩn.*
