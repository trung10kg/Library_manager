-- ============================================================================
-- library_schema_postgres.sql
-- Schema quan ly thu vien (PostgreSQL) - nguon de chuyen doi sang MySQL 8.0
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. PHAN QUYEN
-- ----------------------------------------------------------------------------

CREATE TABLE roles (
    id          SMALLSERIAL PRIMARY KEY,
    code        VARCHAR(30)  NOT NULL UNIQUE,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id             BIGSERIAL PRIMARY KEY,
    username       VARCHAR(50)  NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    full_name      VARCHAR(150) NOT NULL,
    email          VARCHAR(150) UNIQUE,
    phone          VARCHAR(20),
    is_active      BOOLEAN NOT NULL DEFAULT true,
    last_login_at  TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_users_email CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT ck_users_phone CHECK (phone IS NULL OR phone ~ '^[0-9+()\- ]{8,20}$')
);

CREATE TABLE user_roles (
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id     SMALLINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, role_id)
);

-- ----------------------------------------------------------------------------
-- 2. DANH MUC SACH
-- ----------------------------------------------------------------------------

CREATE TABLE authors (
    id           BIGSERIAL PRIMARY KEY,
    full_name    VARCHAR(150) NOT NULL,
    pen_name     VARCHAR(150),
    nationality  VARCHAR(100),
    birth_year   SMALLINT,
    death_year   SMALLINT,
    biography    TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_authors_years CHECK (death_year IS NULL OR birth_year IS NULL OR death_year >= birth_year)
);

CREATE INDEX idx_authors_fullname_lower ON authors (lower(full_name));

CREATE TABLE publishers (
    id         BIGSERIAL PRIMARY KEY,
    name       VARCHAR(200) NOT NULL UNIQUE,
    address    VARCHAR(300),
    phone      VARCHAR(20),
    email      VARCHAR(150),
    website    VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE categories (
    id          BIGSERIAL PRIMARY KEY,
    parent_id   BIGINT REFERENCES categories(id) ON DELETE RESTRICT,
    code        VARCHAR(30) UNIQUE,
    name        VARCHAR(150) NOT NULL,
    level       SMALLINT NOT NULL DEFAULT 1,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_categories_level CHECK (level BETWEEN 1 AND 3)
);

CREATE TABLE books (
    id               BIGSERIAL PRIMARY KEY,
    title            VARCHAR(300) NOT NULL,
    subtitle         VARCHAR(300),
    isbn13           VARCHAR(20) UNIQUE,
    category_id      BIGINT REFERENCES categories(id) ON DELETE SET NULL,
    publisher_id     BIGINT REFERENCES publishers(id) ON DELETE SET NULL,
    publish_year     SMALLINT,
    edition          VARCHAR(50),
    language         VARCHAR(50) NOT NULL DEFAULT 'vi',
    page_count       INT,
    description      TEXT,
    cover_image_url  VARCHAR(500),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_books_year CHECK (publish_year IS NULL OR publish_year BETWEEN 1000 AND EXTRACT(YEAR FROM CURRENT_DATE)::INT),
    CONSTRAINT ck_books_pages CHECK (page_count IS NULL OR page_count > 0)
);

CREATE INDEX idx_books_title_lower ON books (lower(title));
CREATE INDEX idx_books_category ON books (category_id);
CREATE INDEX idx_books_publisher ON books (publisher_id);

CREATE TABLE book_authors (
    book_id      BIGINT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    author_id    BIGINT NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    author_order SMALLINT NOT NULL DEFAULT 1,
    role         VARCHAR(20) NOT NULL DEFAULT 'AUTHOR',
    PRIMARY KEY (book_id, author_id),
    CONSTRAINT ck_book_authors_role CHECK (role IN ('AUTHOR','TRANSLATOR','EDITOR','ILLUSTRATOR'))
);

-- ----------------------------------------------------------------------------
-- 3. KHO VAT LY
-- ----------------------------------------------------------------------------

CREATE TABLE shelves (
    id         BIGSERIAL PRIMARY KEY,
    code       VARCHAR(20) NOT NULL UNIQUE,
    location   VARCHAR(200),
    capacity   INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_shelves_capacity CHECK (capacity IS NULL OR capacity > 0)
);

CREATE TABLE book_copies (
    id             BIGSERIAL PRIMARY KEY,
    book_id        BIGINT NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
    barcode        VARCHAR(50) NOT NULL UNIQUE,
    shelf_id       BIGINT REFERENCES shelves(id) ON DELETE SET NULL,
    status         VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE',
    condition_note VARCHAR(300),
    acquired_date  DATE NOT NULL DEFAULT CURRENT_DATE,
    price          NUMERIC(12,2),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_copies_status CHECK (status IN ('AVAILABLE','ON_LOAN','RESERVED','DAMAGED','LOST','WITHDRAWN')),
    CONSTRAINT ck_copies_price CHECK (price IS NULL OR price >= 0)
);

CREATE INDEX idx_copies_book ON book_copies (book_id);
CREATE INDEX idx_copies_status ON book_copies (status);

-- ----------------------------------------------------------------------------
-- 4. BAN DOC
-- ----------------------------------------------------------------------------

CREATE TABLE readers (
    id             BIGSERIAL PRIMARY KEY,
    full_name      VARCHAR(150) NOT NULL,
    date_of_birth  DATE,
    gender         VARCHAR(10),
    id_number      VARCHAR(30) UNIQUE,
    address        VARCHAR(300),
    phone          VARCHAR(20),
    email          VARCHAR(150),
    reader_type    VARCHAR(20) NOT NULL DEFAULT 'STUDENT',
    user_id        BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_readers_dob CHECK (date_of_birth IS NULL OR date_of_birth < CURRENT_DATE),
    CONSTRAINT ck_readers_gender CHECK (gender IS NULL OR gender IN ('MALE','FEMALE','OTHER')),
    CONSTRAINT ck_readers_type CHECK (reader_type IN ('STUDENT','TEACHER','STAFF','PUBLIC')),
    CONSTRAINT ck_readers_phone CHECK (phone IS NULL OR phone ~ '^[0-9+()\- ]{8,20}$')
);

CREATE INDEX idx_readers_fullname_lower ON readers (lower(full_name));

CREATE TABLE library_cards (
    id           BIGSERIAL PRIMARY KEY,
    reader_id    BIGINT NOT NULL REFERENCES readers(id) ON DELETE RESTRICT,
    card_number  VARCHAR(30) NOT NULL UNIQUE,
    issue_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    expiry_date  DATE NOT NULL,
    status       VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    notes        VARCHAR(300),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_cards_status CHECK (status IN ('ACTIVE','EXPIRED','LOCKED','LOST')),
    CONSTRAINT ck_cards_expiry CHECK (expiry_date > issue_date)
);

-- Mot ban doc chi co toi da 1 the ACTIVE
CREATE UNIQUE INDEX ux_cards_one_active ON library_cards (reader_id) WHERE status = 'ACTIVE';
CREATE INDEX idx_cards_reader ON library_cards (reader_id);

-- ----------------------------------------------------------------------------
-- 5. CHINH SACH MUON TRA
-- ----------------------------------------------------------------------------

CREATE TABLE loan_policies (
    id                   SMALLSERIAL PRIMARY KEY,
    code                 VARCHAR(30) NOT NULL UNIQUE,
    reader_type          VARCHAR(20) NOT NULL UNIQUE,
    max_loan_items       SMALLINT NOT NULL,
    loan_period_days     SMALLINT NOT NULL,
    max_renewals         SMALLINT NOT NULL DEFAULT 1,
    renewal_period_days  SMALLINT NOT NULL,
    fine_per_day         NUMERIC(10,2) NOT NULL,
    max_reservations     SMALLINT NOT NULL DEFAULT 3,
    is_active            BOOLEAN NOT NULL DEFAULT true,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_policies_reader_type CHECK (reader_type IN ('STUDENT','TEACHER','STAFF','PUBLIC')),
    CONSTRAINT ck_policies_max_items CHECK (max_loan_items > 0),
    CONSTRAINT ck_policies_period CHECK (loan_period_days > 0),
    CONSTRAINT ck_policies_renewals CHECK (max_renewals >= 0),
    CONSTRAINT ck_policies_renewal_period CHECK (renewal_period_days > 0),
    CONSTRAINT ck_policies_fine CHECK (fine_per_day >= 0),
    CONSTRAINT ck_policies_max_res CHECK (max_reservations >= 0)
);

-- ----------------------------------------------------------------------------
-- 6. MUON - TRA
-- ----------------------------------------------------------------------------

CREATE TABLE loans (
    id               BIGSERIAL PRIMARY KEY,
    reader_id        BIGINT NOT NULL REFERENCES readers(id) ON DELETE RESTRICT,
    library_card_id  BIGINT NOT NULL REFERENCES library_cards(id) ON DELETE RESTRICT,
    policy_id        SMALLINT NOT NULL REFERENCES loan_policies(id) ON DELETE RESTRICT,
    staff_id         BIGINT REFERENCES users(id) ON DELETE SET NULL,
    loan_date        DATE NOT NULL DEFAULT CURRENT_DATE,
    status           VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    notes            VARCHAR(300),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_loans_status CHECK (status IN ('OPEN','PARTIAL','CLOSED','CANCELLED'))
);

CREATE INDEX idx_loans_reader ON loans (reader_id);
CREATE INDEX idx_loans_status ON loans (status);

CREATE TABLE loan_items (
    id                BIGSERIAL PRIMARY KEY,
    loan_id           BIGINT NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    copy_id           BIGINT NOT NULL REFERENCES book_copies(id) ON DELETE RESTRICT,
    due_date          DATE NOT NULL,
    returned_at       TIMESTAMPTZ,
    return_condition  VARCHAR(20),
    notes             VARCHAR(300),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_items_return_cond CHECK (return_condition IS NULL OR return_condition IN ('GOOD','DAMAGED','LOST'))
);

-- Mot ban sao khong the nam o 2 phieu muon chua tra cung luc
CREATE UNIQUE INDEX ux_items_open_copy ON loan_items (copy_id) WHERE returned_at IS NULL;
-- Ho tro truy van cac dong chua tra theo han
CREATE INDEX idx_items_due ON loan_items (due_date) WHERE returned_at IS NULL;
CREATE INDEX idx_items_loan ON loan_items (loan_id);

CREATE TABLE loan_renewals (
    id             BIGSERIAL PRIMARY KEY,
    loan_item_id   BIGINT NOT NULL REFERENCES loan_items(id) ON DELETE CASCADE,
    old_due_date   DATE NOT NULL,
    new_due_date   DATE NOT NULL,
    renewed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    staff_id       BIGINT REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT ck_renewals_dates CHECK (new_due_date > old_due_date)
);

-- ----------------------------------------------------------------------------
-- 7. DAT CHO
-- ----------------------------------------------------------------------------

CREATE TABLE reservations (
    id           BIGSERIAL PRIMARY KEY,
    reader_id    BIGINT NOT NULL REFERENCES readers(id) ON DELETE RESTRICT,
    book_id      BIGINT NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
    reserved_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    status       VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    expires_at   TIMESTAMPTZ,
    notes        VARCHAR(300),
    CONSTRAINT ck_reservations_status CHECK (status IN ('PENDING','READY','FULFILLED','CANCELLED','EXPIRED'))
);

-- Mot ban doc khong dat trung cung dau sach khi phieu cu con PENDING/READY
CREATE UNIQUE INDEX ux_reservations_active ON reservations (reader_id, book_id) WHERE status IN ('PENDING','READY');
CREATE INDEX idx_reservations_book ON reservations (book_id);

-- ----------------------------------------------------------------------------
-- 8. PHAT
-- ----------------------------------------------------------------------------

CREATE TABLE fines (
    id            BIGSERIAL PRIMARY KEY,
    loan_item_id  BIGINT REFERENCES loan_items(id) ON DELETE SET NULL,
    reader_id     BIGINT NOT NULL REFERENCES readers(id) ON DELETE RESTRICT,
    fine_type     VARCHAR(20) NOT NULL,
    amount        NUMERIC(10,2) NOT NULL,
    status        VARCHAR(20) NOT NULL DEFAULT 'UNPAID',
    issued_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    notes         VARCHAR(300),
    CONSTRAINT ck_fines_type CHECK (fine_type IN ('OVERDUE','DAMAGE','LOST')),
    CONSTRAINT ck_fines_amount CHECK (amount >= 0),
    CONSTRAINT ck_fines_status CHECK (status IN ('UNPAID','PARTIAL','PAID','WAIVED'))
);

CREATE INDEX idx_fines_reader ON fines (reader_id);
CREATE INDEX idx_fines_status ON fines (status);

CREATE TABLE payments (
    id        BIGSERIAL PRIMARY KEY,
    fine_id   BIGINT NOT NULL REFERENCES fines(id) ON DELETE CASCADE,
    amount    NUMERIC(10,2) NOT NULL,
    paid_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    method    VARCHAR(20) NOT NULL DEFAULT 'CASH',
    staff_id  BIGINT REFERENCES users(id) ON DELETE SET NULL,
    notes     VARCHAR(300),
    CONSTRAINT ck_payments_amount CHECK (amount > 0),
    CONSTRAINT ck_payments_method CHECK (method IN ('CASH','TRANSFER','CARD'))
);

CREATE INDEX idx_payments_fine ON payments (fine_id);

-- ----------------------------------------------------------------------------
-- 9. AUDIT LOG
-- ----------------------------------------------------------------------------

CREATE TABLE audit_logs (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT REFERENCES users(id) ON DELETE SET NULL,
    action      VARCHAR(50) NOT NULL,
    table_name  VARCHAR(50) NOT NULL,
    record_id   BIGINT,
    old_data    JSONB,
    new_data    JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_table_record ON audit_logs (table_name, record_id);

-- ----------------------------------------------------------------------------
-- 10. VIEW BAO CAO
-- ----------------------------------------------------------------------------

-- Tinh trang san co cua tung dau sach
CREATE VIEW v_book_availability AS
SELECT
    b.id AS book_id,
    b.title,
    COUNT(bc.id) AS total_copies,
    COUNT(*) FILTER (WHERE bc.status = 'AVAILABLE') AS available_copies,
    COUNT(*) FILTER (WHERE bc.status = 'ON_LOAN')   AS on_loan_copies,
    COUNT(*) FILTER (WHERE bc.status = 'DAMAGED')   AS damaged_copies,
    COUNT(*) FILTER (WHERE bc.status = 'LOST')      AS lost_copies,
    (SELECT COUNT(*) FROM reservations r
      WHERE r.book_id = b.id AND r.status IN ('PENDING','READY')) AS active_reservations
FROM books b
LEFT JOIN book_copies bc ON bc.book_id = b.id
GROUP BY b.id, b.title;

-- Danh sach phieu muon qua han, kem so ngay tre va tien phat uoc tinh
CREATE VIEW v_overdue_loans AS
SELECT
    li.id AS loan_item_id,
    l.id  AS loan_id,
    r.id  AS reader_id,
    r.full_name AS reader_name,
    b.id  AS book_id,
    b.title,
    bc.barcode,
    li.due_date,
    (CURRENT_DATE - li.due_date) AS days_overdue,
    ((CURRENT_DATE - li.due_date) * lp.fine_per_day) AS estimated_fine
FROM loan_items li
JOIN loans l          ON l.id = li.loan_id
JOIN readers r         ON r.id = l.reader_id
JOIN loan_policies lp  ON lp.id = l.policy_id
JOIN book_copies bc    ON bc.id = li.copy_id
JOIN books b           ON b.id = bc.book_id
WHERE li.returned_at IS NULL
  AND li.due_date < CURRENT_DATE;

-- Cong no phat cua tung ban doc (dung de chan muon tiep)
CREATE VIEW v_reader_debt AS
SELECT
    r.id AS reader_id,
    r.full_name,
    COALESCE(SUM(f.amount), 0)         AS total_fine_amount,
    COALESCE(SUM(p.paid_total), 0)     AS total_paid,
    COALESCE(SUM(f.amount), 0) - COALESCE(SUM(p.paid_total), 0) AS outstanding_debt,
    COUNT(*) FILTER (WHERE f.status IN ('UNPAID','PARTIAL')) AS unpaid_fine_count
FROM readers r
JOIN fines f ON f.reader_id = r.id
LEFT JOIN LATERAL (
    SELECT SUM(pay.amount) AS paid_total
    FROM payments pay
    WHERE pay.fine_id = f.id
) p ON true
GROUP BY r.id, r.full_name
HAVING COALESCE(SUM(f.amount), 0) - COALESCE(SUM(p.paid_total), 0) > 0;
