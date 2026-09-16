-- ============================================================================
-- 02_triggers.sql
-- Toan bo trigger nghiep vu (MySQL 8.0)
-- Chay doc lap, chay lai nhieu lan khong loi (DROP TRIGGER IF EXISTS truoc
-- moi CREATE TRIGGER).
-- ============================================================================

USE library_db;

DELIMITER $$

-- ----------------------------------------------------------------------------
-- (b) CHECK dung ham khong tat dinh (CURRENT_DATE) -> chuyen sang trigger
-- ----------------------------------------------------------------------------

-- ck_books_year: publish_year phai tu 1000 den nam hien tai
DROP TRIGGER IF EXISTS trg_books_year_ins$$
CREATE TRIGGER trg_books_year_ins BEFORE INSERT ON books
FOR EACH ROW
BEGIN
    IF NEW.publish_year IS NOT NULL
       AND (NEW.publish_year < 1000 OR NEW.publish_year > YEAR(CURRENT_DATE)) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'ck_books_year: publish_year phai nam trong khoang 1000..nam hien tai';
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_books_year_upd$$
CREATE TRIGGER trg_books_year_upd BEFORE UPDATE ON books
FOR EACH ROW
BEGIN
    IF NEW.publish_year IS NOT NULL
       AND (NEW.publish_year < 1000 OR NEW.publish_year > YEAR(CURRENT_DATE)) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'ck_books_year: publish_year phai nam trong khoang 1000..nam hien tai';
    END IF;
END$$

-- ck_readers_dob: ngay sinh phai truoc ngay hien tai
DROP TRIGGER IF EXISTS trg_readers_dob_ins$$
CREATE TRIGGER trg_readers_dob_ins BEFORE INSERT ON readers
FOR EACH ROW
BEGIN
    IF NEW.date_of_birth IS NOT NULL AND NEW.date_of_birth >= CURRENT_DATE THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'ck_readers_dob: ngay sinh phai truoc ngay hien tai';
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_readers_dob_upd$$
CREATE TRIGGER trg_readers_dob_upd BEFORE UPDATE ON readers
FOR EACH ROW
BEGIN
    IF NEW.date_of_birth IS NOT NULL AND NEW.date_of_birth >= CURRENT_DATE THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'ck_readers_dob: ngay sinh phai truoc ngay hien tai';
    END IF;
END$$

-- ----------------------------------------------------------------------------
-- Trigger nghiep vu muon - tra
-- ----------------------------------------------------------------------------

-- Khi them dong loan_items:
--  - Neu chua tra (returned_at NULL): dat book_copies.status = ON_LOAN
--  - Neu da tra ngay luc them (du lieu lich su/seed): dat trang thai cuoi
--    cung tuong ung (AVAILABLE/DAMAGED/LOST) va cap nhat trang thai loans
DROP TRIGGER IF EXISTS trg_items_after_insert$$
CREATE TRIGGER trg_items_after_insert AFTER INSERT ON loan_items
FOR EACH ROW
BEGIN
    DECLARE v_total INT;
    DECLARE v_returned INT;

    IF NEW.returned_at IS NULL THEN
        UPDATE book_copies
           SET status = 'ON_LOAN', updated_at = CURRENT_TIMESTAMP
         WHERE id = NEW.copy_id;
    ELSE
        IF NEW.return_condition = 'DAMAGED' THEN
            UPDATE book_copies SET status = 'DAMAGED', updated_at = CURRENT_TIMESTAMP WHERE id = NEW.copy_id;
        ELSEIF NEW.return_condition = 'LOST' THEN
            UPDATE book_copies SET status = 'LOST', updated_at = CURRENT_TIMESTAMP WHERE id = NEW.copy_id;
        ELSE
            UPDATE book_copies SET status = 'AVAILABLE', updated_at = CURRENT_TIMESTAMP WHERE id = NEW.copy_id;
        END IF;
    END IF;

    SELECT COUNT(*), SUM(CASE WHEN returned_at IS NOT NULL THEN 1 ELSE 0 END)
      INTO v_total, v_returned
      FROM loan_items
     WHERE loan_id = NEW.loan_id;

    IF v_returned >= v_total THEN
        UPDATE loans SET status = 'CLOSED', updated_at = CURRENT_TIMESTAMP WHERE id = NEW.loan_id;
    ELSEIF v_returned > 0 THEN
        UPDATE loans SET status = 'PARTIAL', updated_at = CURRENT_TIMESTAMP WHERE id = NEW.loan_id;
    END IF;
END$$

-- Khi loan_items.returned_at duoc set (tu NULL -> co gia tri):
--  - Tra book_copies.status ve AVAILABLE, hoac DAMAGED/LOST tuy return_condition
--  - Cap nhat loans.status: CLOSED neu tat ca item da tra, PARTIAL neu con dong chua tra
DROP TRIGGER IF EXISTS trg_items_after_update$$
CREATE TRIGGER trg_items_after_update AFTER UPDATE ON loan_items
FOR EACH ROW
BEGIN
    DECLARE v_total INT;
    DECLARE v_returned INT;

    IF NEW.returned_at IS NOT NULL AND OLD.returned_at IS NULL THEN
        IF NEW.return_condition = 'DAMAGED' THEN
            UPDATE book_copies SET status = 'DAMAGED', updated_at = CURRENT_TIMESTAMP WHERE id = NEW.copy_id;
        ELSEIF NEW.return_condition = 'LOST' THEN
            UPDATE book_copies SET status = 'LOST', updated_at = CURRENT_TIMESTAMP WHERE id = NEW.copy_id;
        ELSE
            UPDATE book_copies SET status = 'AVAILABLE', updated_at = CURRENT_TIMESTAMP WHERE id = NEW.copy_id;
        END IF;

        SELECT COUNT(*), SUM(CASE WHEN returned_at IS NOT NULL THEN 1 ELSE 0 END)
          INTO v_total, v_returned
          FROM loan_items
         WHERE loan_id = NEW.loan_id;

        IF v_returned >= v_total THEN
            UPDATE loans SET status = 'CLOSED', updated_at = CURRENT_TIMESTAMP WHERE id = NEW.loan_id;
        ELSE
            UPDATE loans SET status = 'PARTIAL', updated_at = CURRENT_TIMESTAMP WHERE id = NEW.loan_id;
        END IF;
    END IF;
END$$

DELIMITER ;
