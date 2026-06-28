# 🔭 Observability Standard - MVP Demo

> Dự án mẫu chuẩn hóa Observability cho các dịch vụ .NET 8, tuân thủ [Tài liệu Quy định Tiêu chuẩn Observability](./spec.md) và [Tài liệu Tiêu chuẩn Observability Standard cho Dev & SA](./OBSERVABILITY_STANDARD.md).

## 📋 Tổng quan

Dự án này cung cấp:

- **Sample Service (.NET 8)**: Dịch vụ quản lý đơn hàng (Order Management) được tích hợp đầy đủ Logs, Metrics, Traces theo chuẩn Observability.
- **Hạ tầng Docker**: Stack hoàn chỉnh bao gồm OpenTelemetry Collector, Elasticsearch, Kibana — sẵn sàng demo bằng một lệnh duy nhất.
- **Kibana Dashboards**: 2 dashboard được tự động import, hiển thị trạng thái sức khỏe hệ thống và công cụ điều tra lỗi.

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

### Dashboard 1: Executive Overview
- **KPI Panels**: Total Requests, Error Rate, RPS, Avg Latency
- **RPS Time-series**: Biểu đồ lưu lượng request theo thời gian
- **Latency p95/p99**: Biểu đồ độ trễ phân vị
- **Error Distribution**: Phân bố mã HTTP status

### Dashboard 2: Developer Deep-Dive
- **Top 10 Slowest Endpoints**: Bảng API chậm nhất
- **Top 10 Error-Prone Endpoints**: Bảng API lỗi nhiều nhất
- **Error Timeline**: Timeline lỗi theo endpoint
- **Log Stream**: Xem log theo TraceId

### Tra cứu theo TraceId

1. Vào **Kibana → Discover**
2. Chọn Data View: `traces-*.otel-*` hoặc `logs-*.otel-*`
3. Tìm kiếm: `trace_id: "<your-trace-id>"`

## 🔄 Tích hợp Kafka (Dành cho DevOps)

Theo chuẩn kiến trúc Observability hiện tại, SDK `ISC.Observability` **KHÔNG** ghi log trực tiếp vào Kafka để giữ cho App nhẹ nhất có thể. Thay vào đó, việc đồng bộ log/trace sang Kafka được ủy quyền hoàn toàn cho **OpenTelemetry Collector**.

Nếu DevOps muốn xuất log sang hệ thống Kafka có sẵn, chỉ cần cấu hình thêm `kafka exporter` trong file `otel-collector-config.yml`:

```yaml
exporters:
  kafka:
    protocolVersion: 2.0.0
    brokers:
      - kafka-broker1:9092
      - kafka-broker2:9092
    topic: my-observability-logs
    # Tùy chọn cấu hình auth, retry, queue...

service:
  pipelines:
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [elasticsearch, kafka] # Thêm kafka vào đây
```
*(Việc cấu hình này không yêu cầu Dev phải cập nhật Code hay Deploy lại Application)*

## 🏗️ Cấu trúc dự án

```
observability-standard/
├── spec.md                          # Tài liệu tiêu chuẩn Observability
├── docker-compose.yml               # Docker Compose orchestration
├── otel-collector-config.yml        # Cấu hình OTel Collector
├── README.md                        # Tài liệu hướng dẫn (file này)
├── kibana/
│   └── dashboards.ndjson            # Kibana dashboards (auto-import)
├── scripts/
│   └── load-generator.sh            # Script tạo traffic giả lập
└── src/
    └── MvpDemo.Service/
        ├── Dockerfile               # Multi-stage Docker build
        ├── MvpDemo.Service.csproj    # Project file
        ├── Program.cs               # Entry point + OTel setup
        ├── appsettings.json         # Configuration
        ├── appsettings.Demo.json    # Demo environment config
        ├── Controllers/
        │   └── OrdersController.cs   # REST API endpoints
        ├── Middleware/
        │   ├── GlobalExceptionMiddleware.cs
        │   └── CorrelationIdMiddleware.cs
        ├── Models/
        │   └── Order.cs              # Domain model
        ├── Services/
        │   └── OrderService.cs       # Business logic
        └── Telemetry/
            ├── DiagnosticsConfig.cs   # ActivitySource & Meter
            └── PiiMaskingEnricher.cs  # PII masking enricher
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
