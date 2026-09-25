# Hướng dẫn phát triển — Library System

Backend quản lý thư viện: 5 service FastAPI, đăng nhập JWT RS256, event qua
RabbitMQ. Chỉ có database và REST API, không có giao diện.

Ba vai trò: `ADMIN`, `LIBRARIAN` (thủ thư), `READER` (bạn đọc).

> Đã xong **Phase 2**: auth-service đầy đủ (đăng nhập, refresh token xoay
> vòng, quản trị tài khoản). Catalog, reader, circulation, billing mới có
> `/health` — nghiệp vụ đến ở Phase 3–4.

## Cần có sẵn

| | |
|---|---|
| Python 3.12 | `python --version` |
| Docker Desktop | dùng cho RabbitMQ và gateway |
| MySQL 8.0.16+ | **cài trên máy, không chạy trong Docker**, đã có `library_db` |
| Client `mysql` | trong PATH, hoặc ở `C:\Program Files\MySQL\MySQL Server 8.0\bin` |

MySQL phải từ 8.0.16 trở lên thì `CHECK` constraint mới được thực thi.

> **Thư mục `db/` không nằm trong repo** (đã đưa vào `.gitignore`). Clone về
> xong, xin file schema/migration từ người quản lý dự án và chép vào `db/` ở
> thư mục gốc. Thiếu `db/` thì `db-reset`, `db-migrate`, `seed`, `db-verify`
> và các test cần MySQL đều không chạy được.

## Chạy lần đầu

```bash
python task.py setup       # tạo .venv, cài dependency, tạo .env
python task.py keys        # sinh cặp RSA cho JWT vào keys/
python task.py db-migrate  # áp migration db/06+ vào library_db (tự backup trước)
python task.py seed        # đặt mật khẩu dev cho user mẫu
python task.py dev         # chạy tất cả
```

Sửa `.env` nếu MySQL của bạn không phải `root/1234` ở `127.0.0.1:3306`.

### Tài khoản dev (sau `seed`)

| Username | Mật khẩu | Vai trò |
|---|---|---|
| `admin` | `SEED_ADMIN_PASSWORD` trong `.env` (mặc định `Admin@12345`) | ADMIN |
| `thuthu01`, `thuthu02` | `SEED_DEFAULT_PASSWORD` (mặc định `Thuvien@123`) | LIBRARIAN |
| `docgia01` … `docgia10` | `SEED_DEFAULT_PASSWORD` | READER, có `reader_id` |

`seed` chỉ đụng tới user còn giữ chuỗi hash giả của `db/04_seed.sql`, nên
chạy lại không ghi đè mật khẩu ai đã đổi.

Sau `dev`, mọi API đi qua một cổng: http://localhost:8000. Kiểm tra bằng
`python task.py smoke` ở một cửa sổ khác.

**Danh sách toàn bộ API: http://localhost:8000/docs** — một trang Swagger gộp
cả 5 service, nhóm theo service. Service nào chưa chạy thì trang vẫn mở và
báo ở đầu trang. Docs riêng từng service vẫn ở `<prefix>/docs`.

Bấm **Authorize**, nhập username/mật khẩu là thử được mọi API cần đăng nhập —
một token dùng cho cả 5 service.

## API của auth-service

| Method | Path | Quyền |
|---|---|---|
| POST | `/api/auth/login` | public — form `username`, `password` |
| POST | `/api/auth/refresh` | public — `{refresh_token}` |
| POST | `/api/auth/logout` | đã đăng nhập — `{refresh_token}` |
| GET | `/api/auth/me` | đã đăng nhập |
| POST | `/api/auth/register` | public — tạo tài khoản READER |
| GET | `/api/auth/users` | ADMIN — `?page&size&q&role&is_active` |
| GET | `/api/auth/users/{id}` | ADMIN |
| POST | `/api/auth/users` | ADMIN — tạo thủ thư/admin |
| PATCH | `/api/auth/users/{id}` | ADMIN — khóa/mở, đổi quyền, sửa thông tin |

- Access token sống 15 phút, refresh token 7 ngày (`ACCESS_TTL_MINUTES`,
  `REFRESH_TTL_DAYS`).
- Mỗi lần refresh, token cũ bị thu hồi. **Dùng lại một refresh token đã thu
  hồi thì mọi phiên của tài khoản đó bị đăng xuất** — coi như token bị đánh
  cắp.
- Khóa tài khoản cắt mọi phiên ngay; access token đã phát còn sống tối đa 15
  phút.
- Admin không tự khóa hay tự bỏ quyền ADMIN của mình được. Thao tác tạo/sửa
  tài khoản được ghi vào `audit_logs` (không bao giờ ghi mật khẩu).

## Lệnh

`task.py` thay cho Makefile: chạy giống nhau ở PowerShell và Git Bash, không
cần cài `make` hay `uv`.

| Lệnh | Việc |
|---|---|
| `setup` | Tạo `.venv` và cài dependency |
| `keys` | Sinh cặp RSA cho JWT (`--force` để ghi đè) |
| `dev` | 5 service bằng uvicorn trên host + RabbitMQ/gateway trong Docker |
| `infra` | Chỉ RabbitMQ + gateway |
| `up` | 5 service chạy trong container (cần `db-grant` trước) |
| `down` / `reset` / `ps` / `logs [svc]` | Quản lý container |
| `test [svc]` | pytest — bỏ trống để chạy hết, hoặc `common`, `auth`… |
| `lint` / `fmt` | ruff |
| `smoke` | Gọi `/health` của 5 service qua gateway |
| `db-verify` | Chạy `db/05_verify.sql` — kiểm schema còn nguyên |
| `db-cli` | Mở `mysql` client vào `library_db` |
| `db-backup` | `mysqldump` `library_db` ra `backups/` |
| `db-migrate` | Áp migration `db/06+` chưa chạy — **tự backup trước** |
| `seed` | Đặt mật khẩu dev cho user mẫu, đảm bảo có một ADMIN |
| `db-grant` | In SQL tạo user MySQL cho đường Docker |
| `db-reset` | **Xóa và dựng lại `library_db`** (backup → nền → migration → seed) — cần cờ `--yes-wipe-library-db` |

## Thay đổi schema

Không dùng Alembic. `db/01`–`04` là nền; mọi thay đổi sau đó là một file mới
`db/NN_mo_ta.sql` với `NN` từ 06 trở lên:

1. Tạo `db/09_them_cot_x.sql` — không có `USE`, runner tự chọn database.
2. `python task.py db-migrate` — backup, rồi chạy các file chưa có trong bảng
   `schema_migrations`. Mỗi file chỉ chạy một lần.
3. Test tự dựng `library_test_db` từ nền + mọi migration, không cần làm gì thêm.

Không sửa file migration đã chạy; muốn đổi thì thêm file mới. Khôi phục từ
backup: `mysql -uroot -p < backups/library_db_<thoi-diem>.sql`.

| Migration | Nội dung |
|---|---|
| `06_auth_refresh_tokens.sql` | Bảng `refresh_tokens` (chỉ lưu sha256 của token) |
| `07_readers_user_unique.sql` | `UNIQUE(readers.user_id)` — một tài khoản tối đa một hồ sơ bạn đọc |
| `08_fines_three_statuses.sql` | Khoản phạt chỉ còn `UNPAID` / `PAID` / `WAIVED` (bỏ `PARTIAL`) |

## Kiến trúc

```
                    ┌─ gateway (nginx, Docker, :8000)
                    │
   /api/auth        ├─> auth-service         :8001
   /api/catalog     ├─> catalog-service      :8002
   /api/readers     ├─> reader-service       :8003
   /api/circulation ├─> circulation-service  :8004
   /api/billing     └─> billing-service      :8005
                              │
              ┌───────────────┴───────────────┐
        MySQL library_db                 RabbitMQ
        (host, :3306)                    (Docker, :5672)
```

Mỗi service có `/health` ở cả `/health` và `<prefix>/health`; Swagger ở
`<prefix>/docs`.

```
libs/common/common/    config, db, security, errors, events, http,
                       pagination, datetime_utils, health, testing
services/<svc>/app/    main, core/config, api/v1/{__init__,deps},
                       models, schemas, repositories, services, events
db/                    schema MySQL — nguồn duy nhất, không dùng Alembic
                       (không commit, xem "Cần có sẵn")
gateway/               template nginx
keys/                  jwt_*.pem (không commit)
```

Luồng gọi một chiều: **router → service → repository → DB**. Router không
viết query; repository không raise HTTPException.

Repository viết SQL tay bằng `text()` với tham số `:ten` (không ghép chuỗi).
Câu nào cần trả object ORM thì bọc `select(Model).from_statement(text(...))`.
INSERT và việc gán thuộc tính trên object trong service vẫn để SQLAlchemy
sinh SQL lúc `flush()`/`commit()`. Muốn xem mọi câu SQL đang chạy: truyền
`echo=True` cho `configure_database`.

## Quyền sở hữu bảng

Cả 5 service dùng chung một database, nên ranh giới dữ liệu là **quy ước chứ
không được DB ép buộc**. Mỗi service chỉ khai báo ORM model cho bảng nó sở
hữu; cần dữ liệu của service khác thì gọi API của service đó.

| Service | Bảng |
|---|---|
| auth | `users`, `roles`, `user_roles`, `audit_logs`, `refresh_tokens` |
| catalog | `books`, `authors`, `book_authors`, `publishers`, `categories`, `shelves`, `book_copies` |
| reader | `readers`, `library_cards` |
| circulation | `loans`, `loan_items`, `loan_renewals`, `reservations`, `loan_policies`, `processed_events`¹ |
| billing | `fines`, `payments`, `processed_events`¹ |

¹ thêm ở Phase 4.

`libs/common/tests/test_table_ownership.py` là thứ duy nhất giữ ranh giới này
không bị rò rỉ dần. Nó fail khi một service:

- khai báo ORM model (`__tablename__` hoặc `Table(...)`) cho bảng ngoài phạm vi;
- viết SQL thô (`FROM` / `JOIN` / `INTO` / `UPDATE`) chạm bảng của service khác.

**Ngoại lệ duy nhất**, ghi tên trong `ALLOWED_CROSS_READS`: auth-service đọc
`SELECT id FROM readers WHERE user_id = ?` trong
`app/repositories/reader_link_repo.py` để đưa `reader_id` vào JWT lúc đăng
nhập. Nhờ vậy đăng nhập không phụ thuộc reader-service phải đang chạy.

## Test

```bash
python task.py test              # tất cả
python task.py test common       # chỉ libs/common
python task.py test auth         # chỉ auth-service
```

Test chạy trên database riêng `library_test_db`, dựng lại từ `db/*.sql` mỗi
lần. `library_db` không bị đụng tới: `common.testing.load_schema` từ chối mọi
tên database không kết thúc bằng `_test_db`.

## Vài điều dễ vấp

- **`db/01_schema_mysql.sql` mở đầu bằng `DROP DATABASE`.** Đừng chạy tay vào
  `library_db` nếu không định xóa sạch. Dùng `task.py db-reset`.
- **MySQL `DATETIME` không lưu múi giờ.** Đọc lên là naive. Luôn đi qua
  `common.datetime_utils.as_utc()` trước khi đưa ra schema, và
  `to_naive_utc()` trước khi ghi xuống.
- **Trigger trong `db/02_triggers.sql` đã tự cập nhật `book_copies.status` và
  `loans.status`** khi `loan_items` đổi. Tầng service không được làm lại việc
  đó, nếu không hai bên sẽ ghi đè nhau.
- **Chống mượn trùng nằm ở tầng DB.** `ux_items_open_copy` (unique trên
  generated column) chặn hai phiếu mượn cùng giữ một bản sao. Bắt lỗi
  duplicate key rồi đổi thành `AppError(409, "copy_not_available")` — không
  cần `UPDATE ... RETURNING`, thứ MySQL vốn không có.
- **Tiền là `DECIMAL`**, sang Python là `Decimal`. Không dùng float.
- **Sửa `gateway/default.conf.template` xong phải `docker compose restart
  gateway`.** Template chỉ được render lúc container khởi động, và
  `docker compose up` không tạo lại container khi chỉ file mount thay đổi.

## Khác với `.claude/skills/library-backend/SKILL.md`

Skill viết cho PostgreSQL với 5 database tách rời. Dự án này dùng schema MySQL
20 bảng có sẵn, nên chín điểm sau đã lệch: MySQL + aiomysql thay
PostgreSQL + asyncpg; một database chung thay 5; bỏ Alembic (schema do
`db/*.sql` quản lý); `Base` và session nằm ở `libs/common`; claim `roles` là
mảng thay vì `role` đơn (schema có bảng nối `user_roles`); đăng nhập bằng
`username` thay email; quy tắc mượn trả đọc từ bảng `loan_policies` thay vì
`Settings`; venv + pip thay `uv`; `task.py` thay Makefile.
