# TÀI LIỆU QUY ĐỊNH TIÊU CHUẨN OBSERVABILITY (SPECIFICATION DOCUMENT)
**Dự án:** Hệ thống MVP Demo chuẩn hóa Vận hành & Giám sát
**Vai trò ban hành:** Khối Quản lý Chất lượng (QA) & Đảm bảo Vận hành
**Đối tượng áp dụng:** Toàn bộ Đội ngũ Phát triển Phần mềm (Developers)
**Tech Stack Quy Định:** .NET 6 trở lên, OpenTelemetry (OTel), Elasticsearch, Kibana

---

## 1. MỤC TIÊU VÀ PHẠM VI SỬ DỤNG
Tài liệu này quy định các tiêu chuẩn bắt buộc về việc thu thập dữ liệu quan sát (Observability) bao gồm **Logs, Metrics, và Traces** đối với các dịch vụ phát triển trên nền tảng .NET 6+. 

**Mục tiêu chính:**
* Đảm bảo mọi dịch vụ khi triển khai lên môi trường Demo/Staging/Production đều có khả năng tự minh bạch trạng thái hoạt động.
* Chuẩn hóa cấu trúc dữ liệu đầu ra để hệ thống lưu trữ (Elasticsearch) và hiển thị (Kibana) hoạt động đồng bộ, chính xác.
* Hỗ trợ QA và Dev nhanh chóng phát hiện, cô lập và xử lý sự cố (MTTR - Mean Time To Resolution thấp nhất).

---

## 2. TIÊU CHUẨN GHI LOGGING (NHẬT KÝ SỰ KIỆN)

### 2.1. Định dạng Log bắt buộc
* **Tuyệt đối không sử dụng Plain Text Logging** (Log dạng chuỗi văn bản thuần túy).
* **Bắt buộc 100% sử dụng Structured Logging** (Cấu trúc dữ liệu JSON) thông qua thư viện `Serilog` kết hợp với cấu hình định dạng tương thích Elasticsearch.

```csharp
// SAI (Nghiêm cấm): Không truyền biến bằng phép cộng chuỗi hoặc nội suy chuỗi $""
_logger.LogInformation($"User {userId} login failed at {DateTime.Now} due to wrong password.");

// ĐÚNG: Sử dụng Message Template để tạo cấu trúc key-value tự động trong Elasticsearch
_logger.LogInformation("User {UserId} login failed. Reason: {FailureReason}", userId, reason);
```

### 2.2. Phân định Log Levels (Mức độ Log)
Nhà phát triển phải sử dụng đúng ý nghĩa của các Log Level theo bảng quy định sau:

| Log Level | Tình huống sử dụng | Hành động của Hệ thống / Vận hành |
| :--- | :--- | :--- |
| **FATAL** | Sự cố nghiêm trọng làm sập hoàn toàn ứng dụng hoặc luồng nghiệp vụ cốt lõi không thể phục hồi (Mất kết nối DB chính, Crash loop...). | Kích hoạt cảnh báo Pager/Slack/SMS ngay lập tức cho đội On-call. |
| **ERROR** | Lỗi xảy ra trong một request/chức năng cụ thể nhưng ứng dụng vẫn tiếp tục chạy được (Lỗi tính toán, lỗi HTTP 500 từ Dependency...). | Đẩy vào Dashboard lỗi, yêu cầu Dev kiểm tra trong vòng 24h. |
| **WARN** | Các hành vi bất thường hoặc tiềm ẩn nguy cơ nhưng hệ thống đã tự xử lý hoặc tự động khắc phục (Retry API thành công, Tải tài nguyên quá ngưỡng nhẹ...). | Theo dõi tần suất, nếu tần suất tăng cao phải chuyển thành Error. |
| **INFO** | Ghi lại các điểm mốc quan trọng trong luồng nghiệp vụ chính (Bắt đầu một tiến trình background, xử lý thành công đơn hàng...). | Lưu trữ để tra cứu luồng hoạt động (Audit trail). Không log trong vòng lặp. |
| **DEBUG** | Chi tiết kỹ thuật sâu phục vụ quá trình phát triển nội bộ (Giá trị biến, kết quả hàm trung gian...). | **Bắt buộc tắt** trên môi trường Production bằng bộ lọc cấu hình. |

### 2.3. Các trường dữ liệu (Metadata) bắt buộc trong cấu trúc Log
Mỗi dòng log xuất ra JSON phải tự động đính kèm các trường hệ thống sau (thông qua Serilog Enrichers):
* `Timestamp`: Thời gian chuẩn ISO 8601 UTC.
* `Environment`: Môi trường triển khai (`demo`, `staging`, `production`).
* `ServiceName`: Tên của dịch vụ xuất log (Ví dụ: `identity-service`, `order-service`).
* `ApplicationVersion`: Phiên bản code/tag đang chạy.
* `TraceId` và `SpanId`: Liên kết trực tiếp với hệ thống Tracing (OpenTelemetry).
* `Exception`: Nếu là log ERROR/FATAL, bắt buộc phải truyền toàn bộ đối tượng `Exception` để bóc tách `StackTrace`, không chỉ log mỗi `Exception.Message`.

### 2.4. Quy định Bảo mật thông tin trong Log (PII & Security)
Nghiêm cấm tuyệt đối ghi các thông tin sau vào Log hệ thống dưới dạng clear-text:
* Mật khẩu (Passwords), mã PIN, mã OTP.
* Số thẻ tín dụng đầy đủ (Bắt buộc phải mask, chỉ giữ lại 4 số cuối).
* Access Token, Refresh Token, Secret Keys.
* Thông tin định danh cá nhân nhạy cảm khi chưa được mã hóa hoặc xử lý che mờ (PII).

---

## 3. TIÊU CHUẨN METRICS (CHỈ SỐ ĐO LƯỜNG)

Hệ thống MVP Demo yêu cầu triển khai chỉ số đo lường dựa trên mô hình **RED Pattern** kết hợp với đo lường tài nguyên Runtime của .NET.

### 3.1. Mô hình RED Pattern cho các API/Endpoints
Đối với mọi Endpoint HTTP/gRPC, Dev phải đảm bảo OpenTelemetry thu thập đủ 3 chỉ số:
1.  **Rate (Tần suất):** Số lượng requests xử lý trên một đơn vị thời gian (Requests Per Second - RPS). Chia theo mã trạng thái HTTP (2xx, 4xx, 5xx).
2.  **Errors (Lỗi):** Số lượng hoặc tỉ lệ phần trăm các requests bị lỗi (Tập trung vào HTTP mã 5xx hoặc các Exception không được bắt).
3.  **Duration (Thời gian xử lý):** Đo lường độ trễ (Latency) của request.
    * *Yêu cầu bắt buộc:* Phải cấu hình đo lường theo Histogram để tính được các mốc phân vị **p95, p99** (95% và 99% request có thời gian xử lý dưới mức bao nhiêu ms). Không sử dụng chỉ số Average (Trung bình cộng) làm chỉ số quyết định.

### 3.2. Chỉ số System & .NET Runtime Metrics
Dev phải kích hoạt gói tích hợp tự động thu thập các thông số nền tảng của .NET 6+:
* **CPU & Memory Usage:** Lượng tài nguyên tiêu thụ của tiến trình ứng dụng.
* **Garbage Collection (GC) Stats:** Tần suất và thời gian tạm dừng (Pause time) của các phiên dọn rác (GC Gen 0, Gen 1, Gen 2).
* **Thread Pool:** Số lượng Worker Threads đang hoạt động, số lượng Thread nằm trong hàng đợi (Queue Length) để phát hiện Thread Starvation.

### 3.3. Custom Business Metrics (Chỉ số nghiệp vụ tùy biến)
Mỗi dịch vụ cần định nghĩa tối thiểu các chỉ số nghiệp vụ trọng yếu bằng `System.Diagnostics.Metrics.Meter`.
* *Ví dụ:* Bộ đếm đơn hàng thành công (`Counter`), Số lượng người dùng đang trực tuyến (`UpDownCounter`).

---

## 4. TIÊU CHUẨN TRACING (DẤU VẾT PHÂN TÁN)

Tracing là bắt buộc để QA và Dev có thể nhìn thấy bức tranh toàn cảnh của một Request đi qua nhiều tầng kiến trúc (Controller -> Service -> Repository -> Database / External API).

### 4.1. Quy định về Context Propagation (Truyền dẫn ngữ cảnh)
* Mọi request khởi đầu từ phía Gateway hoặc Client phải được cấp một mã `TraceId` duy nhất theo chuẩn **W3C Trace Context** (`traceparent` header).
* Khi dịch vụ thực hiện gọi các thành phần phụ thuộc bên ngoài (qua `HttpClient`) hoặc gửi message vào hàng đợi (RabbitMQ, Kafka), Dev **không được làm đứt chuỗi**. Phải cấu hình để OpenTelemetry tự động inject `TraceId` vào HTTP Header hoặc Message Metadata của hệ thống tiếp theo.

### 4.2. Khởi tạo Custom Spans (Hàm xử lý nội bộ phức tạp)
Đối với các hàm nghiệp vụ có logic tính toán phức tạp hoặc xử lý tốn thời gian, yêu cầu sử dụng `System.Diagnostics.Activity` để bọc lại thành một Span con (Child Span):

```csharp
private static readonly ActivitySource MyActivitySource = new("Company.AppName.ServiceName");

public async Task ProcessOrderAsync(Order order)
{
    // Khởi tạo một Span mới
    using Activity? activity = MyActivitySource.StartActivity("ProcessOrderLogic");
    
    // Gắn thông tin ngữ cảnh phục vụ việc tìm kiếm (Không gắn dữ liệu quá lớn)
    activity?.SetTag("order.id", order.Id);
    activity?.SetTag("order.total_amount", order.TotalAmount);

    try
    {
        // Thực hiện logic xử lý
        await _repository.SaveAsync(order);
    }
    catch (Exception ex)
    {
        // Bắt buộc đánh dấu Span lỗi và đính kèm thông tin Exception vào Trace
        activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
        activity?.RecordException(ex);
        throw;
    }
}
```

### 4.3. Cấu hình Auto-Instrumentation cho Dependencies
Dev phải cấu hình OpenTelemetry tự động bắt vết các thư viện ngoại vi:
* `OpenTelemetry.Instrumentation.AspNetCore`: Theo dõi toàn bộ vòng đời HTTP Request đi vào.
* `OpenTelemetry.Instrumentation.Http`: Theo dõi toàn bộ HTTP Request đi ra ngoại vi.
* `OpenTelemetry.Instrumentation.SqlClient` hoặc `OpenTelemetry.Instrumentation.EntityFrameworkCore`: Tự động bắt vết thời gian thực thi, câu lệnh SQL gửi tới Database (Lưu ý cấu hình ẩn thông tin tham số nhạy cảm trong câu SQL).

---

## 5. QUY ĐỊNH THIẾT KẾ MONITORING DASHBOARD TRÊN KIBANA

Hệ thống Dashboard giám sát trên Kibana cho phiên bản MVP phải được chia làm 2 màn hình quản trị chuyên biệt:

### Màn hình 1: High-Level Executive Overview (Giao diện Vận hành & Cảnh báo nhanh)
*Mục tiêu: Cung cấp trạng thái sức khỏe tổng quan của hệ thống trong vòng 5 giây nhìn.*

* **Khối 1: Sức khỏe Hệ thống (KPI Lớn - Màu sắc thay đổi theo trạng thái):**
    * Trạng thái Liveness/Readiness của dịch vụ (Xanh: OK, Đỏ: Sập).
    * Tỉ lệ lỗi toàn hệ thống hiện tại (Yêu cầu: < 1%).
* **Khối 2: Biểu đồ Đường (Time-series Line Chart):**
    * Lưu lượng Request (RPS) theo thời gian thực (Trục X: Thời gian, Trục Y: Số lượng request).
    * Biểu đồ Latency p95 và p99 chồng dịch để thấy rõ xu hướng phản hồi chậm của hệ thống.
* **Khối 3: Biểu đồ Vùng/Cột (Error Distribution):**
    * Tỉ lệ phân bố mã lỗi HTTP 5xx và 4xx.

### Màn hình 2: Developer & QA Deep-Dive (Giao diện Điều tra Lỗi & Tối ưu hóa)
*Mục tiêu: Phục vụ QA và Dev tìm chính xác nguyên nhân gây lỗi hoặc gây chậm.*

* **Bảng 1: Top 10 Slowest Endpoints (Bảng thống kê):**
    * Liệt kê danh sách các API Route có thời gian p95 lớn nhất.
    * Các cột thông tin: `API Route`, `Method`, `p95 Latency (ms)`, `Max Latency (ms)`, `Call Count`.
* **Bảng 2: Top 10 Most Error-Prone Endpoints:**
    * Liệt kê các API Route ném ra nhiều mã lỗi 500 hoặc Exception nhất.
* **Khối 3: Embedded Trace & Log Viewer:**
    * Thanh tìm kiếm theo `TraceId`. Khi nhập `TraceId`, Kibana phải hiển thị cấu trúc cây (Tree view) của Request đó kèm theo tất cả các Log dòng (Logs) tương ứng có cùng `TraceId` xếp theo thứ tự thời gian.

---

## 6. PHỤ LỤC: CẤU HÌNH CÀI ĐẶT MẪU (BOILERPLATE CODE FOR DEV)

Yêu cầu Dev áp dụng cấu hình mẫu sau vào file `Program.cs` của ứng dụng .NET 6+ để đảm bảo tính đồng bộ của hệ thống Observability:

```csharp
using Serilog;
using Serilog.Events;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

var builder = WebApplication.CreateBuilder(args);

// ==========================================
// 1. CẤU HÌNH SERILOG (STRUCTURED LOGGING)
// ==========================================
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Information()
    .MinimumLevel.Override("Microsoft", LogEventLevel.Warning) // Giảm log rác từ framework
    .Enrich.FromLogContext()
    .Enrich.WithProperty("Environment", builder.Environment.EnvironmentName)
    .Enrich.WithProperty("ServiceName", "mvp-demo-service")
    .WriteTo.Console(new Serilog.Formatting.Json.JsonFormatter()) // Log ra Console dạng JSON phục vụ thu thập
    .CreateLogger();

builder.Host.UseSerilog();

// ==========================================
// 2. CẤU HÌNH OPENTELEMETRY (METRICS & TRACES)
// ==========================================
var resourceBuilder = ResourceBuilder.CreateDefault()
    .AddService("mvp-demo-service", serviceVersion: "1.0.0");

builder.Services.AddOpenTelemetry()
    .WithTracing(tracerProviderBuilder =>
    {
        tracerProviderBuilder
            .SetResourceBuilder(resourceBuilder)
            .AddAspNetCoreInstrumentation(options => {
                options.RecordException = true; // Tự động ghi Exception vào Trace span
            })
            .AddHttpClientInstrumentation()
            .AddSqlClientInstrumentation(options => {
                options.SetDbStatementForText = true; // Thu thập câu lệnh SQL dạng text công khai
            })
            .AddSource("Company.AppName.ServiceName")
            .AddOtlpExporter(opt => {
                opt.Endpoint = new Uri(builder.Configuration["Otel:OtlpEndpoint"] ?? "http://localhost:4317");
            });
    })
    .WithMetrics(metricProviderBuilder =>
    {
        metricProviderBuilder
            .SetResourceBuilder(resourceBuilder)
            .AddAspNetCoreInstrumentation()
            .AddRuntimeInstrumentation() // Kích hoạt .NET runtime metrics (GC, ThreadPool...)
            .AddHttpClientInstrumentation()
            .AddOtlpExporter(opt => {
                opt.Endpoint = new Uri(builder.Configuration["Otel:OtlpEndpoint"] ?? "http://localhost:4317");
            });
    });

var app = builder.Build();

// Thêm Endpoint kiểm tra sức khỏe bắt buộc cho hạ tầng giám sát
app.MapHealthChecks("/healthz");
app.MapHealthChecks("/ready");

app.MapGet("/api/demo", () => "MVP Observability Standard OK!");

app.Run();
