# HƯỚNG DẪN ĐIỀU CHỈNH VĂN BẢN QUY ĐỊNH OBSERVABILITY

> **Dành cho:** Người phụ trách chỉnh sửa văn bản quy định trên SharePoint / Word  
> **Tài liệu gốc cần sửa:** `ISC_QuyDinh_Observability_v1_0.docx` (hoặc bản PDF tương ứng)  
> **Mục tiêu:** Đồng bộ văn bản quy định với thực tế vận hành hạ tầng ISC và SDK `ISC.Observability v1.4.3`.  
> **Cách làm:** Tìm đúng vị trí đề mục trong file Word, xem đối chiếu **Nội dung cũ** và copy toàn bộ **Nội dung mới** dán đè lên.

---

## DANH SÁCH 7 HẠNG MỤC CẦN SỬA ĐỔI

---

### HẠNG MỤC 1: MỤC 2 - THUẬT NGỮ VÀ ĐỊNH NGHĨA (Trang 1)

* **Vị trí cần tìm:** Dòng định nghĩa thuật ngữ **`Label`** và **`Latency`** trong bảng Thuật ngữ.
* **Nội dung CŨ:**
  > `Label`: Nhãn phân loại gắn kèm metric, ví dụ theo service hoặc theo route.  
  > `Latency`: Thời gian xử lý một request.
* **Nội dung MỚI (Copy & Paste đè lên 2 dòng tương ứng):**
  > `Attributes (Labels)`: Nhãn phân loại gắn kèm metric, trace, log (ví dụ: theo `service_name` hoặc theo `route`). Trong chuẩn OpenTelemetry gọi là Attributes, trong Prometheus gọi là Labels.  
  > `Latency`: Thời gian xử lý một request, đo lường theo các phân vị **p50, p95, p99** (thay vì giá trị trung bình) để phản ánh trung thực chất lượng dịch vụ.

---

### HẠNG MỤC 2: MỤC 4.1 - CẤU TRÚC BẢN GHI LOG (Trang 4)

* **Vị trí cần tìm:** Toàn bộ khối JSON và ghi chú tại **Mục 4.1**.
* **Nội dung CŨ:**
  ```json
  { 
    "timestamp": "2026-09-17T10:23:45.123Z", 
    "level": "INFO", 
    "service": "payment-service", 
    "env": "prod", 
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736", 
    "span_id": "00f067aa0ba902b7", 
    "event": "payment.authorized", 
    "message": "Payment authorized", 
    "duration_ms": 128, 
    "order_id": "ORD-10422" 
  } 
  ```
  *(kèm dòng: BLOCKER: Thiếu trace_id, service hoặc level — log không dùng được để điều tra sự cố.)*

* **Nội dung MỚI (Copy & Paste toàn bộ khối bên dưới đè lên Mục 4.1):**

  > **4.1 Cấu trúc bản ghi log**
  >
  > Toàn bộ log xuất ra từ ứng dụng phải tuân thủ định dạng JSON có cấu trúc. Cấu trúc bản ghi log bắt buộc phải có đầy đủ các trường thực tế do SDK xuất ra như sau:
  >
  > ```json
  > {
  >   "timestamp": "2026-09-18T06:40:00.123Z",
  >   "severity_text": "Information",
  >   "service_name": "payment-svc",
  >   "environment": "production",
  >   "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  >   "span_id": "00f067aa0ba902b7",
  >   "correlation_id": "req-9b1deb4d-3b7d-4bad-9bdd",
  >   "message": "Payment authorized"
  > }
  > ```
  >
  > **BLOCKER:** Thiếu `trace_id`, `service_name` hoặc `severity_text` — log không dùng được để điều tra sự cố. Cố tình ghi đè hoặc vô hiệu hóa các trường này sẽ bị từ chối phê duyệt Merge Request / Quality Gate 2.
  >
  > **Các trường bắt buộc trong bản ghi log:**
  > | Tên trường | Tính bắt buộc | Ý nghĩa |
  > |---|---|---|
  > | `timestamp` | Bắt buộc | Thời gian ghi nhận sự kiện theo chuẩn ISO 8601 UTC. |
  > | `severity_text` | Bắt buộc | Mức độ nghiêm trọng của log theo chuẩn OTLP (`Information`, `Warning`, `Error`). |
  > | `service_name` | Bắt buộc | Tên microservice (định dạng `kebab-case` kèm hậu tố `-svc`). |
  > | `environment` | Bắt buộc | Môi trường triển khai (`production`, `staging`, `dev`). |
  > | `trace_id` | Bắt buộc | Mã định danh truy vết phân tán xuyên suốt các service. |
  > | `span_id` | Bắt buộc | Mã định danh công đoạn thực thi hiện tại. |
  > | `correlation_id` | Bắt buộc | Mã đối soát request từ Client/Gateway gửi vào. |
  > | `message` | Bắt buộc | Nội dung thông điệp mô tả sự kiện. |

---

### HẠNG MỤC 3: MỤC 5.1 - TRUYỀN TRACE CONTEXT GIỮA CÁC SERVICE (Trang 5)

* **Vị trí cần tìm:** Đoạn văn bản đầu tiên của **Mục 5.1**.
* **Nội dung CŨ:**
  > Áp dụng chuẩn W3C Trace Context. Mọi lời gọi tới service khác phải mang header sau:  
  > `traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`
* **Nội dung MỚI (Copy & Paste đè lên đoạn văn bản trên):**
  > Áp dụng đồng thời chuẩn **W3C Trace Context** và **B3 Propagator** (cho cụm Istio / Envoy Service Mesh). Mọi lời gọi tới service khác phải mang header hợp lệ:  
  > • Chuẩn W3C: `traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`  
  > • Chuẩn Service Mesh: `x-b3-traceid: 4bf92f3577b34da6a3ce929d0e0e4736` (SDK tự động cấu hình qua `CompositeTextMapPropagator`).

---

### HẠNG MỤC 4: MỤC 5.2 - BẢNG CÁC SPAN BẮT BUỘC KHỞI TẠO (Trang 5)

* **Vị trí cần tìm:** Dòng thứ 2 trong bảng ở Mục 5.2 (Hoạt động: *Gọi HTTP ra ngoài*).
* **Nội dung CŨ:**
  > Tên span: `HTTP GET payment-service`
* **Nội dung MỚI (Copy & Paste đè lên ô Tên span):**
  > `HTTP GET payment-svc`
* *(Lý do: Tên service bắt buộc dùng định dạng kebab-case kèm hậu tố `-svc` theo quy định đặt tên microservice của ISC).*

---

### HẠNG MỤC 5: MỤC 6.1 VÀ 6.2 - QUY ĐỊNH VỀ METRICS VÀ LABELS (Trang 6)

* **Vị trí cần tìm:** Toàn bộ bảng metrics ở **Mục 6.1** và các gạch đầu dòng ở **Mục 6.2**.
* **Nội dung CŨ:**
  * Bảng Mục 6.1 cũ:
    | Metric | Kiểu | Label bắt buộc | Ý nghĩa |
    |---|---|---|---|
    | `http_server_requests_total` | Counter | `service, route, method, status` | Số request, suy ra RPS và Error Rate |
    | `http_server_duration_ms` | Histogram | `service, route, method` | Latency p50/p95/p99 |
    | `app_errors_total` | Counter | `service, error_code` | Số lỗi theo loại |
    | `app_dependency_duration_ms` | Histogram | `service, target` | Thời gian gọi hệ thống ngoài |
  * Mục 6.2 cũ:
    * Chữ thường, phân cách bằng `_`, kết thúc bằng đơn vị (`_ms`, `_bytes`, `_total`)
    * Label không chứa giá trị biến thiên cao (`user_id`, `order_id`, `email`) — gây nổ cardinality
    * BLOCKER: Đặt ID người dùng hoặc ID giao dịch làm label của metric.

* **Nội dung MỚI (Copy & Paste toàn bộ đoạn dưới đè lên Mục 6.1 và 6.2):**

  > **6.1 Danh mục metrics bắt buộc**
  >
  > | Metric | Kiểu | Labels (Attributes) bắt buộc | Ý nghĩa | Cơ chế sinh |
  > |---|---|---|---|---|
  > | `http_server_requests_total` | Counter | `service_name`, `route`, `method`, `status_code` | Tổng số request, tính RPS và Error Rate | SDK tự động 100% |
  > | `http_server_duration_ms` | Histogram | `service_name`, `route`, `method` | Thời gian xử lý request (Latency p50/p95/p99) | SDK tự động 100% |
  > | `observability.sdk.active` | Counter/Gauge | `service_name`, `environment`, `sdk_version` | Tín hiệu xác nhận service đã tích hợp SDK chuẩn hóa | SDK tự động 100% |
  > | `app_errors_total` | Counter | `service_name`, `error_code` | Số lỗi nghiệp vụ theo phân loại mã lỗi | Developer tự gắn |
  > | `app_dependency_duration_ms` | Histogram | `service_name`, `target` | Thời gian gọi hệ thống ngoài (DB, API, Queue) | Developer tự gắn |
  >
  > *(Lưu ý: `service_name` là Resource Attribute do SDK tự động gắn ở cấp ứng dụng, Developer không cần truyền thủ công trong từng câu lệnh đo metric).*
  >
  > **6.2 Quy tắc đặt tên metrics và quản lý Labels (Chống bùng nổ Cardinality)**
  > • Tên metric: Chữ thường, phân cách bằng dấu gạch dưới `_`, kết thúc bằng đơn vị tính (`_total`, `_ms`, `_bytes`).  
  > • Tên label (Label Key): 100% sử dụng định dạng `snake_case` (ví dụ: `service_name`, `status_code`, `error_code`).  
  > • **Quy chuẩn nhãn `route`:** Bắt buộc dùng **Route Template** (ví dụ: `/api/orders/{id}`), tuyệt đối không dùng raw URL chứa ID cụ thể.  
  > • **Quy chuẩn nhãn `status_code`:** Bắt buộc là mã HTTP (ví dụ: `200`, `400`, `500`).  
  > • **Quy chuẩn nhãn `method`:** Giá trị viết HOA (`GET`, `POST`, `PUT`, `DELETE`).  
  > • **Quy chuẩn nhãn `error_code`:** Là mã danh mục lỗi nghiệp vụ (ví dụ: `PAYMENT_TIMEOUT`), nghiêm cấm đưa exception message vào nhãn.  
  > • **Quy chuẩn nhãn `target`:** Là tên microservice đích (ví dụ: `billing-svc`) hoặc hostname bên thứ ba, không đưa URL kèm tham số.  
  >
  > **BLOCKER:** Đặt giá trị biến thiên cao (User ID, Order ID, Transaction ID, Raw URL, Error Message) làm label của metric gây sập hạ tầng giám sát.

---

### HẠNG MỤC 6: MỤC 7.1 - THAM SỐ CẤU HÌNH BẮT BUỘC (Trang 6)

* **Vị trí cần tìm:** Toàn bộ nội dung chữ và code ở **Mục 7.1**.
* **Nội dung CŨ:**
  ```properties
  OTEL_SERVICE_NAME=payment-service
  OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
  OTEL_EXPORTER_OTLP_PROTOCOL=grpc
  OTEL_RESOURCE_ATTRIBUTES=deployment.environment=prod,service.version=2.4.0
  OTEL_SERVICE_NAME trùng tên service trên dashboard và trùng field service trong log.
  ```
* **Nội dung MỚI (Copy & Paste toàn bộ đoạn dưới đè lên Mục 7.1):**

  > **7.1 Tham số cấu hình chuẩn cho ứng dụng**
  > 
  > **A. Đối với ứng dụng .NET (Sử dụng SDK `ISC.Observability`):**  
  > Cấu hình trong file `appsettings.json` (hoặc ánh xạ sang biến môi trường K8s dạng `Otel__*`):
  > ```json
  > {
  >   "ServiceName": "payment-svc",
  >   "Otel": {
  >     "Protocol": "http",
  >     "OtlpHttpEndpoint": "http://otel-collector:4318"
  >   }
  > }
  > ```
  > *(Mặc định SDK sử dụng giao thức OTLP HTTP Protobuf qua cổng 4318 hoặc cổng 80 Ingress để đảm bảo tương thích 100% với hạ tầng mạng ISC).*
  > 
  > **B. Đối với Service đa ngôn ngữ (Node.js, Python, Go) hoặc cấu hình Pod K8s:**  
  > Khai báo qua biến môi trường chuẩn OpenTelemetry:
  > ```properties
  > OTEL_SERVICE_NAME=payment-svc
  > OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
  > OTEL_EXPORTER_OTLP_PROTOCOL=http
  > OTEL_RESOURCE_ATTRIBUTES=deployment.environment=production,service.version=1.4.2
  > ```

---

### HẠNG MỤC 7: MỤC 8 - QUY ĐỊNH VỀ DASHBOARD GIÁM SÁT (Trang 8)

* **Vị trí cần tìm:** Dòng **Layer 4 · QA Compliance Tracker** trong bảng ở Mục 8.
* **Nội dung CŨ:**
  > Nội dung bắt buộc: Đối chiếu tuân thủ tại Quality Gate 2 (Mức độ: BLOCKER)
* **Nội dung MỚI (Copy & Paste đè lên ô Nội dung bắt buộc):**
  > Giám sát metric `observability.sdk.active = 1`, tỷ lệ truyền TraceId và đối chiếu đủ 3 trụ cột (Logs, Traces, Metrics) tại Quality Gate 2 (Mức độ: BLOCKER).

---

### HẠNG MỤC 8: MỤC 9.2 - TIÊU CHÍ NGHIỆM THU TRACING & METRICS (Trang 8)

* **Vị trí cần tìm:** Khối checklist tại **Mục 9.2**.
* **Nội dung CŨ:**
  ```text
  ☐ Mọi request mang TraceId và SpanId
  ☐ TraceId liên tục qua toàn bộ luồng xử lý giữa các service
  ☐ Log correlate được về đúng TraceId của request
  ☐ Đủ metrics RPS, Latency, Error Rate, CPU
  ```
* **Nội dung MỚI (Bổ sung thêm dòng thứ 5 vào checklist):**
  ```text
  ☐ Mọi request mang TraceId và SpanId
  ☐ TraceId liên tục qua toàn bộ luồng xử lý giữa các service
  ☐ Log correlate được về đúng TraceId của request
  ☐ Đủ metrics RPS, Latency, Error Rate, CPU
  ☐ Có phát tín hiệu xác nhận tích hợp SDK chuẩn hóa (observability.sdk.active = 1)
  ```
* *(Lý do: Đồng bộ tiêu chí nghiệm thu Quality Gate 2 của QA theo đúng quy định tại Mục 8 Layer 4).*
