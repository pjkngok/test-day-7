---
name: lead_scoring_skill
description: Kỹ năng chấm điểm khách hàng tiềm năng dựa trên mô tả nhu cầu bất động sản.
---

# Lead Scoring Skill (Bất Động Sản)

Kỹ năng này giúp AI phân tích `nhu_cau_mo_ta` từ dữ liệu khách hàng để chấm điểm tiềm năng.

## 1. Quy tắc chấm điểm

### A. Nhóm Siêu Tiềm Năng (Cộng 50 điểm)
Cộng điểm nếu nội dung chứa các dấu hiệu sau:
- **Ngân sách:** >= 20 tỷ, "tài chính mạnh", "không thành vấn đề".
- **Loại hình:** "Biệt thự đơn lập", "Penthouse", "Shophouse mặt đường lớn", "Quỹ đất công nghiệp", "Sàn văn phòng diện tích lớn".
- **Vị trí:** "Quận 1", "Ven sông", "Vinhomes Ocean Park", "Phú Mỹ Hưng".
- **Đối tượng:** "Chủ doanh nghiệp", "Nhà đầu tư chuyên nghiệp", "Mua sỉ", "Mua số lượng lớn".
- **Pháp lý/Cấp thiết:** "Pháp lý chuẩn 100%", "Sổ hồng riêng", "Gặp trực tiếp chủ đầu tư".

### B. Nhóm Rác/Không Tiềm Năng (Trừ 50 điểm)
Trừ điểm nếu nội dung chứa các dấu hiệu sau:
- **Phi thực tế:** Giá quá rẻ so với khu vực (VD: Q1 giá 1-2 tỷ).
- **Không nhu cầu:** "Nhầm số", "Dữ liệu cũ", "Nhầm ngành".
- **Thiếu thiện chí:** "Hỏi cho vui", "Chưa định mua", "Không hợp tác".
- **Spam:** "Bảo hiểm", "Vay vốn", "Mời chào dịch vụ".
- **Lỗi liên lạc:** "Thuê bao", "Không nghe máy", "Không rep Zalo".

### C. Nhóm Tiềm Năng Trung Bình (0 - 10 điểm)
- Mua chung cư, nhà phố 3-10 tỷ.
- Cần vay ngân hàng.
- Cần tư vấn thêm pháp lý/vị trí.

## 2. Cấu trúc dữ liệu đầu vào
Hệ thống sẽ cung cấp dữ liệu từ Google Sheets với các cột:
- `id`: Mã khách hàng.
- `ten_khach`: Tên khách hàng.
- `sdt`: Số điện thoại.
- `nhu_cau_mo_ta`: Nội dung mô tả nhu cầu (Cần phân tích chính).

## 3. Output mong đợi
AI trả về kết quả dưới dạng JSON:
```json
{
  "id": "string",
  "score": number,
  "reason": "string (Giải thích ngắn gọn lý do chấm điểm)",
  "classification": "VIP | Tiềm năng | Trung bình | Rác"
}
```
