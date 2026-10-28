# Quản trị Dự án — MEMORY (Tri Thức & Quyết Định Kiến Trúc)

## 🏛️ 1. Quyết Định Kiến Trúc (Architectural Decision Records - ADR)

### ADR-01: Sử dụng CompositeTextMapPropagator cho Service Mesh
- **Bối cảnh**: Khi request đi qua Istio/Envoy Sidecar Proxy, header B3 (`x-b3-traceid`) được sử dụng. Nếu SDK chỉ hỗ trợ W3C `traceparent` thì luồng trace bị ngắt kết nối.
- **Quyết định**: Khởi tạo `CompositeTextMapPropagator` hỗ trợ đồng thời W3C, B3 (Single & Multi header) và Baggage làm mặc định.
- **Kết quả**: Trace spans liên kết 100% qua Service Mesh.

### ADR-02: Chuyển logic phát Metric Compliance vào IHostedService
- **Bối cảnh**: Gọi `Counter.Add()` trong giai đoạn DI registration trước khi `MeterProvider` hoàn tất build khiến lệnh `Add()` bị no-op.
- **Quyết định**: Đưa logic phát metric `observability.sdk.active` vào `ComplianceMetricsService` triển khai `IHostedService.StartAsync()`.

### ADR-03: Chuyển cổng SigNoz UI sang Port 8090
- **Bối cảnh**: Port `3300` bị chiếm dụng bởi process `wslhost.exe` của cụm Kubernetes Kind local.
- **Quyết định**: Ánh xạ port SigNoz Web UI sang `8090:8080` (`http://localhost:8090`).

### ADR-04: Dev tự đánh dấu log business + chọn topic Kafka, Collector route EXCLUSIVE theo attribute (SDK v1.6.0)
- **Bối cảnh**: Dev cần một số log nghiệp vụ (business event) được stream sang Kafka cho consumer khác dùng — nhưng không muốn Dev code logic Kafka producer trong app (vi phạm §4.4 OBSERVABILITY_STANDARD.md). Quyết định rõ ràng (sau khi hỏi lại): log đã route sang Kafka thì **không còn lên Elasticsearch/Kibana nữa** (exclusive, không phải dual-write) — đổi lấy tiết kiệm storage ES, đánh đổi mất khả năng tra cứu các business event này trên Kibana.
- **Quyết định**: Thêm `ISC.Observability.Logging.BusinessLog.Begin(string kafkaTopic)` — Dev bọc `using (BusinessLog.Begin("order-events")) { _logger.LogInformation(...); }`, SDK chỉ gắn 2 property snake_case `log_category=business` + `kafka_topic=<topic>` vào LogContext (không tự kết nối Kafka). Collector (`otel-collector-config.yml`) dùng **2 filter bổ sung cho nhau** (không phải fan-out): `filter/topic_<ten>` giữ lại log khớp topic đó cho pipeline Kafka riêng; `filter/exclude_kafka_routed` loại đúng các log đó ra khỏi pipeline `logs` chính (ES) — 2 điều kiện phải khớp 1-1, thêm 1 topic mới phải sửa cả 2 chỗ. Demo dùng trong `OrderService.ProcessOrderAsync`.
- **Kết quả**: Đã verify thật end-to-end 2 lần (docker run otel-collector-contrib:0.114.0 trên `obs-network` + curl OTLP/HTTP + `kafka-console-consumer`/`GetOffsetShell` + đếm "log records" qua debug exporter của pipeline ES): (1) log business `kafka_topic=order-events` → lên đúng Kafka, biến mất khỏi pipeline ES; (2) log business với topic chưa khai báo (`payment-events`) → không lọt Kafka, vẫn lên ES bình thường (lưới an toàn, không mất dữ liệu do gõ sai/quên khai báo); (3) log thường không business → chỉ lên ES như cũ. Không crash Collector ở cả 3 trường hợp.

---

## 💡 2. Bài Học Kỹ Thuật (Gotchas)

> [!warning] GOT-01 — PromQL Metric Name Normalization
> Engine PromQL của SigNoz tự động chuyển đổi dấu chấm `.` trong tên metric thành dấu gạch dưới `_`.
> *Ví dụ*: `observability.sdk.active` -> `observability_sdk_active`.

> [!warning] GOT-02 — SigNoz Dashboard Builder v4 Schema
> Khi cấu hình Panel bằng Query Builder v4, thuộc tính `aggregateAttribute.key` phải trỏ đúng tên metric `observability.sdk.active` kèm `isColumn: true`.

> [!warning] GOT-03 — kafkaexporter `topic_from_attribute` chỉ đọc RESOURCE attribute, không đọc log-record attribute
> Đã verify thật (otel-collector-contrib:0.114.0): cấu hình `topic_from_attribute: "kafka_topic"` trên `kafkaexporter` cho signal **logs** CHỈ route đúng topic khi `kafka_topic` là **Resource attribute** (cố định theo cả process). Đặt `kafka_topic` làm log-record attribute (chính là cách `Serilog.Context.LogContext.PushProperty` + `.Enrich.FromLogContext()` đang hoạt động trong SDK) bị **bỏ qua âm thầm** — log rơi vào `topic` fallback, không có log lỗi nào cả. Vì Resource không đổi được theo từng dòng log, nhu cầu "mỗi log event tự chọn 1 Kafka topic khác nhau" (ADR-04) **không dùng được** `topic_from_attribute`. Giải pháp: dùng `filterprocessor` ở `log_record` context (đã verify đọc đúng log-record attribute) để lọc theo từng topic, mỗi topic 1 pipeline + 1 `kafkaexporter` tĩnh riêng.

---

## 📦 3. Nhật Ký Phiên Bản SDK (SDK Version Registry)
- **v1.3.0 & v1.3.1**: Sửa lỗi `Counter.Add()` no-op qua `ComplianceMetricsService`.
- **v1.3.2**: Hỗ trợ B3 Propagator cho Envoy Mesh & wildcard `tracing.AddSource("*")`. Published trên NuGet.org.
- **v1.6.0**: Thêm `ISC.Observability.Logging.BusinessLog` — Dev đánh dấu log business + chọn topic Kafka đích, Collector route theo attribute (ADR-04).
