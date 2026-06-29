# 📜 Polyglot Observability Contract (Hợp Đồng Giám Sát Đa Ngôn Ngữ)

Tài liệu này định nghĩa **"Luật chơi chung" (Standard Conventions)** bắt buộc cho tất cả các Microservices trong hệ thống, bất kể được viết bằng ngôn ngữ nào (.NET, Node.js, Golang, PHP, Java...).

Mục tiêu là đảm bảo mọi Service đều sinh ra dữ liệu (Logs, Traces, Metrics) có cùng một định dạng chuẩn (JSON/OTLP), giúp các hệ thống lưu trữ và hiển thị (Kibana, SigNoz) có thể truy vấn và phân tích trơn tru mà không bị phân mảnh dữ liệu.

---

## 1. Nguyên Tắc Cốt Lõi (Core Principles)

1. **Giao thức duy nhất:** Toàn bộ dữ liệu Observability phải được xuất qua giao thức **OTLP (OpenTelemetry Protocol)**.
2. **Không ghi ra file vật lý:** Ứng dụng không được phép cấu hình ghi log ra file `.txt` hoặc `.log` trên ổ cứng server. Mọi thứ phải được truyền trực tiếp qua mạng (gRPC/HTTP) tới OTel Collector.
3. **Không ghi trực tiếp vào DB/Kafka:** Ứng dụng không tự ý đẩy log vào Kafka hay Elasticsearch. OTel Collector sẽ làm nhiệm vụ định tuyến này.

---

## 2. Chuẩn Nối Chuỗi (Context Propagation)

Để hệ thống vẽ được một Trace đi qua nhiều Services khác nhau (VD: Web App -> Node.js API -> Golang gRPC -> DB), các ngôn ngữ **bắt buộc** tuân thủ chuẩn **W3C Trace Context**.

* **Yêu cầu:** Bất kỳ khi nào Service A gọi mạng (HTTP/gRPC) sang Service B, nó phải chèn thêm HTTP Header: `traceparent`.
* **Ví dụ Header:** `traceparent: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01`
* Hầu hết các thư viện OpenTelemetry SDK chính chủ của các ngôn ngữ đều tự động làm việc này nếu được cấu hình đúng.

---

## 3. Quy Chuẩn Đặt Tên Trường Dữ Liệu (Semantic Conventions)

Mọi JSON payload gửi lên (qua Log hoặc Trace Span) **TUYỆT ĐỐI KHÔNG TỰ CHẾ TÊN BIẾN** (Ví dụ: cấm dùng `appName`, `StatusCode`, `ReqUrl`). Phải sử dụng bộ từ điển chuẩn của OpenTelemetry dưới đây:

### 3.1. Các trường định danh dịch vụ (Resource Attributes)
*Bắt buộc phải khai báo lúc khởi tạo SDK, sẽ đính kèm vào mọi Log/Trace/Metric.*

| Trường Chuẩn (Key) | Kiểu | Bắt buộc? | Mô tả & Ví dụ |
| :--- | :--- | :---: | :--- |
| `service.name` | string | **CÓ** | Tên định danh của service. Khuyến nghị viết thường, dùng dấu gạch ngang. VD: `payment-gateway`, `order-worker` |
| `service.version` | string | **CÓ** | Phiên bản đang deploy (Git Hash hoặc SemVer). VD: `v1.2.3` |
| `deployment.environment` | string | **CÓ** | Môi trường chạy thực tế. Chấp nhận các giá trị: `dev`, `staging`, `production` |
| `host.name` | string | Không | Tên server hoặc Pod ID trên Kubernetes. VD: `pod-xyz-123` |

### 3.2. Các trường dành cho HTTP Requests (Span/Log Attributes)
*Bắt buộc có khi ghi log hoặc tạo Trace liên quan đến gọi API.*

| Trường Chuẩn (Key) | Kiểu | Bắt buộc? | Mô tả & Ví dụ |
| :--- | :--- | :---: | :--- |
| `http.request.method` | string | **CÓ** | Động từ HTTP viết HOA. VD: `GET`, `POST` |
| `url.path` | string | **CÓ** | Đường dẫn API được gọi. VD: `/api/v1/users/123` |
| `http.response.status_code` | int | **CÓ** | Mã lỗi HTTP trả về. VD: `200`, `500` |
| `client.address` | string | Không | IP của người gọi (Client IP). VD: `192.168.1.1` |
| `user_agent.original` | string | Không | Thông tin trình duyệt/App của client. |

### 3.3. Các trường dành cho Database (SQL/NoSQL)
*Khi truy vấn DB, phải sinh ra các thông tin này để đo độ trễ câu Query.*

| Trường Chuẩn (Key) | Kiểu | Bắt buộc? | Mô tả & Ví dụ |
| :--- | :--- | :---: | :--- |
| `db.system` | string | **CÓ** | Tên hệ quản trị CSDL. VD: `mysql`, `postgresql`, `mongodb`, `redis` |
| `db.statement` | string | Không | Nguyên văn câu lệnh Query (Nên cẩn thận không log dữ liệu nhạy cảm). VD: `SELECT * FROM users WHERE id = ?` |
| `db.operation` | string | Không | Thao tác chính. VD: `SELECT`, `INSERT` |

---

## 4. Chuẩn Cấu Trúc Dữ Liệu Log (JSON Log Format)

Dù bác code bằng Node.js hay Golang, khi đẩy log qua OTLP, cấu trúc JSON bên dưới phải đảm bảo có đủ các thành phần cơ bản (thường SDK sẽ tự lo việc map này, nhưng Dev cần hiểu cấu trúc):

```json
{
  "Timestamp": "2026-06-29T19:45:00.1234567Z",
  "SeverityText": "INFO", 
  "SeverityNumber": 9,
  "TraceId": "0af7651916cd43dd8448eb211c80319c",
  "SpanId": "b7ad6b7169203331",
  "Body": "User 999 vừa tạo đơn hàng thành công.",
  "Resource": {
    "service.name": "order-api",
    "deployment.environment": "production"
  },
  "Attributes": {
    "http.response.status_code": 200,
    "url.path": "/api/orders",
    "business.order_id": "ORD-555" // Có thể thêm các field nghiệp vụ tự do bắt đầu bằng tiền tố business.*
  }
}
```
*(Quy định: Các field nghiệp vụ riêng của team tự chế nên có prefix như `app.*` hoặc `business.*` để không đụng hàng với chuẩn của OpenTelemetry).*

---

## 5. Quy Chế Lọc Nhiễu (Log Level Noise Reduction)

Để hệ thống không bị "rác" log, làm nghẽn băng thông và tốn tiền lưu trữ, MỌI NGÔN NGỮ phải cấu hình bộ lọc Log Level tại App:

1. **Tầng Framework/Thư viện (Third-party):** Bắt buộc cấu hình Minimum Log Level là `WARNING` hoặc `ERROR`. (Ví dụ: Cấm Express.js, Spring Boot, Gin tự động log "Routing match" hay "Ping DB" ở mức INFO).
2. **Tầng Application (Code do Dev nhà viết):** Cho phép cấu hình Minimum Log Level là `INFO`.
3. **Môi trường Production:** Tuyệt đối KHÔNG ĐƯỢC bật mức log `DEBUG` hoặc `TRACE`.

---

## 6. Quy Chế Bảo Mật & Ẩn Danh (PII Masking)

Các team Dev phải tự triển khai một lớp Middleware hoặc Log Formatter/Filter để **chủ động làm mờ (Mask) dữ liệu nhạy cảm** trước khi đẩy log vào hệ thống Observability.

**Danh sách bắt buộc phải Mask (thay bằng `***` hoặc `[REDACTED]`):**
* Mật khẩu (Passwords, Tokens, API Keys, Bearer auth)
* Số điện thoại (`090****123`)
* Email (`nguyen***@gmail.com`)
* Số thẻ tín dụng, CCCD/CMND.

*Chế tài:* Bất kỳ service nào đẩy lộ lọt thông tin khách hàng (Clear text) lên hệ thống Log tập trung sẽ bị đánh dấu vi phạm Compliance nghiêm trọng.
