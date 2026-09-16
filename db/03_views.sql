-- ============================================================================
-- 03_views.sql
-- 3 view bao cao (MySQL 8.0)
-- Chay doc lap, chay lai nhieu lan khong loi (CREATE OR REPLACE VIEW).
-- ============================================================================

USE library_db;

-- Tinh trang san co cua tung dau sach.
-- COUNT(*) FILTER (WHERE ...) cua Postgres -> SUM(CASE WHEN ... THEN 1 ELSE 0 END)
CREATE OR REPLACE VIEW v_book_availability AS
SELECT
    b.id AS book_id,
    b.title,
    COUNT(bc.id) AS total_copies,
    SUM(CASE WHEN bc.status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available_copies,
    SUM(CASE WHEN bc.status = 'ON_LOAN'   THEN 1 ELSE 0 END) AS on_loan_copies,
    SUM(CASE WHEN bc.status = 'DAMAGED'   THEN 1 ELSE 0 END) AS damaged_copies,
    SUM(CASE WHEN bc.status = 'LOST'      THEN 1 ELSE 0 END) AS lost_copies,
    (SELECT COUNT(*) FROM reservations r
      WHERE r.book_id = b.id AND r.status IN ('PENDING','READY')) AS active_reservations
FROM books b
LEFT JOIN book_copies bc ON bc.book_id = b.id
GROUP BY b.id, b.title;

-- Danh sach phieu muon qua han, kem so ngay tre va tien phat uoc tinh.
-- CURRENT_DATE - due_date cua Postgres -> DATEDIFF(CURRENT_DATE, due_date)
CREATE OR REPLACE VIEW v_overdue_loans AS
SELECT
    li.id AS loan_item_id,
    l.id  AS loan_id,
    r.id  AS reader_id,
    r.full_name AS reader_name,
    b.id  AS book_id,
    b.title,
    bc.barcode,
    li.due_date,
    DATEDIFF(CURRENT_DATE, li.due_date) AS days_overdue,
    (DATEDIFF(CURRENT_DATE, li.due_date) * lp.fine_per_day) AS estimated_fine
FROM loan_items li
JOIN loans l          ON l.id = li.loan_id
JOIN readers r         ON r.id = l.reader_id
JOIN loan_policies lp  ON lp.id = l.policy_id
JOIN book_copies bc    ON bc.id = li.copy_id
JOIN books b           ON b.id = bc.book_id
WHERE li.returned_at IS NULL
  AND li.due_date < CURRENT_DATE;

-- Cong no phat cua tung ban doc (dung de chan muon tiep).
-- LEFT JOIN LATERAL cua Postgres -> derived table (subquery) gom nhom san
-- theo fine_id roi JOIN thuong, vi khong can tuong quan tung dong ngoai fine_id.
CREATE OR REPLACE VIEW v_reader_debt AS
SELECT
    r.id AS reader_id,
    r.full_name,
    COALESCE(SUM(f.amount), 0)     AS total_fine_amount,
    COALESCE(SUM(p.paid_total), 0) AS total_paid,
    COALESCE(SUM(f.amount), 0) - COALESCE(SUM(p.paid_total), 0) AS outstanding_debt,
    SUM(CASE WHEN f.status IN ('UNPAID','PARTIAL') THEN 1 ELSE 0 END) AS unpaid_fine_count
FROM readers r
JOIN fines f ON f.reader_id = r.id
LEFT JOIN (
    SELECT fine_id, SUM(amount) AS paid_total
    FROM payments
    GROUP BY fine_id
) p ON p.fine_id = f.id
GROUP BY r.id, r.full_name
HAVING COALESCE(SUM(f.amount), 0) - COALESCE(SUM(p.paid_total), 0) > 0;
