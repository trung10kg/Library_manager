# Library System

Backend cho **hệ thống quản lý thư viện**: quản lý đầu sách và bản sao, bạn đọc
và thẻ thư viện, mượn – trả – gia hạn – đặt chỗ, tiền phạt. Dự án chỉ gồm
database và REST API, không có giao diện.

## Vai trò

| Vai trò | Làm được gì |
|---|---|
| `ADMIN` | Quản trị tài khoản, phân quyền, mọi việc của thủ thư |
| `LIBRARIAN` | Quản lý sách, bạn đọc, cho mượn / nhận trả, xử lý phạt |
| `READER` | Xem sách, xem phiếu mượn và khoản phạt của chính mình |

## Kiến trúc

Năm microservice FastAPI, đi chung một cổng Nginx:

| Service | Phụ trách |
|---|---|
| `auth-service` | Đăng nhập, JWT, tài khoản và phân quyền |
| `catalog-service` | Sách, tác giả, danh mục, kệ, bản sao |
| `reader-service` | Bạn đọc, thẻ thư viện, xuất thẻ PDF |
| `circulation-service` | Mượn, trả, gia hạn, đặt chỗ, báo cáo quá hạn |
| `billing-service` | Tiền phạt và thanh toán |

Công nghệ: Python 3.12 · FastAPI · SQLAlchemy 2.0 async · MySQL 8 ·
JWT RS256 · RabbitMQ · Docker Compose · pytest.

## Tiến độ

- [x] Phase 1 – Khung monorepo, thư viện dùng chung, gateway
- [x] Phase 2 – auth-service: đăng nhập, refresh token xoay vòng, quản trị tài khoản
- [ ] Phase 3 – catalog-service, reader-service
- [ ] Phase 4 – circulation, billing, flow mượn – trả, event
- [ ] Phase 5 – Báo cáo quá hạn, test end-to-end

## Chạy thử

```bash
python task.py setup && python task.py keys
python task.py db-migrate && python task.py seed
python task.py dev          # API tại http://localhost:8000/docs
```

Cần Python 3.12, Docker Desktop và MySQL 8 cài trên máy. Thư mục schema `db/`
không nằm trong repo.

Hướng dẫn chi tiết (cài đặt, tài khoản dev, danh sách API, lệnh, quy ước code):
**[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)**.
