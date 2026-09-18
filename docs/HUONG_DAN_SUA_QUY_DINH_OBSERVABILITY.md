# HƯỚNG DẪN ĐIỀU CHỈNH VĂN BẢN QUY ĐỊNH OBSERVABILITY

> **Dành cho:** Người phụ trách chỉnh sửa văn bản quy định trên SharePoint / Word  
> **Tài liệu gốc cần sửa:** `ISC_QuyDinh_Observability_v1_0.docx` (hoặc bản PDF tương ứng)  
> **Mục tiêu:** Đồng bộ văn bản quy định với thực tế vận hành hạ tầng ISC, bộ quy chuẩn `indexing-rules` và SDK `ISC.Observability v1.4.2`.  
> **Cách làm:** Tìm đúng vị trí đề mục trong file Word, xem đối chiếu **Nội dung cũ** và copy toàn bộ **Nội dung mới** dán đè lên.

---

## DANH SÁCH 8 HẠNG MỤC CẦN SỬA ĐỔI

---

### HẠNG MỤC 1: SỬA CÁC TIÊU ĐỀ BỊ LỖI LẶP TỪ (CHÍNH TẢ)
*Trong văn bản hiện tại, hầu hết tiêu đề các mục đang bị lặp lại từ cuối cùng do lỗi sao chép văn bản.*

| Trang | Vị trí mục | Tiêu đề HIỆN TẠI (Bị lỗi) | Tiêu đề MỚI (Copy & Paste đè lên) |
|:---:|---|---|---|
| **Trang 2** | Mục 3.1 | 3.1 Phân công trách nhiệm **nhiệm** | **3.1 Phân công trách nhiệm** |
| **Trang 3** | Mục 3.2 | 3.2 Mức độ tuân thủ và thẩm quyền xác định **định** | **3.2 Mức độ tuân thủ và thẩm quyền xác định** |
| **Trang 4** | Mục 4.1 | 4.1 Cấu trúc bản ghi log**ghi log** | **4.1 Cấu trúc bản ghi log** |
| **Trang 4** | Mục 4.2 | 4.2 Các điểm bắt buộc ghi log**ghi log** | **4.2 Các điểm bắt buộc ghi log** |
| **Trang 4** | Mục 4.3 | 4.3 Các hành vi không được phép **phép** | **4.3 Các hành vi không được phép** |
| **Trang 5** | Mục 5.1 | 5.1 Truyền trace context giữa các service**các service** | **5.1 Truyền trace context giữa các service** |
| **Trang 5** | Mục 5.2 | 5.2 Các span bắt buộc khởi tạo **tạo** | **5.2 Các span bắt buộc khởi tạo** |
| **Trang 5** | Mục 5.3 | 5.3 Nguyên tắc thực hiện **hiện** | **5.3 Nguyên tắc thực hiện** |
| **Trang 6** | Mục 6.1 | 6.1 Danh mục metrics bắt buộc **buộc** | **6.1 Danh mục metrics bắt buộc** |
| **Trang 6** | Mục 6.2 | 6.2 Quy tắc đặt tên metrics**tên metrics** | **6.2 Quy tắc đặt tên metrics** |
| **Trang 6** | Mục 7.1 | 7.1 Tham số cấu hình bắt buộc **buộc** | **7.1 Tham số cấu hình chuẩn cho ứng dụng** |
| **Trang 7** | Mục 7.3 | 7.3 Anti-pattern bị nghiêm cấm **cấm** | **7.3 Anti-pattern bị nghiêm cấm** |
| **Trang 8** | Mục 9.3 | 9.3 Hạ tầng & Dashboard**tầng & Dashboard** | **9.3 Hạ tầng & Dashboard** |

---

### HẠNG MỤC 2: MỤC 2 - THUẬT NGỮ VÀ ĐỊNH NGHĨA (Trang 1)

* **Vị trí cần tìm:** Dòng định nghĩa thuật ngữ **`Label`** trong bảng Thuật ngữ.
* **Nội dung CŨ:**
  > `Label`: Nhãn phân loại gắn kèm metric, ví dụ theo service hoặc theo route.
* **Nội dung MỚI (Copy & Paste đè lên dòng này):**
  > `Attributes (Labels)`: Nhãn phân loại gắn kèm metric, trace, log (ví dụ: theo `service_name` hoặc theo `route`). Trong chuẩn OpenTelemetry gọi là Attributes, trong Prometheus gọi là Labels.

---

### HẠNG MỤC 3: MỤC 4.1 - CẤU TRÚC BẢN GHI LOG (Trang 4)

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
  *(kèm dòng: BLOCKER: Thiếu trace_id, service hoặc level...)*

* **Nội dung MỚI (Copy & Paste toàn bộ khối bên dưới đè lên Mục 4.1):**

  > **4.1 Cấu trúc bản ghi log**
  >
  > ```json
  > {
  >   "timestamp": "2026-09-18T06:40:00.123Z",
  >   "level": "INFO",
  >   "service_name": "payment-svc",
  >   "environment": "production",
  >   "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  >   "span_id": "00f067aa0ba902b7",
  >   "correlation_id": "req-9b1deb4d-3b7d-4bad-9bdd",
  >   "message": "Payment authorized"
  > }
  > ```
  >
  > **BLOCKER:** Thiếu `trace_id`, `service_name` hoặc `level` — log không dùng được để điều tra sự cố.
  >
  > **Các trường bắt buộc trong bản ghi log:**
  > | Tên trường | Tính bắt buộc | Ý nghĩa |
  > |---|---|---|
  > | `timestamp` | Bắt buộc | Thời gian ghi nhận sự kiện theo chuẩn ISO 8601 UTC. |
  > | `level` | Bắt buộc | Mức độ nghiêm trọng của log (`INFO`, `WARN`, `ERROR`). |
  > | `service_name` | Bắt buộc | Tên microservice (định dạng `kebab-case` kèm hậu tố `-svc`). |
  > | `environment` | Bắt buộc | Môi trường triển khai (`production`, `staging`, `dev`). |
  > | `trace_id` | Bắt buộc | Mã định danh truy vết phân tán xuyên suốt các service. |
  > | `span_id` | Bắt buộc | Mã định danh công đoạn thực thi hiện tại. |
  > | `correlation_id` | Bắt buộc | Mã đối soát request từ Client/Gateway gửi vào. |
  > | `message` | Bắt buộc | Nội dung thông điệp mô tả sự kiện. |

---

### HẠNG MỤC 4: MỤC 5.1 - TRUYỀN TRACE CONTEXT GIỮA CÁC SERVICE (Trang 5)

* **Vị trí cần tìm:** Đoạn văn bản đầu tiên của **Mục 5.1**.
* **Nội dung CŨ:**
  > Áp dụng chuẩn W3C Trace Context. Mọi lời gọi tới service khác phải mang header sau:  
  > `traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`
* **Nội dung MỚI (Copy & Paste đè lên đoạn văn bản trên):**
  > Áp dụng đồng thời chuẩn **W3C Trace Context** và **B3 Propagator** (cho cụm Istio / Envoy Service Mesh). Mọi lời gọi tới service khác phải mang header hợp lệ:  
  > • Chuẩn W3C: `traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`  
  > • Chuẩn Service Mesh: `x-b3-traceid: 4bf92f3577b34da6a3ce929d0e0e4736` (SDK tự động cấu hình qua `CompositeTextMapPropagator`).

---

### HẠNG MỤC 5: MỤC 5.2 - BẢNG CÁC SPAN BẮT BUỘC KHỞI TẠO (Trang 5)

* **Vị trí cần tìm:** Dòng thứ 2 trong bảng ở Mục 5.2 (Hoạt động: *Gọi HTTP ra ngoài*).
* **Nội dung CŨ:**
  > Tên span: `HTTP GET payment-service`
* **Nội dung MỚI (Copy & Paste đè lên ô Tên span):**
  > `HTTP GET payment-svc`
* *Lý do:* Tên service bắt buộc dùng định dạng kebab-case kèm hậu tố `-svc` theo quy định đặt tên microservice của ISC.

---

### HẠNG MỤC 6: MỤC 6.1 - DANH MỤC METRICS BẮT BUỘC (Trang 6)

* **Vị trí cần tìm:** Bảng danh mục metrics ở **Mục 6.1**.
* **Cách sửa:**
  1. Thêm **1 dòng mới** vào bảng:
     * Cột Metric: **`observability.sdk.active`**
     * Cột Kiểu: **`Gauge / Counter`**
     * Cột Label bắt buộc: **`service_name, environment, sdk_version`**
     * Cột Ý nghĩa: **`Tín hiệu xác nhận service đã tích hợp SDK chuẩn hóa (phục vụ Quality Gate 2)`**
  2. Đổi nhãn `service` ở tất cả các dòng khác trong bảng thành **`service_name`** (định dạng `snake_case`).

---

### HẠNG MỤC 7: MỤC 7.1 - THAM SỐ CẤU HÌNH BẮT BUỘC (Trang 6)

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

### HẠNG MỤC 8: MỤC 8 - QUY ĐỊNH VỀ DASHBOARD GIÁM SÁT (Trang 8)

* **Vị trí cần tìm:** Dòng **Layer 4 · QA Compliance Tracker** trong bảng ở Mục 8.
* **Nội dung CŨ:**
  > Nội dung bắt buộc: Đối chiếu tuân thủ tại Quality Gate 2 (Mức độ: BLOCKER)
* **Nội dung MỚI (Copy & Paste đè lên ô Nội dung bắt buộc):**
  > Giám sát metric `observability.sdk.active = 1`, tỷ lệ truyền TraceId và đối chiếu đủ 3 trụ cột (Logs, Traces, Metrics) tại Quality Gate 2 (Mức độ: BLOCKER).
