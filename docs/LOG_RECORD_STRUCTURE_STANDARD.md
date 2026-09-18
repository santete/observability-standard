# TIÊU CHUẨN CẤU TRÚC BẢN GHI LOG (SDK ISC.OBSERVABILITY v1.4.2)

> **Tài liệu tham chiếu:** Quy chuẩn nội bộ ISC (`R-OBS-FIELD-001`, `R-RESP-FIELD-001`, `R-SVC-001`)  
> **Áp dụng cho:** Tất cả Microservices chạy trên nền tảng .NET 8 / OpenTelemetry / Serilog

---

## 1. MẪU BẢN GHI LOG THỰC TẾ XUẤT RA TỪ SDK (JSON CHUẨN OTLP)

Dưới đây là cấu trúc mẫu tin JSON thực tế đầy đủ nhất được SDK `ISC.Observability` xuất ra và đẩy về cụm lưu trữ trung tâm (OpenTelemetry Collector ➔ SigNoz / Elasticsearch / ClickHouse):

```json
{
  /* =========================================================================
     NHÓM 1: CÁC TRƯỜNG CỐT LÕI MỨC PROTOCOL (TOP-LEVEL FIELDS) - BẮT BUỘC
     ========================================================================= */
  "timestamp": "2026-09-18T06:40:00.1234567Z",
  "severity_text": "Information",
  "severity_number": 9,
  "body": "Xử lý thanh toán đơn hàng ORD-10422 thành công cho khách hàng a***@fpt.com",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",

  /* =========================================================================
     NHÓM 2: ĐỊNH DANH TÀI NGUYÊN HỆ THỐNG (RESOURCE ATTRIBUTES) - BẮT BUỘC
     ========================================================================= */
  "resource": {
    "service.name": "payment-svc",                      // Bắt buộc: kebab-case + "-svc" (R-SVC-001)
    "service.version": "1.4.2",                         // Bắt buộc: Phiên bản ứng dụng / Git SHA
    "deployment.environment": "production"              // Bắt buộc: production | staging | dev
  },

  /* =========================================================================
     NHÓM 3: THUỘC TÍNH CHI TIẾT (ATTRIBUTES / CONTEXT)
     ========================================================================= */
  "attributes": {
    
    // --- [3.1] BẮT BUỘC DO SDK TỰ ĐỘNG ENRICH (Dev không cần code thêm) ---
    "service_name": "payment-svc",                      // Chuẩn R-OBS-FIELD-001
    "environment": "production",                        // Chuẩn R-OBS-FIELD-001
    "application_version": "1.4.2",                     // Chuẩn R-OBS-FIELD-001
    "machine_name": "pod-payment-svc-78f94c8b-2x9la",   // Tên Pod / Server vật lý
    "thread_id": 24,                                    // ID luồng xử lý của .NET runtime
    "correlation_id": "req-9b1deb4d-3b7d-4bad-9bdd",    // Mã xuyên suốt toàn bộ hành trình nghiệp vụ
    "request_id": "req-9b1deb4d-3b7d-4bad-9bdd",        // Đồng bộ chuẩn API meta.request_id
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",    // W3C Trace ID
    "span_id": "00f067aa0ba902b7",                      // W3C Span ID
    
    // --- [3.2] BẮT BUỘC ĐỐI VỚI HTTP REQUEST (SDK tự động gắn trong Middleware) ---
    "request_host": "api.domain.com",
    "request_path": "/v1/payments/process",
    "request_method": "POST",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",

    // --- [3.3] BIẾN NGHIỆP VỤ DO DEV GHI (BẮT BUỘC DÙNG snake_case THEO R-OBS-FIELD-001) ---
    "order_id": "ORD-10422",
    "payment_method": "qr_code",
    "amount": 150000.0,
    "transaction_id": "TX-998877",

    // --- [3.4] TỰ ĐỘNG CHE MỜ DỮ LIỆU NHẠY CẢM (PII Masking Enricher) ---
    "customer_email": "a***@fpt.com",                   // Email đã được mask tự động
    "customer_phone": "090*****89"                      // Số điện thoại đã được mask tự động
  }
}
```

---

## 2. BẢNG PHÂN ĐỊNH CHI TIẾT CÁC TRƯỜNG TRONG BẢN GHI LOG

| Tên trường | Kiểu dữ liệu | Tính bắt buộc | Bên chịu trách nhiệm | Ý nghĩa & Quy chuẩn |
|---|---|---|---|---|
| `timestamp` | String (ISO 8601) | **BẮT BUỘC** | **SDK** | Thời gian phát sinh sự kiện theo giờ UTC chuẩn. |
| `level` / `severity_text` | String | **BẮT BUỘC** | **SDK / Dev** | Mức độ log: `Information`, `Warning`, `Error`. |
| `trace_id` | String (Hex 32) | **BẮT BUỘC** | **SDK** | Mã định danh truy vết phân tán xuyên suốt các service. |
| `span_id` | String (Hex 16) | **BẮT BUỘC** | **SDK** | Mã định danh bước thực thi hiện tại trong service. |
| `correlation_id` | String (UUID) | **BẮT BUỘC** | **SDK** | Mã đối soát request từ Client hoặc Gateway gửi vào. |
| `service_name` | String | **BẮT BUỘC** | **SDK** | Tên microservice theo định dạng `kebab-case-svc` (`R-SVC-001`). |
| `environment` | String | **BẮT BUỘC** | **SDK** | Môi trường triển khai: `production`, `staging`, `development`. |
| `application_version` | String | **BẮT BUỘC** | **SDK** | Phiên bản ứng dụng lấy từ assembly version hoặc git hash. |
| `machine_name` | String | **BẮT BUỘC** | **SDK** | Tên Pod K8s hoặc Hostname máy chủ thực thi. |
| `thread_id` | Integer | **BẮT BUỘC** | **SDK** | ID Thread xử lý của runtime .NET. |
| `body` / `message` | String | **BẮT BUỘC** | **Developer** | Thông điệp log mô tả sự kiện (dùng Message Template). |
| **Các tham số nghiệp vụ** *(vd: `order_id`, `amount`)* | Tùy biến | **BẮT BUỘC** *(khi có)* | **Developer** | **PHẢI viết theo `snake_case`** (`R-OBS-FIELD-001`). Cấm dùng camelCase hoặc PascalCase. |

> [!CAUTION]
> **TIÊU CHÍ BLOCKER:** Bất kỳ bản ghi log nào thiếu một trong các trường: `trace_id`, `service_name`, hoặc `level` đều bị coi là **vi phạm nghiêm trọng** và sẽ bị từ chối phê duyệt Merge Request / Quality Gate 2 vì làm mất khả năng điều tra sự cố.

---

## 3. VÍ DỤ CODE C# TRONG ỨNG DỤNG ĐỂ SINH RA LOG CHUẨN

Developer chỉ cần viết code như bình thường, **toàn bộ các trường hệ thống sẽ do SDK tự động gắn**:

```csharp
[ApiController]
[Route("v1/payments")]
public class PaymentController : ControllerBase
{
    private readonly ILogger<PaymentController> _logger;

    public PaymentController(ILogger<PaymentController> logger)
    {
        _logger = logger;
    }

    [HttpPost("process")]
    public IActionResult ProcessPayment([FromBody] PaymentRequest request)
    {
        // ----------------------------------------------------------------------------------
        // CHUẨN R-OBS-FIELD-001: Developer đặt tên biến trong Template bắt buộc là snake_case
        // CÁC TRƯỜNG HỆ THỐNG: trace_id, correlation_id, service_name, environment, machine_name...
        // SẼ ĐƯỢC SDK TỰ ĐỘNG ĐÍNH KÈM VÀO BẢN GHI ĐẨY VỀ COLLECTOR!
        // ----------------------------------------------------------------------------------
        _logger.LogInformation(
            "Xử lý thanh toán đơn hàng {order_id} thành công cho khách hàng {customer_email} với số tiền {amount} qua cổng {payment_method}",
            request.OrderId,
            request.Email,       // SDK tự động che mờ (masking) thành "a***@fpt.com"
            request.Amount,
            request.PaymentMethod);

        return Ok(new { success = true });
    }
}
```
