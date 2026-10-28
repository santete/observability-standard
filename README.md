# 🔭 Observability Standard - MVP Demo

> Dự án mẫu chuẩn hóa Observability cho các dịch vụ .NET 8, tuân thủ [Quy định Tiêu chuẩn Observability](./docs/OBSERVABILITY_STANDARD.md) và [Kiến trúc Tiêu chuẩn](./docs/architecture_standard.md).
> 
> 🌐 **Xem tài liệu trình bày trực quan tại:** [https://santete.github.io/observability-standard/](https://santete.github.io/observability-standard/)

## 📋 Tổng quan

Dự án này cung cấp:

- **SDK Tiêu chuẩn (`ISC.Observability`)**: Gói thư viện dùng chung cho phép các service .NET tích hợp Observability chỉ với 1 dòng code. Hỗ trợ đa dạng Instrumentations (Redis, Mongo, Kafka, SQL, gRPC...). (👉 **[Xem Hướng dẫn sử dụng & Cấu hình SDK](src/ISC.Observability/README.md)**)
- **Sample Service (.NET 8)**: Dịch vụ quản lý đơn hàng (Order Management) sử dụng SDK trên.
- **Hạ tầng Docker**: Stack hoàn chỉnh bao gồm OpenTelemetry Collector, Elasticsearch, Kibana — sẵn sàng demo bằng một lệnh duy nhất.
- **Kibana Dashboards**: 4 dashboard tiêu chuẩn (Executive, Developer, Infrastructure, QA) được tự động import, phục vụ đầy đủ quy trình vận hành.

### Kiến trúc

```
┌─────────────────┐     OTLP/gRPC      ┌──────────────────┐    Bulk API     ┌───────────────┐
│  .NET 8 App     │ ──── :4317 ──────► │  OTel Collector   │ ─────────────► │ Elasticsearch │
│  (Serilog +     │     OTLP/HTTP      │  (contrib)        │  mapping:otel  │   (8.17.0)    │
│   OTel SDK)     │ ──── :4318 ──────► │                   │                │               │
└─────────────────┘                    └──────────────────┘                └───────┬───────┘
                                                                                   │
                                                                        ┌──────────▼──────────┐
                                                                        │   Kibana (8.17.0)   │
                                                                        │  • Executive View   │
                                                                        │  • Dev Deep-Dive    │
                                                                        │  • Infra & Runtime  │
                                                                        │  • QA Compliance    │
                                                                        └─────────────────────┘
```

## 🚀 Quick Start

### Yêu cầu

- [Docker](https://docs.docker.com/get-docker/) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)
- Ít nhất **4GB RAM** cho Docker

### Khởi chạy

```bash
# 1. Clone và vào thư mục dự án
cd observability-standard

# 2. Khởi chạy toàn bộ stack
docker compose up -d --build

# 3. Chờ tất cả services sẵn sàng (~60-90 giây)
docker compose ps

# 4. (Tùy chọn) Chạy Load Generator để tạo traffic giả lập
docker compose --profile load-test up -d
```

### Truy cập

| Service | URL | Mô tả |
|---|---|---|
| **Application** | [http://localhost:8080](http://localhost:8080) | .NET 8 API |
| **Kibana** | [http://localhost:5601](http://localhost:5601) | Dashboard & Visualization |
| **Elasticsearch** | [http://localhost:9200](http://localhost:9200) | Storage engine |
| **Health Check** | [http://localhost:8080/healthz](http://localhost:8080/healthz) | Liveness probe |

## 📡 API Endpoints

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/api/orders` | Danh sách tất cả đơn hàng |
| `GET` | `/api/orders/{id}` | Chi tiết đơn hàng |
| `POST` | `/api/orders` | Tạo đơn hàng mới |
| `PUT` | `/api/orders/{id}/status` | Cập nhật trạng thái đơn hàng |
| `POST` | `/api/orders/{id}/process` | Xử lý đơn hàng (simulate complex logic) |
| `GET` | `/api/orders/simulate-error` | Trigger lỗi giả lập |
| `GET` | `/api/orders/demo-pii` | Demo PII masking trong log |

### Ví dụ sử dụng

```bash
# Tạo đơn hàng
curl -X POST http://localhost:8080/api/orders \
  -H "Content-Type: application/json" \
  -d '{"customerName": "Nguyen Van A", "items": ["Laptop", "Mouse"], "totalAmount": 25000000}'

# Xử lý đơn hàng
curl -X POST http://localhost:8080/api/orders/{order-id}/process

# Trigger lỗi (để xem trên dashboard)
curl http://localhost:8080/api/orders/simulate-error
```

## 📊 Kibana Dashboards

Sau khi khởi chạy, truy cập [Kibana](http://localhost:5601) → **Dashboard** để xem:

### Dashboard 1: Executive Overview (Lớp 1)
- **KPI Panels**: Total Requests, Error Rate, RPS, Avg Latency
- **RPS Time-series**: Biểu đồ lưu lượng request theo thời gian
- **Latency p95/p99**: Biểu đồ độ trễ phân vị
- **Error Distribution**: Phân bố mã HTTP status

### Dashboard 2: Developer Deep-Dive (Lớp 2)
- **Top 10 Slowest Endpoints**: Bảng API chậm nhất
- **Top 10 Error-Prone Endpoints**: Bảng API lỗi nhiều nhất
- **Error Timeline**: Timeline lỗi theo endpoint
- **Log Stream & Recent Errors**: Xem log chi tiết kèm TraceId để gỡ lỗi

### Dashboard 3: Infrastructure & Runtime (Lớp 3)
- **Memory & CPU**: RAM usage, CPU load của service
- **Garbage Collection (GC)**: GC Pause time, Heap fragmentation
- **ThreadPool**: Starvation, Queue length

### Dashboard 4: QA Compliance Tracker (Lớp 4)
- **Service Registration**: Danh sách các service đã tích hợp SDK
- **Compliance Status**: Đánh giá mức độ tuân thủ tiêu chuẩn Observability
- **Release Gating**: Thông tin hỗ trợ QA quyết định cho phép release hay không
### Tra cứu theo TraceId

1. Vào **Kibana → Discover**
2. Chọn Data View: `traces-*.otel-*` hoặc `logs-*.otel-*`
3. Tìm kiếm: `trace_id: "<your-trace-id>"`

## 🔄 Tích hợp Kafka — Dev đánh dấu log business, Collector route theo topic (SDK v1.6.0)

Theo chuẩn kiến trúc Observability hiện tại, SDK `ISC.Observability` **KHÔNG** tự kết nối/ghi trực tiếp vào Kafka để giữ cho App nhẹ nhất có thể. Việc đẩy message vào Kafka được ủy quyền hoàn toàn cho **OpenTelemetry Collector** — Dev chỉ *đánh dấu ý định* trên log, DevOps mới là bên quyết định cơ chế route thật qua cấu hình Collector.

**Phía Dev** — bọc log cần stream sang Kafka bằng `ISC.Observability.Logging.BusinessLog`, chỉ định luôn tên topic:

```csharp
using ISC.Observability.Logging;

using (BusinessLog.Begin("order-events"))
{
    _logger.LogInformation(
        "Order processed successfully. OrderId: {OrderId}", order.Id);
}
```
Log bên trong scope này tự động có thêm 2 field `log_category=business` và `kafka_topic=order-events` (xem `docs/LOG_RECORD_STRUCTURE_STANDARD.md` §3.5) — Dev không viết bất kỳ dòng code Kafka nào.

**Phía DevOps** — với mỗi topic Dev đã thống nhất dùng, thêm **2 chỗ** trong `otel-collector-config.yml`: (1) 1 filter+exporter+pipeline đẩy log đó sang Kafka, và (2) 1 điều kiện loại trừ trong filter của pipeline `logs` chính để log đó **không còn lên Elasticsearch nữa** (routing loại trừ lẫn nhau — 1 log business chỉ nằm ở đúng 1 nơi: Kafka):

```yaml
processors:
  # Giữ lại các log record khớp topic "order-events" -> đẩy sang Kafka
  filter/topic_order_events:
    error_mode: ignore
    logs:
      log_record:
        - 'attributes["log_category"] != "business" or attributes["kafka_topic"] != "order-events"'

  # Loại các log đã được route sang Kafka ra khỏi pipeline Elasticsearch chính.
  # Điều kiện ở đây phải khớp 1-1 với từng filter/topic_<ten> phía trên — thêm 1 topic mới
  # thì thêm 1 "or (...)" ở đây.
  filter/exclude_kafka_routed:
    error_mode: ignore
    logs:
      log_record:
        - 'attributes["log_category"] == "business" and attributes["kafka_topic"] == "order-events"'

exporters:
  kafka/order_events:
    brokers: ["kafka:9092"]
    topic: "order-events"
    encoding: otlp_json

service:
  pipelines:
    logs:                                    # pipeline chính: loại log đã đi Kafka ra
      receivers: [otlp]
      processors: [filter/exclude_kafka_routed, batch]
      exporters: [otlp/elastic, debug]
    logs/business_order_events:
      receivers: [otlp]
      processors: [filter/topic_order_events, batch]
      exporters: [kafka/order_events]
```

> [!WARNING]
> Không dùng field `topic_from_attribute` của `kafkaexporter` cho nhu cầu này — đã verify thật (otel-collector-contrib `0.114.0`, xem `governance/memory.md` GOT-03) rằng field đó chỉ đọc được **Resource attribute** (cố định theo cả service), không đọc được **log-record attribute** (chính là cách `kafka_topic` của `BusinessLog` hoạt động) — log sẽ âm thầm rơi vào topic fallback mà không có lỗi nào được log ra.

> [!IMPORTANT]
> **Exclusive routing (quyết định có chủ đích):** log business khớp 1 topic đã khai báo sẽ **biến mất khỏi Kibana** — không còn tra cứu được bằng `trace_id` trên Elasticsearch nữa, chỉ còn trong Kafka. Nếu Dev dùng một tên topic mà DevOps **chưa** khai báo route tương ứng (gõ sai tên, hoặc topic mới chưa kịp thêm), log đó **không bị mất** — vẫn lên Elasticsearch bình thường như lưới an toàn, chỉ đơn giản chưa có nhánh Kafka nào nhận. Hệ quả: 1 topic mới = DevOps phải sửa **cả 2 chỗ** (thêm route + thêm điều kiện loại trừ) thì log mới thật sự rời khỏi Kibana; quên sửa chỗ (2) thì log sẽ tạm thời lên **cả 2 nơi** cho tới khi DevOps bổ sung.

## 🏗️ Cấu trúc dự án

```
observability-standard/
├── docs/                            # Tài liệu & Trang chủ GitHub Pages
│   ├── index.html                   # HTML Presentation trực quan
│   ├── ARCHITECTURE_STANDARD.html   # HTML version
│   ├── OBSERVABILITY_STANDARD.html  # HTML version
│   ├── RUNBOOK_TEMPLATE.html        # HTML version
│   └── POLYGLOT_CONTRACT.md         # Quy chuẩn Data cho Đa Ngôn Ngữ (Node, Go...)
├── docker-compose.yml               # Docker Compose orchestration
├── otel-collector-config.yml        # Cấu hình OTel Collector
├── README.md                        # Tài liệu hướng dẫn (file này)
├── kibana/
│   └── dashboards.ndjson            # 4 Kibana dashboards (auto-import)
├── scripts/
│   ├── load-generator.sh            # Script tạo traffic giả lập
│   └── rebuild_dashboards_v2.py     # Script automation khởi tạo/update dashboard
└── src/
    ├── ISC.Observability/           # 📦 SDK DÙNG CHUNG CHO TOÀN BỘ BACKEND
    │   ├── ISC.Observability.csproj
    │   ├── Extensions/ObservabilityExtensions.cs
    │   ├── Middleware/CorrelationIdMiddleware.cs
    │   ├── Middleware/GlobalExceptionMiddleware.cs
    │   └── Telemetry/PiiMaskingEnricher.cs
    └── MvpDemo.Service/             # 🛒 ỨNG DỤNG DEMO (SỬ DỤNG SDK)
        ├── Dockerfile
        ├── Program.cs               # Chỉ cần gọi builder.AddStandardObservability()
        ├── Controllers/
        └── Services/
```

## 🔍 Mapping Spec → Implementation

| Spec Section | Yêu cầu | Implementation |
|---|---|---|
| 2.1 | Structured Logging | Serilog + Message Templates trong mọi file |
| 2.2 | Log Levels | INFO/WARN/ERROR/DEBUG demo trong OrderService |
| 2.3 | Metadata fields | Serilog Enrichers + CorrelationIdMiddleware |
| 2.4 | PII Masking | PiiMaskingEnricher + `/api/orders/demo-pii` |
| 3.1 | RED Pattern | OTel ASP.NET Core auto-instrumentation |
| 3.2 | .NET Runtime Metrics | `OpenTelemetry.Instrumentation.Runtime` |
| 3.3 | Custom Business Metrics | DiagnosticsConfig (Counter, Histogram, UpDownCounter) |
| 4.1 | Context Propagation | OTel SDK + W3C TraceContext tự động |
| 4.2 | Custom Spans | ActivitySource trong OrderService.ProcessOrderAsync |
| 4.3 | Auto-Instrumentation | ASP.NET Core + HttpClient instrumentation |
| 5 | Kibana Dashboards | 2 dashboards auto-imported |

## 🛑 Dừng hệ thống

```bash
# Dừng tất cả services
docker compose --profile load-test down

# Dừng và xóa dữ liệu
docker compose --profile load-test down -v
```

## ⚠️ Lưu ý

- Dự án này chạy với **security disabled** (`xpack.security.enabled=false`), chỉ phù hợp cho môi trường Demo/Dev.
- Dữ liệu đơn hàng lưu **in-memory**, sẽ mất khi restart container app.
- Cần tối thiểu **4GB RAM** cho Docker để chạy Elasticsearch ổn định.

## 🗺️ Roadmap / Next Steps

- [x] Phase 1: Chuẩn hóa Observability cho Backend Microservices (.NET 8).
- [x] Phase 2: Triển khai các Dashboard tiêu chuẩn (Lớp 1, 2, 3, 4).
- [ ] **Phase 3 (Sắp tới): Phát triển Observability Standard cho Frontend (Web/SPA).**
  - Tích hợp RUM (Real User Monitoring).
  - Web Vitals (FCP, LCP, CLS).
  - Trace Context propagation từ Browser đến Backend.
- [ ] **Phase 4 (Sắp tới): Phát triển Observability Standard cho Mobile Apps (iOS/Android).**
  - Crash reporting & Stack traces.
  - Screen rendering metrics.
  - Network request tracing từ Mobile Client.
