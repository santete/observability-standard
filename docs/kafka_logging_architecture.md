# So Sánh Kiến Trúc Log: Đẩy Log Trực Tiếp Vào Kafka vs OpenTelemetry Collector

Tài liệu này giải thích lý do tại sao việc cấu hình Sink trực tiếp ra Kafka từ bên trong App lại bị coi là "Vi phạm kiến trúc" (Anti-pattern), và tại sao cụm **Kafka + Elasticsearch** lại là bắt buộc đối với hệ thống High-Load thay vì chỉ cắm thẳng vào Elasticsearch.

---

## 1. Mô Hình 1: Đẩy Log Trực Tiếp Vào Kafka (Anti-pattern)

Trong mô hình này, Dev cài đặt thư viện Kafka Sink trực tiếp vào ứng dụng (VD: `Serilog.Sinks.Kafka`).

```mermaid
graph TD
    subgraph Microservice [App (C# / .NET)]
        BL[Business Logic]
        subgraph Serilog
            SK[Kafka Sink]
        end
        BL --> Serilog
    end

    subgraph Infrastructure [Hạ tầng]
        Kafka[Kafka Cluster]
        ES[(Elasticsearch)]
    end

    SK == "TCP" ==> Kafka
    Kafka ==> ES
    
    style Microservice fill:#f9f2f4,stroke:#d9534f
    style SK fill:#d9534f,color:#fff
```

### ❌ Tác hại nghiêm trọng:
1. **Phình to ứng dụng (Dependency Bloat):** App cõng thêm toàn bộ driver Kafka (quản lý connection pool, TCP socket, buffer, retry policy).
2. **Cạnh tranh tài nguyên:** Việc serialize log và giao tiếp Kafka tranh giành trực tiếp CPU và RAM với chức năng nghiệp vụ cốt lõi.
3. **Hiệu ứng Domino (Cascading Failures):** Nếu Kafka sập hoặc nghẽn, bộ đệm trong App sẽ phình to gây **Out of Memory (OOM)**, kéo sập toàn bộ ứng dụng chỉ vì tính năng ghi log.
4. **Trói buộc công nghệ (Vendor Lock-in):** Khó thay đổi hệ thống đích (như đổi sang Kinesis hay S3) mà không sửa code.

---

## 2. Mô Hình 2: Tiêu Chuẩn OTLP qua OTel Collector (Best Practice)

Trong mô hình này, App không biết Kafka hay Elasticsearch là gì. Nó chỉ đẩy log qua giao thức OpenTelemetry (OTLP) tới Collector cục bộ.

```mermaid
graph TD
    subgraph Microservice [App (C# / .NET)]
        BL[Business Logic]
        subgraph Serilog
            OTLP[OTLP Sink]
        end
        BL --> Serilog
    end

    subgraph Sidecar_Daemonset [Hạ tầng cục bộ]
        Collector((OTel Collector))
    end

    subgraph Infrastructure [Hạ tầng trung tâm]
        Kafka[Kafka Cluster]
        ES[(Elasticsearch)]
        Metrics[(Prometheus)]
    end

    OTLP == "gRPC" ==> Collector
    
    Collector == "Export Kafka" ==> Kafka
    Collector -. "Export ES" .-> ES
    Collector -. "Export Metrics" .-> Metrics
    
    Kafka ==> ES
    
    style Microservice fill:#dff0d8,stroke:#5cb85c
    style OTLP fill:#5cb85c,color:#fff
    style Collector fill:#f0ad4e,color:#fff,stroke:#eea236
```

### ✅ Lợi ích:
1. **Offloading hoàn hảo:** OTel Collector (viết bằng Go) nhận trách nhiệm nặng nề nhất (Nén, batching, retry). App .NET nhẹ bẫng.
2. **Tách biệt rủi ro (Fault Isolation):** Nếu Kafka sập, OTel Collector sẽ chịu trận và đệm log ra ổ cứng. Chức năng của App không bị ảnh hưởng.
3. **Kiểm soát luồng dữ liệu:** DevOps có thể cấu hình trích xuất log/metrics/traces ra nhiều hệ thống khác nhau thông qua Collector mà không cần sửa code C#.

---

## 3. Tại Sao Phải Có Kafka Đứng Trước Elasticsearch?

Nhiều người thắc mắc: **"Đằng nào cũng vào Elasticsearch (ES), cắm thẳng vào cho lẹ, qua Kafka làm gì?"**

Đối với hệ thống Enterprise / High-Load, đây là 3 lý do bắt buộc:

1. **Cái "Lò xo giảm xóc" (Shock Absorber):** 
   ES là công cụ tìm kiếm, rất dở trong việc chịu tải Ghi (Write Spikes). Nếu hệ thống bị lỗi Infinite Loop bắn ra hàng triệu dòng stack trace, cắm thẳng vào ES sẽ làm sập ES (429 Too Many Requests / OOM). Kafka được thiết kế để hứng chịu hàng chục triệu sự kiện mỗi giây (Sequential I/O). Nó sẽ "ngậm" tải và nhả từ từ cho ES xử lý, bảo vệ cụm ES.
2. **Không Bao Giờ Mất Log (Zero Data Loss):**
   Khi ES phải bảo trì hoặc nâng cấp, nếu cắm thẳng, log trong thời gian đó sẽ bay màu. Nếu có Kafka, log sẽ nằm yên ở ổ cứng Kafka. Khi ES sống lại, nó sẽ tự động chạy ra đọc bù (Offset resume).
3. **Chia Sẻ Dữ Liệu (Multi-destination Fan-out):**
   Nếu chỉ có ES, dữ liệu bị nhốt trong ES. Nếu có Kafka, log có thể được cung cấp đồng thời cho ES (để search), cho S3 / Hadoop (Data Lake lưu trữ dài hạn kiểm toán), và cho Apache Flink (phân tích gian lận thời gian thực) mà không ảnh hưởng lẫn nhau.
