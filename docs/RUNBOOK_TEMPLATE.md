# 📖 Mẫu Sổ Tay Xử Lý Sự Cố (Runbook Template)

> [!NOTE]
> **Mục đích:** Tài liệu này cung cấp các bước "cầm tay chỉ việc" để xử lý sự cố nhanh chóng. Yêu cầu viết ngắn gọn, tập trung vào hành động (Action-oriented), không giải thích lý thuyết dài dòng.

## 1. Thông Tin Dịch Vụ (Service Metadata)
- **Tên Service:** `[Tên Microservice - VD: MvpDemo.OrderService]`
- **Team Sở Hữu (Owner):** `[Tên Team - VD: Checkout Team]`
- **Kênh Cảnh Báo (Slack/Teams):** `[#alert-checkout-team]`
- **Người Trực Vận Hành (On-call):** `[Link tới PagerDuty hoặc danh sách sdt]`

---

## 2. Danh Sách Cảnh Báo & Cách Xử Lý (Alerts & Mitigation)

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
- **Phương án A (Rollback):** Nếu vừa Release version mới trong vòng 1 tiếng, lập tức Rollback về version cũ qua CI/CD pipeline.
- **Phương án B (Circuit Breaker):** Nếu API bên thứ 3 (ví dụ Cổng thanh toán) bị sập, kích hoạt cấu hình chặn luồng (Force Circuit Breaker Open) để không làm treo toàn bộ app.

#### 📞 Bước 3: Leo Thang (Escalation)
- Nếu sau 15 phút vẫn không tìm ra nguyên nhân hoặc không thể khắc phục: Bấm gọi số Hotline của **Data/DBA Team** hoặc **Platform Team**.

---

### ⚠️ Cảnh Báo 2: CPU/RAM Tiêu Thụ Chạm Ngưỡng (Resource Exhaustion)
- **Kích hoạt khi:** CPU hoặc RAM của Pod vượt ngưỡng **85%** trong 10 phút.
- **Mức độ (Severity):** `SEV-2` (Cảnh báo - Hệ thống bị chậm nhưng chưa sập).

#### 🔍 Bước 1: Điều Tra
1. Mở **[Infrastructure Dashboard](#)**.
2. Kiểm tra biểu đồ **Memory/CPU Usage**:
   - Nếu RAM tăng bậc thang (Memory Leak) -> Báo Dev chuẩn bị fix bug rò rỉ.
   - Nếu CPU tăng vọt cùng với chỉ số RPS (Traffic tăng) -> Đơn giản là quá tải tự nhiên.

#### 🛠️ Bước 2: Khắc Phục Tạm Thời
- Vào Kubernetes/Rancher, tăng số lượng Replica (Scale Out) từ `3` lên `5` Pods.
- Nếu RAM đầy, chủ động Restart Pod thủ công để giải phóng RAM tạm thời.

---

## 3. Quy Trình Sau Sự Cố (Post-Incident)
- Bất kỳ sự cố `SEV-1` nào xảy ra đều **bắt buộc** phải tổ chức họp Post-Mortem (Mổ xẻ sự cố) trong vòng 48h.
- Cập nhật lại chính tài liệu Runbook này nếu các bước xử lý trên bị thiếu hoặc sai.

> [!TIP]
> **Quy tắc vàng:** Sửa lỗi là việc của ngày mai. Việc của người trực On-call đêm nay là "Cầm máu" và đưa hệ thống hoạt động trở lại nhanh nhất có thể (Bằng cách Rollback, Restart, hoặc Scale up).
