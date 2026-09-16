-- ============================================================================
-- 04_seed.sql
-- Du lieu mau tieng Viet co dau (MySQL 8.0)
-- Chay doc lap, chay lai nhieu lan khong loi: xoa sach du lieu cu (giu
-- nguyen cau truc bang) truoc khi insert lai, tat FK check tam thoi de
-- TRUNCATE khong bi chan boi thu tu phu thuoc.
-- ============================================================================

USE library_db;
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE audit_logs;
TRUNCATE TABLE payments;
TRUNCATE TABLE fines;
TRUNCATE TABLE reservations;
TRUNCATE TABLE loan_renewals;
TRUNCATE TABLE loan_items;
TRUNCATE TABLE loans;
TRUNCATE TABLE loan_policies;
TRUNCATE TABLE library_cards;
TRUNCATE TABLE readers;
TRUNCATE TABLE book_copies;
TRUNCATE TABLE shelves;
TRUNCATE TABLE book_authors;
TRUNCATE TABLE books;
TRUNCATE TABLE categories;
TRUNCATE TABLE publishers;
TRUNCATE TABLE authors;
TRUNCATE TABLE user_roles;
TRUNCATE TABLE users;
TRUNCATE TABLE roles;
SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------------------------------------------------------
-- 1. PHAN QUYEN
-- ----------------------------------------------------------------------------

INSERT INTO roles (id, code, name, description) VALUES
(1, 'ADMIN',     'Quản trị hệ thống', 'Toàn quyền quản trị thư viện'),
(2, 'LIBRARIAN', 'Thủ thư',           'Xử lý mượn trả, đặt chỗ, phạt'),
(3, 'READER',    'Bạn đọc',           'Tài khoản tra cứu, đặt chỗ sách');

INSERT INTO users (id, username, password_hash, full_name, email, phone, is_active) VALUES
(1,  'admin',    '$2b$12$KIXQ7lZ5H8yJv3n1QeXO5eN8pQdX9s0kT1uJc2wR3xY4zA5bC6dEf', 'Nguyễn Quản Trị Hệ Thống', 'admin@thuvien.edu.vn',    '0900000001', TRUE),
(2,  'thuthu01', '$2b$12$KIXQ7lZ5H8yJv3n1QeXO5eN8pQdX9s0kT1uJc2wR3xY4zA5bC6dEf', 'Trần Thị Thủ Thư Một',     'thuthu01@thuvien.edu.vn', '0900000002', TRUE),
(3,  'thuthu02', '$2b$12$KIXQ7lZ5H8yJv3n1QeXO5eN8pQdX9s0kT1uJc2wR3xY4zA5bC6dEf', 'Lê Văn Thủ Thư Hai',       'thuthu02@thuvien.edu.vn', '0900000003', TRUE),
(4,  'docgia01', '$2b$12$KIXQ7lZ5H8yJv3n1QeXO5eN8pQdX9s0kT1uJc2wR3xY4zA5bC6dEf', 'Nguyễn Văn An',            'an.nguyen@gmail.com',     '0911000001', TRUE),
(5,  'docgia02', '$2b$12$KIXQ7lZ5H8yJv3n1QeXO5eN8pQdX9s0kT1uJc2wR3xY4zA5bC6dEf', 'Trần Thị Bình',            'binh.tran@gmail.com',     '0911000002', TRUE),
(6,  'docgia03', '$2b$12$KIXQ7lZ5H8yJv3n1QeXO5eN8pQdX9s0kT1uJc2wR3xY4zA5bC6dEf', 'Lê Văn Cường',             'cuong.le@gmail.com',      '0911000003', TRUE),
(7,  'docgia04', '$2b$12$KIXQ7lZ5H8yJv3n1QeXO5eN8pQdX9s0kT1uJc2wR3xY4zA5bC6dEf', 'Phạm Thị Dung',            'dung.pham@gmail.com',     '0911000004', TRUE),
(8,  'docgia05', '$2b$12$KIXQ7lZ5H8yJv3n1QeXO5eN8pQdX9s0kT1uJc2wR3xY4zA5bC6dEf', 'Hoàng Văn Em',             'em.hoang@gmail.com',      '0911000005', TRUE),
(9,  'docgia06', '$2b$12$KIXQ7lZ5H8yJv3n1QeXO5eN8pQdX9s0kT1uJc2wR3xY4zA5bC6dEf', 'Vũ Thị Phương',            'phuong.vu@gmail.com',     '0911000006', TRUE),
(10, 'docgia07', '$2b$12$KIXQ7lZ5H8yJv3n1QeXO5eN8pQdX9s0kT1uJc2wR3xY4zA5bC6dEf', 'Đặng Văn Giang',           'giang.dang@gmail.com',    '0911000007', TRUE),
(11, 'docgia08', '$2b$12$KIXQ7lZ5H8yJv3n1QeXO5eN8pQdX9s0kT1uJc2wR3xY4zA5bC6dEf', 'Bùi Thị Hoa',              'hoa.bui@gmail.com',       '0911000008', TRUE),
(12, 'docgia09', '$2b$12$KIXQ7lZ5H8yJv3n1QeXO5eN8pQdX9s0kT1uJc2wR3xY4zA5bC6dEf', 'Ngô Văn Ính',              'inh.ngo@gmail.com',       '0911000009', TRUE),
(13, 'docgia10', '$2b$12$KIXQ7lZ5H8yJv3n1QeXO5eN8pQdX9s0kT1uJc2wR3xY4zA5bC6dEf', 'Đỗ Thị Kim',               'kim.do@gmail.com',        '0911000010', TRUE);

INSERT INTO user_roles (user_id, role_id) VALUES
(1, 1),
(2, 2), (3, 2),
(4, 3), (5, 3), (6, 3), (7, 3), (8, 3), (9, 3), (10, 3), (11, 3), (12, 3), (13, 3);

-- ----------------------------------------------------------------------------
-- 2. DANH MUC SACH
-- ----------------------------------------------------------------------------

INSERT INTO authors (id, full_name, nationality) VALUES
(1,  'Vũ Trọng Phụng',    'Việt Nam'),
(2,  'Nam Cao',           'Việt Nam'),
(3,  'Ngô Tất Tố',        'Việt Nam'),
(4,  'Tô Hoài',           'Việt Nam'),
(5,  'Nguyễn Du',         'Việt Nam'),
(6,  'Hồ Chí Minh',       'Việt Nam'),
(7,  'Kim Lân',           'Việt Nam'),
(8,  'Nguyễn Nhật Ánh',   'Việt Nam'),
(9,  'Nguyễn Huy Thiệp',  'Việt Nam'),
(10, 'Paulo Coelho',      'Brazil'),
(11, 'Yuval Noah Harari', 'Israel'),
(12, 'Robert C. Martin',  'Hoa Kỳ'),
(13, 'Dale Carnegie',     'Hoa Kỳ'),
(14, 'Napoleon Hill',     'Hoa Kỳ'),
(15, 'Adam Khoo',         'Singapore');

INSERT INTO publishers (id, name) VALUES
(1, 'NXB Kim Đồng'),
(2, 'NXB Trẻ'),
(3, 'NXB Giáo Dục Việt Nam'),
(4, 'NXB Văn Học'),
(5, 'NXB Hội Nhà Văn'),
(6, 'NXB Tổng Hợp TP.HCM'),
(7, 'NXB Phụ Nữ Việt Nam'),
(8, 'NXB Lao Động');

INSERT INTO categories (id, parent_id, code, name, level) VALUES
(1,  NULL, 'VANHOC',        'Văn học',                1),
(2,  NULL, 'KHCN',          'Khoa học - Công nghệ',   1),
(3,  NULL, 'KNKT',          'Kỹ năng - Kinh tế',      1),
(4,  1,    'VANHOC_VN',     'Văn học Việt Nam',       2),
(5,  1,    'VANHOC_NN',     'Văn học nước ngoài',     2),
(6,  2,    'CNTT',          'Công nghệ thông tin',    2),
(7,  2,    'KHTN',          'Khoa học tự nhiên',      2),
(8,  3,    'KYNANG',        'Kỹ năng sống',           2),
(9,  3,    'KINHTE',        'Kinh tế - Quản trị',     2),
(10, 4,    'TIEUTHUYET_VN', 'Tiểu thuyết Việt Nam',   3),
(11, 4,    'TRUYENNGAN_VN', 'Truyện ngắn Việt Nam',   3),
(12, 5,    'TIEUTHUYET_NN', 'Tiểu thuyết nước ngoài', 3),
(13, 6,    'LAPTRINH',      'Lập trình',              3);

INSERT INTO books (id, title, isbn13, category_id, publisher_id, publish_year, language, page_count) VALUES
(1,  'Số Đỏ',                              '9786040000001', 10, 4, 1936, 'vi', 220),
(2,  'Giông Tố',                           '9786040000002', 10, 4, 1937, 'vi', 260),
(3,  'Chí Phèo',                           '9786040000003', 11, 4, 1941, 'vi', 180),
(4,  'Lão Hạc',                            '9786040000004', 11, 4, 1943, 'vi', 150),
(5,  'Tắt Đèn',                            '9786040000005', 10, 4, 1939, 'vi', 200),
(6,  'Dế Mèn Phiêu Lưu Ký',                '9786040000006', 11, 1, 1941, 'vi', 155),
(7,  'Truyện Kiều',                        '9786040000007', 10, 4, 1820, 'vi', 320),
(8,  'Nhật Ký Trong Tù',                   '9786040000008', 11, 4, 1943, 'vi', 140),
(9,  'Vợ Nhặt',                            '9786040000009', 11, 4, 1955, 'vi', 90),
(10, 'Mắt Biếc',                           '9786040000010', 10, 2, 1990, 'vi', 245),
(11, 'Cho Tôi Xin Một Vé Đi Tuổi Thơ',     '9786040000011', 10, 2, 2008, 'vi', 200),
(12, 'Kính Vạn Hoa - Tập 1',               '9786040000012', 11, 2, 1995, 'vi', 180),
(13, 'Tôi Thấy Hoa Vàng Trên Cỏ Xanh',     '9786040000013', 10, 2, 2010, 'vi', 378),
(14, 'Đảo Mộng Mơ',                        '9786040000014', 10, 2, 2011, 'vi', 320),
(15, 'Tướng Về Hưu',                       '9786040000015', 11, 5, 1987, 'vi', 130),
(16, 'Muối Của Rừng',                      '9786040000016', 11, 5, 1986, 'vi', 110),
(17, 'Nhà Giả Kim',                        '9786040000017', 12, 2, 1988, 'vi', 228),
(18, 'The Alchemist',                      '9786040000018', 12, 2, 1988, 'en', 208),
(19, 'Sapiens: Lược Sử Loài Người',        '9786040000019', 12, 6, 2011, 'vi', 466),
(20, 'Homo Deus: Lược Sử Tương Lai',       '9786040000020', 12, 6, 2015, 'vi', 450),
(21, '21 Bài Học Cho Thế Kỷ 21',           '9786040000021', 12, 6, 2018, 'vi', 380),
(22, 'Clean Code',                         '9786040000022', 13, 8, 2008, 'en', 464),
(23, 'Clean Architecture',                 '9786040000023', 13, 8, 2017, 'en', 432),
(24, 'The Clean Coder',                    '9786040000024', 13, 8, 2011, 'en', 256),
(25, 'Đắc Nhân Tâm',                       '9786040000025', 8,  6, 1936, 'vi', 320),
(26, 'Quẳng Gánh Lo Đi Và Vui Sống',       '9786040000026', 8,  6, 1948, 'vi', 300),
(27, 'Nghĩ Giàu Làm Giàu',                 '9786040000027', 9,  6, 1937, 'vi', 280),
(28, 'Bí Quyết Tay Trắng Thành Triệu Phú', '9786040000028', 9,  6, 2007, 'vi', 350),
(29, 'Tôi Tài Giỏi Bạn Cũng Thế',          '9786040000029', 8,  2, 2007, 'vi', 310),
(30, 'Lập Trình Python Cơ Bản',            '9786040000030', 13, 3, 2020, 'vi', 300),
(31, 'Cấu Trúc Dữ Liệu Và Giải Thuật',     '9786040000031', 6,  3, 2019, 'vi', 350),
(32, 'Nhập Môn Cơ Sở Dữ Liệu',             '9786040000032', 6,  3, 2021, 'vi', 280),
(33, 'Kinh Tế Học Vĩ Mô',                  '9786040000033', 9,  3, 2015, 'vi', 400),
(34, 'Kinh Tế Học Vi Mô',                  '9786040000034', 9,  3, 2015, 'vi', 380),
(35, 'Quản Trị Học',                       '9786040000035', 9,  3, 2016, 'vi', 360),
(36, 'Vật Lý Đại Cương',                   '9786040000036', 7,  3, 2018, 'vi', 420),
(37, 'Hóa Học Đại Cương',                  '9786040000037', 7,  3, 2018, 'vi', 400),
(38, 'Sinh Học Cơ Bản',                    '9786040000038', 7,  3, 2017, 'vi', 350),
(39, 'Truyện Ngắn Nam Cao Toàn Tập',       '9786040000039', 11, 4, 2000, 'vi', 500),
(40, 'Tuyển Tập Thơ Hồ Chí Minh',          '9786040000040', 11, 4, 1960, 'vi', 200);

INSERT INTO book_authors (book_id, author_id) VALUES
(1,1),(2,1),(3,2),(4,2),(5,3),(6,4),(7,5),(8,6),(9,7),
(10,8),(11,8),(12,8),(13,8),(14,8),(15,9),(16,9),(17,10),(18,10),
(19,11),(20,11),(21,11),(22,12),(23,12),(24,12),(25,13),(26,13),
(27,14),(28,15),(29,15),(30,12),(31,12),(32,12),(33,14),(34,14),
(35,14),(36,12),(37,12),(38,12),(39,2),(40,6);

-- ----------------------------------------------------------------------------
-- 3. KHO VAT LY
-- ----------------------------------------------------------------------------

INSERT INTO shelves (id, code, location, capacity) VALUES
(1,  'A1', 'Tầng 1 - Khu A - Kệ A1', 200),
(2,  'A2', 'Tầng 1 - Khu A - Kệ A2', 200),
(3,  'B1', 'Tầng 1 - Khu B - Kệ B1', 200),
(4,  'B2', 'Tầng 1 - Khu B - Kệ B2', 200),
(5,  'C1', 'Tầng 2 - Khu C - Kệ C1', 150),
(6,  'C2', 'Tầng 2 - Khu C - Kệ C2', 150),
(7,  'D1', 'Tầng 2 - Khu D - Kệ D1', 150),
(8,  'D2', 'Tầng 2 - Khu D - Kệ D2', 150),
(9,  'E1', 'Tầng 3 - Khu E - Kệ E1', 100),
(10, 'E2', 'Tầng 3 - Khu E - Kệ E2', 100);

-- 100 ban sao (barcode BC00001..BC00100), rai deu tren 40 dau sach va 10 ke.
-- Sach id 1..20 co 3 ban sao (copy_id = n, n+40, n+80), sach id 21..40 co 2
-- ban sao (copy_id = n, n+40). AUTO_INCREMENT gan id = n theo dung thu tu
-- ORDER BY nen loan_items ben duoi tham chieu truc tiep copy_id so.
INSERT INTO book_copies (book_id, barcode, shelf_id, status, acquired_date, price)
WITH RECURSIVE seq AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM seq WHERE n < 100
)
SELECT
    ((n - 1) % 40) + 1,
    CONCAT('BC', LPAD(n, 5, '0')),
    ((n - 1) % 10) + 1,
    'AVAILABLE',
    '2023-01-15',
    100000.00
FROM seq
ORDER BY n;

-- ----------------------------------------------------------------------------
-- 4. BAN DOC
-- ----------------------------------------------------------------------------

INSERT INTO readers (id, full_name, date_of_birth, gender, id_number, phone, email, reader_type, user_id) VALUES
(1,  'Nguyễn Văn An',    '2003-05-12', 'MALE',   '001099012345', '0921000001', 'an.nguyen@gmail.com',   'STUDENT', 4),
(2,  'Trần Thị Bình',    '2002-11-03', 'FEMALE', '001099012346', '0921000002', 'binh.tran@gmail.com',   'STUDENT', 5),
(3,  'Lê Văn Cường',     '2004-02-20', 'MALE',   '001099012347', '0921000003', 'cuong.le@gmail.com',    'STUDENT', 6),
(4,  'Phạm Thị Dung',    '2003-07-08', 'FEMALE', '001099012348', '0921000004', 'dung.pham@gmail.com',   'STUDENT', 7),
(5,  'Hoàng Văn Em',     '1985-01-15', 'MALE',   '001085012349', '0921000005', 'em.hoang@gmail.com',    'TEACHER', 8),
(6,  'Vũ Thị Phương',    '1988-09-25', 'FEMALE', '001088012350', '0921000006', 'phuong.vu@gmail.com',   'TEACHER', 9),
(7,  'Đặng Văn Giang',   '1990-03-30', 'MALE',   '001090012351', '0921000007', 'giang.dang@gmail.com',  'STAFF',   10),
(8,  'Bùi Thị Hoa',      '1992-12-12', 'FEMALE', '001092012352', '0921000008', 'hoa.bui@gmail.com',     'STAFF',   11),
(9,  'Ngô Văn Ính',      '1975-06-18', 'MALE',   '001075012353', '0921000009', 'inh.ngo@gmail.com',     'PUBLIC',  12),
(10, 'Đỗ Thị Kim',       '1980-04-22', 'FEMALE', '001080012354', '0921000010', 'kim.do@gmail.com',      'PUBLIC',  13);

-- reader 9: the EXPIRED (het han) - reader 10: the LOCKED (bi khoa)
INSERT INTO library_cards (id, reader_id, card_number, issue_date, expiry_date, status) VALUES
(1,  1,  'TC-0001', '2024-01-10', '2027-01-10', 'ACTIVE'),
(2,  2,  'TC-0002', '2024-01-10', '2027-01-10', 'ACTIVE'),
(3,  3,  'TC-0003', '2024-01-10', '2027-01-10', 'ACTIVE'),
(4,  4,  'TC-0004', '2024-01-10', '2027-01-10', 'ACTIVE'),
(5,  5,  'TC-0005', '2024-02-15', '2027-02-15', 'ACTIVE'),
(6,  6,  'TC-0006', '2024-02-15', '2027-02-15', 'ACTIVE'),
(7,  7,  'TC-0007', '2024-03-01', '2027-03-01', 'ACTIVE'),
(8,  8,  'TC-0008', '2024-03-01', '2027-03-01', 'ACTIVE'),
(9,  9,  'TC-0009', '2022-01-10', '2023-01-10', 'EXPIRED'),
(10, 10, 'TC-0010', '2024-05-01', '2027-05-01', 'LOCKED');

-- ----------------------------------------------------------------------------
-- 5. CHINH SACH MUON TRA
-- ----------------------------------------------------------------------------

INSERT INTO loan_policies (id, code, reader_type, max_loan_items, loan_period_days, max_renewals, renewal_period_days, fine_per_day, max_reservations) VALUES
(1, 'POL_STUDENT', 'STUDENT', 5, 14, 2, 7,  2000.00, 3),
(2, 'POL_TEACHER', 'TEACHER', 8, 30, 3, 14, 1500.00, 5),
(3, 'POL_STAFF',   'STAFF',   6, 21, 2, 10, 1500.00, 4),
(4, 'POL_PUBLIC',  'PUBLIC',  3, 10, 1, 5,  3000.00, 2);

-- ----------------------------------------------------------------------------
-- 6. MUON - TRA
-- ----------------------------------------------------------------------------

-- L1-L5: da tra du (CLOSED, lich su)
-- L6-L10: dang muon, chua den han (OPEN)
-- L11-L15: dang muon, DA QUA HAN (>= 5 phieu, phuc vu v_overdue_loans)
-- L16-L18: tra mot phan (PARTIAL, 2 cuon/phieu)
-- L19-L20: bi huy truoc khi giao sach (CANCELLED, khong co loan_items)
INSERT INTO loans (id, reader_id, library_card_id, policy_id, staff_id, loan_date, status) VALUES
(1,  1,  1,  1, 2, '2026-07-06', 'OPEN'),
(2,  2,  2,  1, 2, '2026-07-08', 'OPEN'),
(3,  3,  3,  1, 3, '2026-07-11', 'OPEN'),
(4,  4,  4,  1, 3, '2026-07-14', 'OPEN'),
(5,  5,  5,  2, 2, '2026-07-18', 'OPEN'),
(6,  6,  6,  2, 2, '2026-09-11', 'OPEN'),
(7,  7,  7,  3, 3, '2026-09-14', 'OPEN'),
(8,  8,  8,  3, 2, '2026-09-11', 'OPEN'),
(9,  9,  9,  4, 3, '2026-09-12', 'OPEN'),
(10, 10, 10, 4, 2, '2026-09-10', 'OPEN'),
(11, 1,  1,  1, 2, '2026-08-06', 'OPEN'),
(12, 2,  2,  1, 3, '2026-08-11', 'OPEN'),
(13, 3,  3,  1, 2, '2026-08-15', 'OPEN'),
(14, 4,  4,  1, 3, '2026-08-18', 'OPEN'),
(15, 5,  5,  2, 2, '2026-08-22', 'OPEN'),
(16, 6,  6,  2, 3, '2026-08-16', 'OPEN'),
(17, 7,  7,  3, 2, '2026-08-22', 'OPEN'),
(18, 8,  8,  3, 3, '2026-08-14', 'OPEN'),
(19, 9,  9,  4, 2, '2026-09-05', 'CANCELLED'),
(20, 10, 10, 4, 3, '2026-09-06', 'CANCELLED');

-- loan_items: cot copy_id_if_open tu sinh nen khong insert; trigger
-- trg_items_after_insert se tu cap nhat book_copies.status va loans.status.
INSERT INTO loan_items (loan_id, copy_id, due_date, returned_at, return_condition) VALUES
(1,  1,  '2026-07-20', '2026-07-18 10:00:00', 'GOOD'),
(2,  2,  '2026-07-22', '2026-07-21 09:00:00', 'GOOD'),
(3,  3,  '2026-07-25', '2026-07-24 14:00:00', 'GOOD'),
(4,  4,  '2026-07-28', '2026-07-27 16:00:00', 'GOOD'),
(5,  5,  '2026-08-01', '2026-08-01 11:00:00', 'GOOD'),
(6,  6,  '2026-09-25', NULL, NULL),
(7,  7,  '2026-09-28', NULL, NULL),
(8,  8,  '2026-10-02', NULL, NULL),
(9,  9,  '2026-09-22', NULL, NULL),
(10, 10, '2026-09-20', NULL, NULL),
(11, 11, '2026-08-20', NULL, NULL),
(12, 12, '2026-08-25', NULL, NULL),
(13, 13, '2026-08-29', NULL, NULL),
(14, 14, '2026-09-01', NULL, NULL),
(15, 15, '2026-09-05', NULL, NULL),
(16, 18, '2026-08-30', '2026-09-05 10:00:00', 'GOOD'),
(16, 19, '2026-09-20', NULL, NULL),
(17, 20, '2026-09-05', '2026-09-10 10:00:00', 'GOOD'),
(17, 21, '2026-09-22', NULL, NULL),
(18, 22, '2026-08-28', '2026-09-08 10:00:00', 'DAMAGED'),
(18, 23, '2026-09-25', NULL, NULL);

-- ----------------------------------------------------------------------------
-- 7. DAT CHO
-- ----------------------------------------------------------------------------

INSERT INTO reservations (reader_id, book_id, reserved_at, status, expires_at) VALUES
(5, 10, '2026-09-10 09:00:00', 'PENDING',   NULL),
(6, 15, '2026-09-05 09:00:00', 'READY',     '2026-09-20 09:00:00'),
(7, 20, '2026-08-20 09:00:00', 'FULFILLED', NULL),
(8, 25, '2026-08-25 09:00:00', 'CANCELLED', NULL),
(9, 30, '2026-07-01 09:00:00', 'EXPIRED',   '2026-07-15 09:00:00');

-- ----------------------------------------------------------------------------
-- 8. PHAT
-- ----------------------------------------------------------------------------

-- fine 1,2,3,5 gan voi 4 trong 5 phieu qua han (loan_item_id 11-14);
-- fine 4 la phi hu hong (loan_item_id 20, tra sach DAMAGED)
INSERT INTO fines (id, loan_item_id, reader_id, fine_type, amount, status, issued_at) VALUES
(1, 11, 1, 'OVERDUE', 52000.00, 'UNPAID',  '2026-09-15 08:00:00'),
(2, 12, 2, 'OVERDUE', 42000.00, 'PARTIAL', '2026-09-15 08:00:00'),
(3, 13, 3, 'OVERDUE', 34000.00, 'PAID',    '2026-09-15 08:00:00'),
(4, 20, 8, 'DAMAGE',  150000.00,'UNPAID',  '2026-09-08 10:30:00'),
(5, 14, 4, 'OVERDUE', 28000.00, 'UNPAID',  '2026-09-15 08:00:00');

INSERT INTO payments (fine_id, amount, paid_at, method, staff_id) VALUES
(2, 20000.00, '2026-09-12 10:00:00', 'CASH', 2),
(3, 34000.00, '2026-09-10 10:00:00', 'CASH', 3);
