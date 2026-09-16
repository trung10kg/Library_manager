# Library DB — MySQL 8.0

Chuyển đổi từ `../library_schema_postgres.sql` (PostgreSQL) sang MySQL 8.0.
Database: `library_db`, charset `utf8mb4`, collation `utf8mb4_unicode_ci`, engine `InnoDB`.

## Cách chạy

Yêu cầu: MySQL 8.0.16 trở lên (bắt buộc để CHECK constraint được enforce),
client `mysql` trong PATH (hoặc dùng bản cài ở
`C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe`).

### Chạy toàn bộ một lần (khuyến nghị)

```bash
cd db
DB_USER=root DB_PASS=1234 DB_NAME=library_db ./reset.sh
```

Không truyền biến môi trường thì dùng mặc định `DB_USER=root DB_PASS=1234
DB_NAME=library_db DB_HOST=127.0.0.1 DB_PORT=3306` — đúng như môi trường đã
mô tả. Đặt `db/.env` (không commit — đã có trong `.gitignore`) rồi `source
db/.env` trước khi gọi `reset.sh` nếu muốn cố định thông tin kết nối.

Script chạy tuần tự cả 5 file và dừng ngay nếu có lỗi (`set -euo pipefail`).

### Chạy từng file riêng lẻ

Mỗi file tự chứa `DROP ... IF EXISTS` nên chạy lại nhiều lần không lỗi:

```bash
MYSQL="/c/Program Files/MySQL/MySQL Server 8.0/bin/mysql.exe"
"$MYSQL" -h127.0.0.1 -P3306 -uroot -p1234 --default-character-set=utf8mb4 < 01_schema_mysql.sql
"$MYSQL" -h127.0.0.1 -P3306 -uroot -p1234 --default-character-set=utf8mb4 < 02_triggers.sql
"$MYSQL" -h127.0.0.1 -P3306 -uroot -p1234 --default-character-set=utf8mb4 < 03_views.sql
"$MYSQL" -h127.0.0.1 -P3306 -uroot -p1234 --default-character-set=utf8mb4 < 04_seed.sql
"$MYSQL" -h127.0.0.1 -P3306 -uroot -p1234 --default-character-set=utf8mb4 < 05_verify.sql
```

Luôn dùng `--default-character-set=utf8mb4` để dữ liệu tiếng Việt có dấu
không bị lỗi encoding khi nạp qua client.

## Sơ đồ quan hệ (text)

```
roles ─┬─< user_roles >─┬─ users ──< readers >── library_cards ──< loans
       │                │              │                            │
       │                └── users.staff_id (loans, loan_renewals,   │
       │                    payments — thu thu xu ly nghiep vu)     │
       │                                                            ├─< loan_items >── book_copies ── shelves
categories ─┬─< books >─┬─< book_authors >── authors                │        │              │
 (self ref, │           │                                           │        │              └── books
  3 cap)    │           ├─< reservations ── readers                └────────┴── loan_renewals
            │           │
            └── publishers

loan_policies ──< loans (quy tac muon/tra/phat theo reader_type)

loan_items ──< fines ──< payments
readers ──< fines (fines co the khong gan loan_item_id — vd phi hu hong doc lap)

audit_logs ── users (nhat ky thao tac, tuy chon)
```

Tóm tắt quan hệ chính:

- `books` (đầu sách) 1—N `book_copies` (từng cuốn, barcode riêng). Mượn/trả
  và tồn kho gắn vào `book_copies`; tìm kiếm, đặt chỗ gắn vào `books`.
- `loans` (phiếu mượn, header) 1—N `loan_items` (từng cuốn, `due_date` và
  `returned_at` riêng từng dòng).
- `loan_items` 1—N `loan_renewals` (lịch sử gia hạn từng cuốn).
- `readers` 1—N `library_cards` (thẻ), 1—N `loans`, 1—N `reservations`, 1—N `fines`.
- `loan_policies` quy định số cuốn tối đa, hạn mượn, mức phạt/ngày theo
  `reader_type` — `loans` tham chiếu `policy_id`, không hard-code số liệu.
- `fines` 1—N `payments` (một khoản phạt có thể trả nhiều lần → `PARTIAL`).
- `categories` tự tham chiếu `parent_id` để tạo cây danh mục 3 cấp.

## Các chỗ khác biệt so với bản PostgreSQL

| # | PostgreSQL | MySQL 8.0 | Vì sao |
|---|---|---|---|
| 1 | `BIGSERIAL`/`SMALLSERIAL` | `BIGINT`/`SMALLINT AUTO_INCREMENT` | MySQL không có kiểu serial |
| 2 | `TIMESTAMPTZ` | `DATETIME` | Không dùng `TIMESTAMP` để tránh giới hạn năm 2038 |
| 3 | `now()` | `CURRENT_TIMESTAMP` | Cú pháp MySQL |
| 4 | `NUMERIC(p,s)` | `DECIMAL(p,s)` | Tương đương, đổi tên kiểu |
| 5 | `JSONB` | `JSON` | MySQL chỉ có một kiểu JSON (lưu dạng nhị phân tối ưu sẵn) |
| 6 | `~` / `~*` (regex) | `REGEXP_LIKE(col, 'pattern')` trong CHECK | Cú pháp toán tử regex khác nhau |
| 7 | `COUNT(*) FILTER (WHERE ...)` | `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` | MySQL không hỗ trợ `FILTER` |
| 8 | `LEFT JOIN LATERAL` (trong `v_reader_debt`) | Derived table gộp sẵn theo `fine_id` rồi `JOIN` thường | Không cần tương quan ngoài `fine_id`, LATERAL không cần thiết |
| 9 | `CURRENT_DATE - due_date` | `DATEDIFF(CURRENT_DATE, due_date)` | Phép trừ ngày trực tiếp không áp dụng được trên MySQL |

### 3 vấn đề bắt buộc

**(a) Partial unique index → generated column STORED + UNIQUE KEY.**
MySQL không hỗ trợ `CREATE UNIQUE INDEX ... WHERE ...`. Giải pháp: thêm cột
sinh (`GENERATED ALWAYS AS (...) STORED`) chỉ mang giá trị khi điều kiện
nghiệp vụ đúng, còn lại `NULL` — MySQL cho phép nhiều `NULL` trong UNIQUE KEY
nên chỉ chặn đúng lúc vi phạm:

- `loan_items.copy_id_if_open` — chặn 1 bản sao nằm ở 2 phiếu mượn chưa trả
  cùng lúc (`ux_items_open_copy`).
- `library_cards.reader_id_if_active` — chặn 1 bạn đọc có 2 thẻ `ACTIVE`
  (`ux_cards_one_active`).
- `reservations.reader_id_if_active` + `book_id_if_active` — chặn đặt trùng
  cùng đầu sách khi phiếu cũ còn `PENDING`/`READY` (`ux_reservations_active`).

  **Hệ quả không lường trước:** InnoDB không cho phép `ON DELETE
  CASCADE`/`SET NULL` trên một cột đang làm nền cho generated column khác
  trong cùng bảng (lỗi `1215 Cannot add foreign key constraint`). Vì vậy 3
  FK sau đã đổi từ `CASCADE` (dự định ban đầu) sang `RESTRICT` — và đã sửa
  tương ứng trong `library_schema_postgres.sql` để 2 bản khớp nhau:
  `library_cards.reader_id`, `reservations.reader_id`, `reservations.book_id`.

**(b) CHECK dùng hàm không tất định (`CURRENT_DATE`/`now()`) → chuyển sang
BEFORE INSERT/UPDATE trigger.** MySQL cấm hàm không tất định trong CHECK
constraint. `ck_books_year` (publish_year so với năm hiện tại) và
`ck_readers_dob` (ngày sinh phải trước hôm nay) được giữ nguyên quy tắc,
chỉ chuyển chỗ enforce sang trigger (`trg_books_year_ins/upd`,
`trg_readers_dob_ins/upd` trong `02_triggers.sql`), dùng `SIGNAL SQLSTATE
'45000'` để báo lỗi giống hành vi CHECK.

**(c) Partial index `WHERE returned_at IS NULL`** → đổi thành index thường
`idx_items_due` trên `(returned_at, due_date)` — vẫn hỗ trợ tốt truy vấn lọc
theo `returned_at IS NULL` rồi sắp xếp/lọc theo `due_date`.

### Index `lower(...)`

Bản Postgres có index trên `lower(title)` và `lower(full_name)` để tìm kiếm
không phân biệt hoa/thường. Vì `utf8mb4_unicode_ci` (case-insensitive theo
collation) đã tự động không phân biệt hoa/thường, MySQL chỉ cần index
thường trên cột gốc: `idx_books_title`, `idx_authors_fullname`,
`idx_readers_fullname`.

## Trigger nghiệp vụ (`02_triggers.sql`)

Ngoài 2 cặp trigger CHECK ở mục (b), có thêm:

- `trg_items_after_insert` (AFTER INSERT trên `loan_items`): nếu
  `returned_at IS NULL` → đặt `book_copies.status = 'ON_LOAN'`; nếu đã có
  `returned_at` ngay lúc thêm (dữ liệu lịch sử/seed) → đặt thẳng trạng thái
  cuối (`AVAILABLE`/`DAMAGED`/`LOST`) và cập nhật `loans.status` tương ứng.
- `trg_items_after_update` (AFTER UPDATE trên `loan_items`): khi
  `returned_at` chuyển từ `NULL` sang có giá trị → trả `book_copies.status`
  về `AVAILABLE`, hoặc `DAMAGED`/`LOST` tùy `return_condition`; đồng thời cập
  nhật `loans.status = 'CLOSED'` nếu tất cả các dòng của phiếu đã trả, hoặc
  `'PARTIAL'` nếu mới trả một phần.

## File

```
db/
├── 01_schema_mysql.sql   CREATE DATABASE + 20 bảng + index + generated column
├── 02_triggers.sql       Trigger CHECK thay thế + trigger cập nhật trạng thái
├── 03_views.sql          v_book_availability, v_overdue_loans, v_reader_debt
├── 04_seed.sql           Dữ liệu mẫu tiếng Việt có dấu
├── 05_verify.sql         Đếm số dòng, in view, 5 test ràng buộc âm (PASS/FAIL)
├── reset.sh              Drop & dựng lại toàn bộ từ đầu (đọc DB_* từ env)
└── README.md             File này
```

Mỗi file `.sql` tự chứa `DROP ... IF EXISTS` (database/bảng/trigger/view/
procedure tùy loại) nên chạy độc lập, chạy lại nhiều lần không lỗi.

## Đã kiểm chứng thực tế

Đã chạy `reset.sh` trên MySQL 8.0.45 local (root/1234, port 3306):

- Tạo sạch 20 bảng, 3 view, 8 trigger.
- Seed: 40 đầu sách, 100 bản sao, 10 bạn đọc (1 thẻ `EXPIRED`, 1 thẻ
  `LOCKED`), 20 phiếu mượn (5 `CLOSED`, 10 `OPEN`, 3 `PARTIAL`, 2
  `CANCELLED` — trong đó 5 phiếu đang `OPEN` bị quá hạn), 5 đặt chỗ đủ 5
  trạng thái, 5 khoản phạt (`UNPAID`/`PARTIAL`/`PAID`).
- `v_overdue_loans` trả về đúng 5 dòng, tiền phạt ước tính khác 0.
- Cả 5 test ràng buộc âm ở mục 5 của `05_verify.sql` đều `PASS` (bị chặn
  đúng như thiết kế).
