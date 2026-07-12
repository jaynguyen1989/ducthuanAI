# Thuận AI All-in-One — Không cần Tavily

Website gồm:
- `/content`: Xưởng Content
- `/chat`: Chat AI bằng Claude
- `/`: Trang chọn công cụ
- `/health`: Kiểm tra hệ thống

## Biến môi trường duy nhất trên Vercel
- `ANTHROPIC_API_KEY`: bắt buộc

Không cần `TAVILY_API_KEY`.
Tính năng tìm kiếm Internet đã được tắt; chat và tạo content vẫn hoạt động bình thường.

Upload toàn bộ nội dung thư mục này lên thư mục gốc GitHub, rồi Redeploy trên Vercel.
