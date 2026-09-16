-- ============================================================================
-- 01_schema_mysql.sql
-- CREATE DATABASE + tables + indexes + generated columns (MySQL 8.0)
-- Chuyen doi tu ../library_schema_postgres.sql
-- Idempotent: DROP DATABASE IF EXISTS truoc khi tao lai, chay lai bao nhieu
-- lan cung duoc.
-- ============================================================================

DROP DATABASE IF EXISTS library_db;
CREATE DATABASE library_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE library_db;
SET NAMES utf8mb4;

-- ----------------------------------------------------------------------------
-- 1. PHAN QUYEN
-- ----------------------------------------------------------------------------

CREATE TABLE roles (
    id          SMALLINT AUTO_INCREMENT PRIMARY KEY,
    code        VARCHAR(30)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ux_roles_code UNIQUE (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE users (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(50)  NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    full_name      VARCHAR(150) NOT NULL,
    email          VARCHAR(150),
    phone          VARCHAR(20),
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at  DATETIME,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ux_users_username UNIQUE (username),
    CONSTRAINT ux_users_email UNIQUE (email),
    CONSTRAINT ck_users_email CHECK (email IS NULL OR REGEXP_LIKE(email, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')),
    CONSTRAINT ck_users_phone CHECK (phone IS NULL OR REGEXP_LIKE(phone, '^[0-9+() -]{8,20}$'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE user_roles (
    user_id     BIGINT NOT NULL,
    role_id     SMALLINT NOT NULL,
    assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 2. DANH MUC SACH
-- ----------------------------------------------------------------------------

CREATE TABLE authors (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    full_name    VARCHAR(150) NOT NULL,
    pen_name     VARCHAR(150),
    nationality  VARCHAR(100),
    birth_year   SMALLINT,
    death_year   SMALLINT,
    biography    TEXT,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_authors_years CHECK (death_year IS NULL OR birth_year IS NULL OR death_year >= birth_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- utf8mb4_unicode_ci khong phan biet hoa/thuong nen index thuong la du,
-- khong can bieu thuc lower(full_name) nhu ban Postgres
CREATE INDEX idx_authors_fullname ON authors (full_name);

CREATE TABLE publishers (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(200) NOT NULL,
    address    VARCHAR(300),
    phone      VARCHAR(20),
    email      VARCHAR(150),
    website    VARCHAR(200),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ux_publishers_name UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE categories (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    parent_id   BIGINT,
    code        VARCHAR(30),
    name        VARCHAR(150) NOT NULL,
    level       SMALLINT NOT NULL DEFAULT 1,
    description TEXT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ux_categories_code UNIQUE (code),
    CONSTRAINT ck_categories_level CHECK (level BETWEEN 1 AND 3),
    CONSTRAINT fk_categories_parent FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE books (
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,
    title            VARCHAR(300) NOT NULL,
    subtitle         VARCHAR(300),
    isbn13           VARCHAR(20),
    category_id      BIGINT,
    publisher_id     BIGINT,
    publish_year     SMALLINT,
    edition          VARCHAR(50),
    language         VARCHAR(50) NOT NULL DEFAULT 'vi',
    page_count       INT,
    description      TEXT,
    cover_image_url  VARCHAR(500),
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ux_books_isbn13 UNIQUE (isbn13),
    CONSTRAINT ck_books_pages CHECK (page_count IS NULL OR page_count > 0),
    -- ck_books_year (publish_year so voi nam hien tai) da chuyen sang
    -- BEFORE INSERT/UPDATE trigger trong 02_triggers.sql vi MySQL cam ham
    -- khong tat dinh (CURRENT_DATE) trong CHECK constraint.
    CONSTRAINT fk_books_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    CONSTRAINT fk_books_publisher FOREIGN KEY (publisher_id) REFERENCES publishers(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_books_title ON books (title);
CREATE INDEX idx_books_category ON books (category_id);
CREATE INDEX idx_books_publisher ON books (publisher_id);

CREATE TABLE book_authors (
    book_id      BIGINT NOT NULL,
    author_id    BIGINT NOT NULL,
    author_order SMALLINT NOT NULL DEFAULT 1,
    role         VARCHAR(20) NOT NULL DEFAULT 'AUTHOR',
    PRIMARY KEY (book_id, author_id),
    CONSTRAINT ck_book_authors_role CHECK (role IN ('AUTHOR','TRANSLATOR','EDITOR','ILLUSTRATOR')),
    CONSTRAINT fk_book_authors_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    CONSTRAINT fk_book_authors_author FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 3. KHO VAT LY
-- ----------------------------------------------------------------------------

CREATE TABLE shelves (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    code       VARCHAR(20) NOT NULL,
    location   VARCHAR(200),
    capacity   INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ux_shelves_code UNIQUE (code),
    CONSTRAINT ck_shelves_capacity CHECK (capacity IS NULL OR capacity > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE book_copies (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    book_id        BIGINT NOT NULL,
    barcode        VARCHAR(50) NOT NULL,
    shelf_id       BIGINT,
    status         VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE',
    condition_note VARCHAR(300),
    acquired_date  DATE NOT NULL DEFAULT (CURRENT_DATE),
    price          DECIMAL(12,2),
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ux_copies_barcode UNIQUE (barcode),
    CONSTRAINT ck_copies_status CHECK (status IN ('AVAILABLE','ON_LOAN','RESERVED','DAMAGED','LOST','WITHDRAWN')),
    CONSTRAINT ck_copies_price CHECK (price IS NULL OR price >= 0),
    CONSTRAINT fk_copies_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT,
    CONSTRAINT fk_copies_shelf FOREIGN KEY (shelf_id) REFERENCES shelves(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_copies_book ON book_copies (book_id);
CREATE INDEX idx_copies_status ON book_copies (status);

-- ----------------------------------------------------------------------------
-- 4. BAN DOC
-- ----------------------------------------------------------------------------

CREATE TABLE readers (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    full_name      VARCHAR(150) NOT NULL,
    date_of_birth  DATE,
    gender         VARCHAR(10),
    id_number      VARCHAR(30),
    address        VARCHAR(300),
    phone          VARCHAR(20),
    email          VARCHAR(150),
    reader_type    VARCHAR(20) NOT NULL DEFAULT 'STUDENT',
    user_id        BIGINT,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ux_readers_id_number UNIQUE (id_number),
    CONSTRAINT ck_readers_gender CHECK (gender IS NULL OR gender IN ('MALE','FEMALE','OTHER')),
    CONSTRAINT ck_readers_type CHECK (reader_type IN ('STUDENT','TEACHER','STAFF','PUBLIC')),
    CONSTRAINT ck_readers_phone CHECK (phone IS NULL OR REGEXP_LIKE(phone, '^[0-9+() -]{8,20}$')),
    -- ck_readers_dob (date_of_birth < CURRENT_DATE) da chuyen sang
    -- BEFORE INSERT/UPDATE trigger trong 02_triggers.sql
    CONSTRAINT fk_readers_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_readers_fullname ON readers (full_name);

CREATE TABLE library_cards (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    reader_id           BIGINT NOT NULL,
    card_number         VARCHAR(30) NOT NULL,
    issue_date          DATE NOT NULL DEFAULT (CURRENT_DATE),
    expiry_date         DATE NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    notes               VARCHAR(300),
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Thay the cho partial unique index cua Postgres
    -- (CREATE UNIQUE INDEX ... WHERE status = 'ACTIVE'):
    -- cot sinh chi mang gia tri khi status = ACTIVE, con lai la NULL.
    -- MySQL cho phep nhieu NULL trong UNIQUE KEY nen chi rang buoc dung
    -- luc co 2 the ACTIVE tro len cho cung 1 reader_id.
    reader_id_if_active BIGINT GENERATED ALWAYS AS (CASE WHEN status = 'ACTIVE' THEN reader_id ELSE NULL END) STORED,
    CONSTRAINT ux_cards_number UNIQUE (card_number),
    CONSTRAINT ux_cards_one_active UNIQUE (reader_id_if_active),
    CONSTRAINT ck_cards_status CHECK (status IN ('ACTIVE','EXPIRED','LOCKED','LOST')),
    CONSTRAINT ck_cards_expiry CHECK (expiry_date > issue_date),
    -- ON DELETE RESTRICT (khong phai CASCADE nhu du dinh ban dau): InnoDB
    -- khong cho phep CASCADE/SET NULL tren mot cot dang lam nen cho
    -- generated column (reader_id_if_active). Da doi tuong ung sang
    -- RESTRICT trong ca library_schema_postgres.sql de 2 ban khop nhau.
    CONSTRAINT fk_cards_reader FOREIGN KEY (reader_id) REFERENCES readers(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_cards_reader ON library_cards (reader_id);

-- ----------------------------------------------------------------------------
-- 5. CHINH SACH MUON TRA
-- ----------------------------------------------------------------------------

CREATE TABLE loan_policies (
    id                   SMALLINT AUTO_INCREMENT PRIMARY KEY,
    code                 VARCHAR(30) NOT NULL,
    reader_type          VARCHAR(20) NOT NULL,
    max_loan_items       SMALLINT NOT NULL,
    loan_period_days     SMALLINT NOT NULL,
    max_renewals         SMALLINT NOT NULL DEFAULT 1,
    renewal_period_days  SMALLINT NOT NULL,
    fine_per_day         DECIMAL(10,2) NOT NULL,
    max_reservations     SMALLINT NOT NULL DEFAULT 3,
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    created_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ux_policies_code UNIQUE (code),
    CONSTRAINT ux_policies_reader_type UNIQUE (reader_type),
    CONSTRAINT ck_policies_reader_type CHECK (reader_type IN ('STUDENT','TEACHER','STAFF','PUBLIC')),
    CONSTRAINT ck_policies_max_items CHECK (max_loan_items > 0),
    CONSTRAINT ck_policies_period CHECK (loan_period_days > 0),
    CONSTRAINT ck_policies_renewals CHECK (max_renewals >= 0),
    CONSTRAINT ck_policies_renewal_period CHECK (renewal_period_days > 0),
    CONSTRAINT ck_policies_fine CHECK (fine_per_day >= 0),
    CONSTRAINT ck_policies_max_res CHECK (max_reservations >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 6. MUON - TRA
-- ----------------------------------------------------------------------------

CREATE TABLE loans (
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,
    reader_id        BIGINT NOT NULL,
    library_card_id  BIGINT NOT NULL,
    policy_id        SMALLINT NOT NULL,
    staff_id         BIGINT,
    loan_date        DATE NOT NULL DEFAULT (CURRENT_DATE),
    status           VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    notes            VARCHAR(300),
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_loans_status CHECK (status IN ('OPEN','PARTIAL','CLOSED','CANCELLED')),
    CONSTRAINT fk_loans_reader FOREIGN KEY (reader_id) REFERENCES readers(id) ON DELETE RESTRICT,
    CONSTRAINT fk_loans_card FOREIGN KEY (library_card_id) REFERENCES library_cards(id) ON DELETE RESTRICT,
    CONSTRAINT fk_loans_policy FOREIGN KEY (policy_id) REFERENCES loan_policies(id) ON DELETE RESTRICT,
    CONSTRAINT fk_loans_staff FOREIGN KEY (staff_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_loans_reader ON loans (reader_id);
CREATE INDEX idx_loans_status ON loans (status);

CREATE TABLE loan_items (
    id                BIGINT AUTO_INCREMENT PRIMARY KEY,
    loan_id           BIGINT NOT NULL,
    copy_id           BIGINT NOT NULL,
    due_date          DATE NOT NULL,
    returned_at       DATETIME,
    return_condition  VARCHAR(20),
    notes             VARCHAR(300),
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Thay the partial unique index cua Postgres
    -- (WHERE returned_at IS NULL): mot ban sao khong the co 2 dong
    -- loan_items dang mo (chua tra) cung luc.
    copy_id_if_open   BIGINT GENERATED ALWAYS AS (CASE WHEN returned_at IS NULL THEN copy_id ELSE NULL END) STORED,
    CONSTRAINT ux_items_open_copy UNIQUE (copy_id_if_open),
    CONSTRAINT ck_items_return_cond CHECK (return_condition IS NULL OR return_condition IN ('GOOD','DAMAGED','LOST')),
    CONSTRAINT fk_items_loan FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE,
    CONSTRAINT fk_items_copy FOREIGN KEY (copy_id) REFERENCES book_copies(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Thay the partial index "idx_items_due ... WHERE returned_at IS NULL"
-- bang index thuong tren (returned_at, due_date)
CREATE INDEX idx_items_due ON loan_items (returned_at, due_date);
CREATE INDEX idx_items_loan ON loan_items (loan_id);

CREATE TABLE loan_renewals (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    loan_item_id   BIGINT NOT NULL,
    old_due_date   DATE NOT NULL,
    new_due_date   DATE NOT NULL,
    renewed_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    staff_id       BIGINT,
    CONSTRAINT ck_renewals_dates CHECK (new_due_date > old_due_date),
    CONSTRAINT fk_renewals_item FOREIGN KEY (loan_item_id) REFERENCES loan_items(id) ON DELETE CASCADE,
    CONSTRAINT fk_renewals_staff FOREIGN KEY (staff_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 7. DAT CHO
-- ----------------------------------------------------------------------------

CREATE TABLE reservations (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    reader_id           BIGINT NOT NULL,
    book_id             BIGINT NOT NULL,
    reserved_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status              VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    expires_at          DATETIME,
    notes               VARCHAR(300),
    -- Thay the partial unique index tren (reader_id, book_id)
    -- WHERE status IN ('PENDING','READY'): 2 cot sinh cung NULL khi
    -- khong active nen khong bao gio dung cham nhau trong UNIQUE KEY.
    reader_id_if_active BIGINT GENERATED ALWAYS AS (CASE WHEN status IN ('PENDING','READY') THEN reader_id ELSE NULL END) STORED,
    book_id_if_active   BIGINT GENERATED ALWAYS AS (CASE WHEN status IN ('PENDING','READY') THEN book_id ELSE NULL END) STORED,
    CONSTRAINT ux_reservations_active UNIQUE (reader_id_if_active, book_id_if_active),
    CONSTRAINT ck_reservations_status CHECK (status IN ('PENDING','READY','FULFILLED','CANCELLED','EXPIRED')),
    -- ON DELETE RESTRICT o ca 2 FK (thay vi CASCADE) vi cung ly do
    -- generated column nhu tren library_cards
    CONSTRAINT fk_reservations_reader FOREIGN KEY (reader_id) REFERENCES readers(id) ON DELETE RESTRICT,
    CONSTRAINT fk_reservations_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_reservations_book ON reservations (book_id);

-- ----------------------------------------------------------------------------
-- 8. PHAT
-- ----------------------------------------------------------------------------

CREATE TABLE fines (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    loan_item_id  BIGINT,
    reader_id     BIGINT NOT NULL,
    fine_type     VARCHAR(20) NOT NULL,
    amount        DECIMAL(10,2) NOT NULL,
    status        VARCHAR(20) NOT NULL DEFAULT 'UNPAID',
    issued_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes         VARCHAR(300),
    CONSTRAINT ck_fines_type CHECK (fine_type IN ('OVERDUE','DAMAGE','LOST')),
    CONSTRAINT ck_fines_amount CHECK (amount >= 0),
    CONSTRAINT ck_fines_status CHECK (status IN ('UNPAID','PARTIAL','PAID','WAIVED')),
    CONSTRAINT fk_fines_item FOREIGN KEY (loan_item_id) REFERENCES loan_items(id) ON DELETE SET NULL,
    CONSTRAINT fk_fines_reader FOREIGN KEY (reader_id) REFERENCES readers(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_fines_reader ON fines (reader_id);
CREATE INDEX idx_fines_status ON fines (status);

CREATE TABLE payments (
    id        BIGINT AUTO_INCREMENT PRIMARY KEY,
    fine_id   BIGINT NOT NULL,
    amount    DECIMAL(10,2) NOT NULL,
    paid_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    method    VARCHAR(20) NOT NULL DEFAULT 'CASH',
    staff_id  BIGINT,
    notes     VARCHAR(300),
    CONSTRAINT ck_payments_amount CHECK (amount > 0),
    CONSTRAINT ck_payments_method CHECK (method IN ('CASH','TRANSFER','CARD')),
    CONSTRAINT fk_payments_fine FOREIGN KEY (fine_id) REFERENCES fines(id) ON DELETE CASCADE,
    CONSTRAINT fk_payments_staff FOREIGN KEY (staff_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_payments_fine ON payments (fine_id);

-- ----------------------------------------------------------------------------
-- 9. AUDIT LOG
-- ----------------------------------------------------------------------------

CREATE TABLE audit_logs (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT,
    action      VARCHAR(50) NOT NULL,
    table_name  VARCHAR(50) NOT NULL,
    record_id   BIGINT,
    old_data    JSON,
    new_data    JSON,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_audit_table_record ON audit_logs (table_name, record_id);
