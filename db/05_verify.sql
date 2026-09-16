-- ============================================================================
-- 05_verify.sql
-- Script kiem chung: dem so dong, kiem tra view bao cao, va test rang buoc am
-- (moi test PHAI that bai, duoc bat loi va in ra thong bao xac nhan).
-- Chay doc lap, chay lai nhieu lan khong loi.
-- ============================================================================

USE library_db;
SET NAMES utf8mb4;

-- ----------------------------------------------------------------------------
-- 1. Dem so dong tung bang
-- ----------------------------------------------------------------------------

SELECT '===== 1. SO DONG TUNG BANG =====' AS buoc;

SELECT 'roles' AS table_name, COUNT(*) AS so_dong FROM roles
UNION ALL SELECT 'users', COUNT(*) FROM users
UNION ALL SELECT 'user_roles', COUNT(*) FROM user_roles
UNION ALL SELECT 'authors', COUNT(*) FROM authors
UNION ALL SELECT 'publishers', COUNT(*) FROM publishers
UNION ALL SELECT 'categories', COUNT(*) FROM categories
UNION ALL SELECT 'books', COUNT(*) FROM books
UNION ALL SELECT 'book_authors', COUNT(*) FROM book_authors
UNION ALL SELECT 'shelves', COUNT(*) FROM shelves
UNION ALL SELECT 'book_copies', COUNT(*) FROM book_copies
UNION ALL SELECT 'readers', COUNT(*) FROM readers
UNION ALL SELECT 'library_cards', COUNT(*) FROM library_cards
UNION ALL SELECT 'loan_policies', COUNT(*) FROM loan_policies
UNION ALL SELECT 'loans', COUNT(*) FROM loans
UNION ALL SELECT 'loan_items', COUNT(*) FROM loan_items
UNION ALL SELECT 'loan_renewals', COUNT(*) FROM loan_renewals
UNION ALL SELECT 'reservations', COUNT(*) FROM reservations
UNION ALL SELECT 'fines', COUNT(*) FROM fines
UNION ALL SELECT 'payments', COUNT(*) FROM payments
UNION ALL SELECT 'audit_logs', COUNT(*) FROM audit_logs;

-- ----------------------------------------------------------------------------
-- 2. View bao cao
-- ----------------------------------------------------------------------------

SELECT '===== 2. V_OVERDUE_LOANS (phai >= 5 dong, tien phat khac 0) =====' AS buoc;
SELECT * FROM v_overdue_loans;

SELECT '===== 3. V_BOOK_AVAILABILITY (10 dong dau) =====' AS buoc;
SELECT * FROM v_book_availability LIMIT 10;

SELECT '===== 4. V_READER_DEBT =====' AS buoc;
SELECT * FROM v_reader_debt;

-- ----------------------------------------------------------------------------
-- 5. Test rang buoc am: moi test PHAI that bai
-- ----------------------------------------------------------------------------

SELECT '===== 5. TEST RANG BUOC AM =====' AS buoc;

DROP PROCEDURE IF EXISTS sp_test_negative_constraints;

DELIMITER $$

CREATE PROCEDURE sp_test_negative_constraints()
BEGIN
    -- Test 1: muon mot copy dang co nguoi muon chua tra (copy_id=6 dang ON_LOAN o loan 6)
    BEGIN
        DECLARE EXIT HANDLER FOR SQLEXCEPTION
        BEGIN
            GET DIAGNOSTICS CONDITION 1 @msg = MESSAGE_TEXT;
            SELECT 'PASS' AS ket_qua, 'Test 1: muon copy dang ON_LOAN' AS test_case, @msg AS loi_bat_duoc;
        END;
        INSERT INTO loan_items (loan_id, copy_id, due_date) VALUES (7, 6, '2026-09-30');
        SELECT 'FAIL' AS ket_qua, 'Test 1: muon copy dang ON_LOAN' AS test_case, 'KHONG bi chan - loi thiet ke!' AS loi_bat_duoc;
    END;

    -- Test 2: tao the ACTIVE thu hai cho reader da co the ACTIVE (reader_id=1 da co card id=1 ACTIVE)
    BEGIN
        DECLARE EXIT HANDLER FOR SQLEXCEPTION
        BEGIN
            GET DIAGNOSTICS CONDITION 1 @msg = MESSAGE_TEXT;
            SELECT 'PASS' AS ket_qua, 'Test 2: 2 the ACTIVE cho cung 1 doc gia' AS test_case, @msg AS loi_bat_duoc;
        END;
        INSERT INTO library_cards (reader_id, card_number, issue_date, expiry_date, status)
        VALUES (1, 'TC-9999', '2026-01-01', '2028-01-01', 'ACTIVE');
        SELECT 'FAIL' AS ket_qua, 'Test 2: 2 the ACTIVE cho cung 1 doc gia' AS test_case, 'KHONG bi chan - loi thiet ke!' AS loi_bat_duoc;
    END;

    -- Test 3: fines.amount = -1000
    BEGIN
        DECLARE EXIT HANDLER FOR SQLEXCEPTION
        BEGIN
            GET DIAGNOSTICS CONDITION 1 @msg = MESSAGE_TEXT;
            SELECT 'PASS' AS ket_qua, 'Test 3: fines.amount = -1000' AS test_case, @msg AS loi_bat_duoc;
        END;
        INSERT INTO fines (reader_id, fine_type, amount, status) VALUES (1, 'OVERDUE', -1000.00, 'UNPAID');
        SELECT 'FAIL' AS ket_qua, 'Test 3: fines.amount = -1000' AS test_case, 'KHONG bi chan - loi thiet ke!' AS loi_bat_duoc;
    END;

    -- Test 4: book_copies.status = 'INVALID'
    BEGIN
        DECLARE EXIT HANDLER FOR SQLEXCEPTION
        BEGIN
            GET DIAGNOSTICS CONDITION 1 @msg = MESSAGE_TEXT;
            SELECT 'PASS' AS ket_qua, 'Test 4: book_copies.status = INVALID' AS test_case, @msg AS loi_bat_duoc;
        END;
        INSERT INTO book_copies (book_id, barcode, status) VALUES (1, 'BC-INVALID-TEST', 'INVALID');
        SELECT 'FAIL' AS ket_qua, 'Test 4: book_copies.status = INVALID' AS test_case, 'KHONG bi chan - loi thiet ke!' AS loi_bat_duoc;
    END;

    -- Test 5: library_cards.expiry_date truoc issue_date
    BEGIN
        DECLARE EXIT HANDLER FOR SQLEXCEPTION
        BEGIN
            GET DIAGNOSTICS CONDITION 1 @msg = MESSAGE_TEXT;
            SELECT 'PASS' AS ket_qua, 'Test 5: expiry_date truoc issue_date' AS test_case, @msg AS loi_bat_duoc;
        END;
        INSERT INTO library_cards (reader_id, card_number, issue_date, expiry_date, status)
        VALUES (2, 'TC-8888', '2026-06-01', '2026-01-01', 'LOST');
        SELECT 'FAIL' AS ket_qua, 'Test 5: expiry_date truoc issue_date' AS test_case, 'KHONG bi chan - loi thiet ke!' AS loi_bat_duoc;
    END;
END$$

DELIMITER ;

CALL sp_test_negative_constraints();

DROP PROCEDURE IF EXISTS sp_test_negative_constraints;
