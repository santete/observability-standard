# 📖 Mẫu Quy Trình Vận Hành & Xử Lý Sự Cố (SOP & Runbook Template)

> [!NOTE]
> **Mục đích:** Tài liệu này kết hợp cả **Runbook** (Cách xử lý sự cố khẩn cấp) và **SOP** (Quy trình vận hành tiêu chuẩn hàng ngày). Yêu cầu viết ngắn gọn, tập trung vào hành động (Action-oriented), copy-paste lệnh chạy được ngay.

## 1. Thông Tin Dịch Vụ (Service Metadata)
- **Tên Service:** `[Tên Microservice - VD: MvpDemo.OrderService]`
- **Team Sở Hữu (Owner):** `[Tên Team - VD: Checkout Team]`
- **Kênh Cảnh Báo (Slack/Teams):** `[#alert-checkout-team]`
- **Người Trực Vận Hành (On-call):** `[Link tới PagerDuty hoặc danh sách sdt]`

---

## 2. Quy Trình Vận Hành Tiêu Chuẩn (SOP - Hàng ngày/Chủ động)
*Dành cho các tác vụ thay đổi, bảo trì hệ thống (Planned Actions).*

### 2.1. Triển khai (Deploy) & Khôi phục (Rollback)
- **Deploy:** Chạy Pipeline `Deploy-Prod` trên [GitLab CI / Jenkins].
- **Rollback:** Trong trường hợp khẩn cấp, chạy Pipeline `Rollback-Prod` và điền số version an toàn trước đó.

### 2.2. Tăng/Giảm Tài Nguyên (Scaling)
- **Lệnh tăng Replicas thủ công:** `kubectl scale deployment <tên-service> --replicas=5 -n prod`

### 2.3. Cập Nhật Cấu Hình (Config)
- Thay đổi cấu hình tại repo GitOps, tạo Pull Request.
- Cấu hình sẽ được ArgoCD tự động apply trong vòng 3 phút sau khi Merge PR.

---

## 3. Danh Sách Cảnh Báo & Xử Lý Sự Cố (Runbook - Phản ứng)
*Dành cho xử lý khi nhận được tin nhắn Alert đỏ lòm giữa đêm (Reactive Actions).*

### 🚨 Cảnh Báo 1: Tỉ Lệ Lỗi 5xx Tăng Đột Biến (High Error Rate)
- **Kích hoạt khi:** Tỉ lệ lỗi HTTP 5xx vượt quá **1%** trong 5 phút.
- **Mức độ (Severity):** `SEV-1` (Nghiêm trọng - Cần xử lý ngay).
- **Tác động (Impact):** Khách hàng không thể tạo đơn hàng, thất thoát doanh thu trực tiếp.

#### 🔍 Bước 1: Điều Tra (Investigation)
1. Mở **[Developer Deep-Dive Dashboard](#)** trên Kibana.
2. Kiểm tra biểu đồ **Top 10 Error-Prone Endpoints** để xem API nào đang lỗi.
3. Click vào biểu đồ để copy `TraceId`.
4. Dán `TraceId` vào khung search để xem chi tiết StackTrace:
   - *Lỗi do DB?* -> Kiểm tra xem DB có đang quá tải hay kẹt lock.
   - *Lỗi do Timeout API bên thứ 3?* -> Chuyển sang Bước 2.

#### 🛠️ Bước 2: Khắc Phục Tạm Thời (Mitigation)
*Chỉ chọn 1 phương án phù hợp để cầm máu nhanh nhất:*
- **Phương án A (Rollback):** Nếu vừa Release version mới trong vòng 1 tiếng, lập tức Rollback về version cũ theo bước [2.1](#21-triển-khai-deploy--khôi-phục-rollback).
- **Phương án B (Circuit Breaker):** Kích hoạt chặn luồng (Force Circuit Breaker Open) để không làm treo toàn bộ app.

#### 📞 Bước 3: Leo Thang (Escalation)
- Nếu sau 15 phút vẫn không tìm ra nguyên nhân: Gọi số Hotline của **Data/DBA Team** hoặc **Platform Team**.

---

### ⚠️ Cảnh Báo 2: CPU/RAM Tiêu Thụ Chạm Ngưỡng (Resource Exhaustion)
- **Kích hoạt khi:** CPU hoặc RAM của Pod vượt ngưỡng **85%** trong 10 phút.
- **Mức độ (Severity):** `SEV-2` (Cảnh báo - Hệ thống bị chậm nhưng chưa sập).

#### 🔍 Bước 1: Điều Tra
1. Mở **[Infrastructure Dashboard](#)**.
2. Kiểm tra biểu đồ **Memory/CPU Usage**:
   - Nếu RAM tăng bậc thang (Memory Leak) -> Báo Dev chuẩn bị fix bug.
   - Nếu CPU tăng vọt cùng RPS -> Quá tải tự nhiên.

#### 🛠️ Bước 2: Khắc Phục Tạm Thời
- Scale out thủ công lên 5 Pods theo hướng dẫn ở bước [2.2](#22-tănggiảm-tài-nguyên-scaling).
- Nếu RAM đầy, chủ động Restart Pod thủ công để giải phóng RAM tạm thời.

---

## 4. Quy Trình Sau Sự Cố (Post-Incident)
- Bất kỳ sự cố `SEV-1` nào xảy ra đều **bắt buộc** phải tổ chức họp Post-Mortem trong vòng 48h.
- Cập nhật lại chính tài liệu này nếu các bước xử lý trên bị thiếu hoặc sai.

> [!TIP]
> **Quy tắc vàng:** Sửa lỗi là việc của ngày mai. Việc của người trực On-call đêm nay là "Cầm máu" và đưa hệ thống hoạt động trở lại nhanh nhất có thể (Bằng cách Rollback, Restart, hoặc Scale up).
