# QUY ĐỊNH OBSERVABILITY (BẢN ĐỀ XUẤT ĐIỀU CHỈNH v1.1)

**Mã hiệu:** 12-QĐ/PM/HDCV/ISC  
**Lần ban hành/sửa đổi:** 1/1  
**Ngày hiệu lực:** Kể từ ngày ký  
**Tài liệu tham chiếu:** [Observability Standard Portal](https://santete.github.io/observability-standard/)

---

## 1. MỤC ĐÍCH VÀ PHẠM VI ÁP DỤNG
Quy định này xác lập các yêu cầu bắt buộc về logging, tracing và metrics đối với mọi service do Trung tâm phát triển hoặc vận hành, nhằm bảo đảm năng lực giám sát, điều tra sự cố và kiểm soát chất lượng vận hành.

---

## 2. THUẬT NGỮ VÀ ĐỊNH NGHĨA

| Thuật ngữ | Giải thích |
|---|---|
| **Observability** | Năng lực hiểu được trạng thái bên trong của service thông qua dữ liệu service phát ra: log, trace và metrics. |
| **Log** | Bản ghi một sự kiện xảy ra tại một thời điểm, kèm ngữ cảnh nghiệp vụ. |
| **Structured log** | Log ghi dưới dạng JSON có các field cố định, máy đọc và truy vấn được, thay cho câu văn tự do. |
| **Trace** | Toàn bộ hành trình của một request đi qua các service, ghép lại từ nhiều span. |
| **Span** | Một công đoạn trong trace (lời gọi API, truy vấn database), có thời điểm bắt đầu, kết thúc và thuộc tính đi kèm. |
| **TraceId / SpanId** | Mã định danh của trace và của từng span, dùng để ghép log và span về đúng một request. |
| **Trace context** | Thông tin TraceId/SpanId được truyền kèm lời gọi giữa các service để trace không bị đứt đoạn. |
| **Metrics** | Số liệu đo lường theo thời gian (số request, thời gian phản hồi, tỷ lệ lỗi, mức sử dụng tài nguyên). |
| **Attributes (Labels)** | Nhãn phân loại gắn kèm metric/span/log (ví dụ: theo `service_name` hoặc theo `route`). Trong chuẩn OpenTelemetry gọi là Attributes, trong Prometheus gọi là Labels. |
| **Cardinality** | Số lượng tổ hợp giá trị nhãn của một metric. Cardinality quá lớn làm hệ thống lưu trữ quá tải. |
| **Telemetry** | Tên gọi chung cho dữ liệu log, trace và metrics mà hệ thống phát ra. |
| **OpenTelemetry (OTel)** | Bộ chuẩn mở quốc tế về thu thập và truyền telemetry. |
| **OTLP** | Giao thức truyền telemetry tiêu chuẩn của OpenTelemetry (hỗ trợ HTTP Protobuf và gRPC). |
| **OTel Collector** | Thành phần trung gian nhận telemetry từ ứng dụng, xử lý tập trung rồi chuyển tới nơi lưu trữ. |
| **Golden Signals** | Bốn tín hiệu cốt lõi để đánh giá sức khỏe dịch vụ: traffic, latency, error, saturation. |
| **Latency** | Thời gian xử lý một request (tính theo phân vị p50/p95/p99 thay vì trung bình). |
| **APM** | Công cụ theo dõi hiệu năng ứng dụng ở mức chi tiết từng request (Application Performance Monitoring). |
| **Dashboard** | Màn hình tổng hợp hiển thị log, trace và metrics phục vụ giám sát vận hành. |
| **PII** | Dữ liệu định danh cá nhân: họ tên, số điện thoại, email, CCCD, số thẻ. |
| **Masking** | Che một phần hoặc toàn bộ dữ liệu nhạy cảm trước khi ghi ra log. |
| **Quality Gate** | Bộ tiêu chí bắt buộc phải đạt trước khi dự án được chuyển sang bước tiếp theo trong SDLC. |

---

## 3. TRÁCH NHIỆM CỦA CÁC BÊN LIÊN QUAN

### 3.1. Phân công trách nhiệm
| Vai trò | Trách nhiệm | Thời điểm thực hiện |
|---|---|---|
| **Developer** | Tích hợp SDK chuẩn, ghi log có cấu trúc, khởi tạo span và phát metrics cho phần mình phát triển. | Trong quá trình phát triển, trước khi tạo Merge Request. |
| **Tech Lead** | Kiểm tra log, trace và metrics; từ chối MR chưa đạt chuẩn. | Mỗi lần duyệt Merge Request. |
| **DevOps** | Cấu hình hạ tầng truyền telemetry (OTel Collector) và xây dựng dashboard. | Trước khi triển khai môi trường đầu tiên. |
| **QA** | Kiểm tra và xác nhận service đạt tiêu chí nghiệm thu telemetry (Layer 4). | Trước Quality Gate 2. |
| **PM** | Chỉ phê duyệt release khi đã đạt đủ tiêu chí nghiệm thu Quality Gate 2. | Trước Go-live. |

### 3.2. Mức độ tuân thủ và thẩm quyền xác định
| Mức độ | Áp dụng khi | Người xác định | Hành động |
|---|---|---|---|
| **BLOCKER** | Vi phạm một điều được đánh dấu BLOCKER trong quy định này. | Tech Lead khi duyệt MR; PM tại Quality Gate 2 | **PHẢI fix trước khi release.** Không ngoại lệ. |
| **REQUIRED** | Thiếu một nội dung bắt buộc nhưng chưa làm mất khả năng điều tra sự cố. | Tech Lead khi duyệt MR; PM tại Quality Gate 2 | PHẢI fix trong release này hoặc tạo ticket kèm hạn xử lý trước khi release. |
| **GOOD PRACTICE** | Nội dung khuyến nghị, tối ưu hóa hệ thống. | Team phát triển | Tự quyết định, không dùng làm căn cứ từ chối MR. |

---

## 4. QUY ĐỊNH VỀ LOGGING

### 4.1. Cấu trúc bản ghi log
Mẫu tin log xuất ra từ ứng dụng phải tuân thủ định dạng JSON có cấu trúc (Structured JSON). Cấu trúc bản ghi log bắt buộc phải có đầy đủ các trường thực tế do SDK xuất ra như sau:

```json
{
  "timestamp": "2026-09-18T06:40:00.123Z",
  "severity_text": "Information",
  "service_name": "payment-svc",
  "environment": "production",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "correlation_id": "req-9b1deb4d-3b7d-4bad-9bdd",
  "message": "Payment authorized"
}
```

> **BLOCKER:** Thiếu `trace_id`, `service_name` hoặc `severity_text` — log không dùng được để điều tra sự cố. Cố tình ghi đè hoặc vô hiệu hóa các trường này sẽ bị từ chối phê duyệt Merge Request / Quality Gate 2.

**Các trường bắt buộc trong bản ghi log:**
| Tên trường | Tính bắt buộc | Ý nghĩa |
|---|---|---|
| `timestamp` | Bắt buộc | Thời gian ghi nhận sự kiện theo chuẩn ISO 8601 UTC. |
| `severity_text` | Bắt buộc | Mức độ nghiêm trọng của log theo chuẩn OTLP (`Information`, `Warning`, `Error`). |
| `service_name` | Bắt buộc | Tên microservice (định dạng `kebab-case` kèm hậu tố `-svc`). |
| `environment` | Bắt buộc | Môi trường triển khai (`production`, `staging`, `dev`). |
| `trace_id` | Bắt buộc | Mã định danh truy vết phân tán xuyên suốt các service. |
| `span_id` | Bắt buộc | Mã định danh công đoạn thực thi hiện tại. |
| `correlation_id` | Bắt buộc | Mã đối soát request từ Client/Gateway gửi vào. |
| `message` | Bắt buộc | Nội dung thông điệp mô tả sự kiện. |

### 4.2. Các điểm bắt buộc ghi log
| Điểm | Level | Field thêm bắt buộc (`snake_case`) |
|---|---|---|
| Nhận request vào service | `INFO` | `endpoint`, `method` |
| Gọi hệ thống ngoài (API, queue) | `INFO` | `target`, `duration_ms`, `status` |
| Thay đổi trạng thái nghiệp vụ | `INFO` | `entity_id`, `trạng thái cũ → mới` |
| Lỗi nghiệp vụ có kiểm soát | `WARN` / `INFO` | `error_code`, `lý do` |
| Exception ngoài dự kiến | `ERROR` | `stack_trace`, `trace_id`, `error_code` |

### 4.3. Các hành vi không được phép
* ❌ Log dạng text tự do, ghép chuỗi không cấu trúc (phải dùng Message Template `{param}`).
* ❌ Log mật khẩu, token, số thẻ, CCCD, số điện thoại, email đầy đủ — **bắt buộc phải qua bộ lọc Masking của SDK trước khi ghi**.
* ❌ Log toàn bộ request/response body ở mức `INFO` (gây ngập lụt log rác).
* ❌ Dùng `Console.WriteLine`, `print`, `System.out` thay cho logger chuẩn.
* ❌ Sử dụng các Sink trực tiếp (`WriteTo.Kafka()`, `WriteTo.Elasticsearch()`) trong code ứng dụng.

---

## 5. QUY ĐỊNH VỀ TRACING

### 5.1. Truyền trace context giữa các service
Áp dụng đồng thời chuẩn **W3C Trace Context** và **B3 Propagator** (cho cụm Istio/Envoy Service Mesh). Mọi lời gọi tới service khác phải mang header hợp lệ:
* W3C Header: `traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`
* Service Mesh Header: `x-b3-traceid: 4bf92f3577b34da6a3ce929d0e0e4736` (SDK tự động xử lý qua `CompositeTextMapPropagator`).

> **BLOCKER:** Gọi service khác mà không truyền trace context — luồng bị đứt đoạn, không truy vết được.

### 5.2. Các span bắt buộc khởi tạo
| Hoạt động | Tên span | Attribute bắt buộc (`snake_case`) |
|---|---|---|
| HTTP request vào | `GET /api/orders/{id}` | `http.method`, `http.route`, `http.status_code` |
| Gọi HTTP ra ngoài | `HTTP GET payment-svc` | `http.url`, `http.status_code` |
| Truy vấn database | `SELECT orders` | `db.system`, `db.statement` (đã mask tham số) |
| Publish/consume message | `publish order.created` | `messaging.destination` |
| Xử lý nghiệp vụ dài > 200ms | `<domain>.<hành động>` | `entity_id` |

### 5.3. Nguyên tắc thực hiện
* Tên span mô tả hành động, không nhét ID vào tên (dùng `{id}` thay cho giá trị thật để tránh bùng nổ cardinality).
* Span lỗi phải set status `ERROR` kèm mô tả nguyên nhân.
* Log ghi trong một span phải mang đúng `trace_id` và `span_id` của span đó.

---

## 6. QUY ĐỊNH VỀ METRICS

### 6.1. Danh mục metrics bắt buộc
| Metric | Kiểu | Attributes (Labels) bắt buộc | Ý nghĩa |
|---|---|---|---|
| `http.server.request.duration` | Histogram | `service_name`, `http.route`, `http.request.method`, `http.response.status_code` | Thời gian phản hồi request (tính latency p50/p95/p99) |
| `http_server_requests_total` | Counter | `service_name`, `route`, `method`, `status` | Tổng số request, tính RPS và Error Rate |
| **`observability.sdk.active`** | **Gauge / Counter** | **`service_name`, `environment`, `sdk_version`** | **Tín hiệu tuân thủ SDK chuẩn hóa (phục vụ Quality Gate 2)** |
| `app_errors_total` | Counter | `service_name`, `error_code` | Số lỗi theo từng mã lỗi |
| `app_dependency_duration_ms` | Histogram | `service_name`, `target` | Thời gian phụ thuộc bên ngoài (DB, Cache, External API) |

> Các metrics tài nguyên hạ tầng (CPU, RAM, GC, ThreadPool) do runtime SDK cung cấp sẵn; dự án chỉ cần kích hoạt thu thập, không tự lập trình.

### 6.2. Quy tắc đặt tên metrics
* Chữ thường, phân cách bằng `_` hoặc `.`, thể hiện rõ đơn vị đo lường.
* Attributes/Labels không chứa giá trị biến thiên cao (`user_id`, `order_id`, `email`) — gây nổ cardinality làm quá tải backend lưu trữ.

> **BLOCKER:** Đặt ID người dùng hoặc ID giao dịch làm label/attribute của metric.

---

## 7. QUY ĐỊNH VỀ TRUYỀN TELEMETRY

### 7.1. Tham số cấu hình chuẩn cho hạ tầng ISC
Do hạ tầng mạng nội bộ ISC định tuyến qua Ingress HTTP/1.1 (cổng 80 hoặc 4318), các service **mặc định sử dụng giao thức OTLP HTTP Protobuf**:

```properties
# Service Name tuân thủ quy chuẩn R-SVC-001 (kebab-case + "-svc")
OTEL_SERVICE_NAME=payment-svc

# Endpoint OTLP HTTP mặc định của hạ tầng ISC
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http

# Metadata môi trường và phiên bản
OTEL_RESOURCE_ATTRIBUTES=deployment.environment=production,service.version=1.4.2
```

*(Lưu ý: Giao thức gRPC cổng `4317` chỉ áp dụng khi môi trường mạng nội bộ được DevOps xác nhận mở port 4317 trực tiếp).*

### 7.2. Single OTLP Path
```
[ Ứng dụng Microservices ]
            │
            ▼ (OTLP HTTP Protobuf duy nhất)
[ OpenTelemetry Collector ]
            │
            ├─► [ Kafka Topics ]
            └─► [ Elasticsearch / ClickHouse / SigNoz ]
                        │
                        ▼
            [ Dashboard & Kibana / SigNoz UI ]
```

### 7.3. Anti-pattern bị nghiêm cấm
> **BLOCKER:** TUYỆT ĐỐI KHÔNG được đẩy log hoặc trace trực tiếp từ Application vào Kafka hoặc Elasticsearch. Mọi telemetry phải đi qua OTel Collector.

| Cách làm SAI (Cấm) | Cách làm ĐÚNG (Chuẩn) |
|---|---|
| ❌ App cắm driver Kafka producer đẩy log trực tiếp | ✔️ App ➔ OTLP ➔ OTel Collector ➔ Kafka |
| ❌ App cắm client Elasticsearch đẩy log trực tiếp | ✔️ App ➔ OTLP ➔ OTel Collector ➔ Elasticsearch |
| ❌ Mỗi service tự chế đường đẩy riêng | ✔️ Một đường OTLP duy nhất cho toàn hệ thống |

---

## 8. QUY ĐỊNH VỀ DASHBOARD GIÁM SÁT (4 TẦNG)

| Tầng | Đối tượng phục vụ | Nội dung bắt buộc | Mức độ |
|---|---|---|---|
| **Layer 1 · Executive Overview** | Ban Điều hành, Quản lý | Golden Signals: traffic (RPS), latency, error rate, saturation. | REQUIRED |
| **Layer 2 · Developer Deep-Dive** | Developer, Tech Lead | APM chi tiết, truy vết Span Waterfall theo `TraceId`. | REQUIRED |
| **Layer 3 · Infrastructure & Runtime** | DevOps, SRE | CPU, RAM, GC Pause Time, ThreadPool Queue. | REQUIRED |
| **Layer 4 · QA Compliance Tracker** | QA, Quản lý chất lượng | **Giám sát metric `observability.sdk.active = 1` và đối chiếu tuân thủ tại Quality Gate 2.** | **BLOCKER** |

---

## 9. TIÊU CHÍ NGHIỆM THU TRƯỚC KHI RELEASE (QUALITY GATE 2)

### 9.1. Logging
- [x] Log đầu ra là Structured JSON, có ngữ cảnh nghiệp vụ theo `snake_case`.
- [x] Log đầy đủ các cột mốc quan trọng của luồng xử lý.
- [x] Không còn PII, secret, token hay password trong log (đã kích hoạt Masking).

### 9.2. Tracing & Metrics
- [x] Mọi request đều mang `TraceId` và `SpanId`.
- [x] `TraceId` liên tục, không bị đứt đoạn khi đi qua Service Mesh / Kafka.
- [x] Log tương quan (correlated) chính xác về `TraceId` của request.
- [x] Đầy đủ metrics RPS, Latency p95/p99, Error Rate, và metric **`observability.sdk.active`**.

### 9.3. Hạ tầng & Dashboard
- [x] Telemetry chỉ đi qua OTel Collector, không kết nối trực tiếp Kafka/Elasticsearch.
- [x] Dashboard Layer 1–4 hiển thị đúng dữ liệu thực tế của dự án.
- [x] QA xác nhận đạt Quality Gate 2.

> **BLOCKER:** Service không đáp ứng đầy đủ các tiêu chí tại mục 9.1, 9.2 và 9.3 **KHÔNG ĐƯỢC PHÉP PHÊ DUYỆT** triển khai lên môi trường Production.

---

## 10. ĐIỀU KHOẢN THI HÀNH
Quy định này có hiệu lực kể từ ngày ký ban hành và áp dụng cho toàn bộ dự án triển khai mới. Các service đang vận hành phải hoàn thành việc chuẩn hóa theo quy định này trong lần phát hành phiên bản gần nhất kể từ ngày hiệu lực.
