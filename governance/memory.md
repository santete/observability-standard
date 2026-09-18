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

---

## 💡 2. Bài Học Kỹ Thuật (Gotchas)

> [!warning] GOT-01 — PromQL Metric Name Normalization
> Engine PromQL của SigNoz tự động chuyển đổi dấu chấm `.` trong tên metric thành dấu gạch dưới `_`.
> *Ví dụ*: `observability.sdk.active` -> `observability_sdk_active`.

> [!warning] GOT-02 — SigNoz Dashboard Builder v4 Schema
> Khi cấu hình Panel bằng Query Builder v4, thuộc tính `aggregateAttribute.key` phải trỏ đúng tên metric `observability.sdk.active` kèm `isColumn: true`.

---

## 📦 3. Nhật Ký Phiên Bản SDK (SDK Version Registry)
- **v1.3.0 & v1.3.1**: Sửa lỗi `Counter.Add()` no-op qua `ComplianceMetricsService`.
- **v1.3.2**: Hỗ trợ B3 Propagator cho Envoy Mesh & wildcard `tracing.AddSource("*")`. Published trên NuGet.org.
