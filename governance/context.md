# Quản trị Dự án — CONTEXT (Bối Cảnh & Định Hướng)

## 📌 1. Mục Tiêu Dự Án (Project Objectives)
Dự án **Observability Standard** được thiết lập nhằm xây dựng bộ tiêu chuẩn giám sát toàn diện cho toàn bộ hệ thống Microservices trong tổ chức theo 3 trục dữ liệu chính:
- **Logging**: Log cấu trúc JSON (Serilog), tự động mã hóa PII, đính kèm TraceId/SpanId.
- **Tracing**: Phân vết phân tán (Distributed Tracing) toàn luồng request từ Gateway qua Service Mesh đến Backend Services và Database.
- **Metrics**: Thu thập chỉ số đo lường hiệu năng (RPS, Latency, Error Rate) và chỉ số tuân thủ SDK (`observability.sdk.active`).

---

## 📐 2. Phân Chia Trách Nhiệm (Dev vs DevOps Domain)

### 🛠️ Developer (Dev Domain)
- Tích hợp NuGet Package SDK `ISC.Observability`.
- Gọi lệnh đăng ký chuẩn: `builder.AddStandardObservability()` và `app.UseStandardObservability()`.
- Ghi log theo đúng định dạng JSON và đính kèm `LogContext`.
- Không cần bận tâm đến hạ tầng ClickHouse, Kibana hay OTel Collector.

### ⚙️ DevOps / SRE (DevOps Domain)
- Triển khai và vận hành OpenTelemetry Collector (Contrib).
- Quản lý hạ tầng lưu trữ backend (ClickHouse, SigNoz UI).
- Thiết lập quy trình batching, memory limiting và data retention.
- Không cần can thiệp vào mã nguồn .NET của ứng dụng.

---

## 🏗️ 3. Kiến Trúc Kỹ Thuật (Technical Architecture)
```
[ Applications (.NET 8) ] ──► [ ISC.Observability SDK ]
                                        │
                                        ├─► OTLP gRPC (Port 4317)
                                        └─► OTLP HTTP (Port 4318)
                                                │
                                                ▼
                                    [ SigNoz OTel Collector ]
                                                │
                                                ▼
                                    [ ClickHouse Storage ]
                                                │
                                                ▼
                                    [ SigNoz Dashboard UI ] (Port 8090)
```
