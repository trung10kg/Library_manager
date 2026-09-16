#!/usr/bin/env bash
# reset.sh - Drop & dung lai toan bo database library_db tu dau.
#
# Doc thong tin ket noi tu bien moi truong (khong hardcode password):
#   DB_HOST (mac dinh 127.0.0.1)
#   DB_PORT (mac dinh 3306)
#   DB_USER (mac dinh root)
#   DB_PASS (mac dinh 1234)
#   DB_NAME (mac dinh library_db - luu y: 01_schema_mysql.sql dang hardcode
#            ten database "library_db" trong cau lenh CREATE DATABASE, dung
#            dung theo dung moi truong da mo ta trong prompt. Neu doi DB_NAME
#            sang gia tri khac, phai sua lai CREATE DATABASE trong
#            01_schema_mysql.sql cho khop.)
#
# Vi du:
#   DB_USER=root DB_PASS=matkhau_cua_ban ./reset.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-root}"
DB_PASS="${DB_PASS:-1234}"
DB_NAME="${DB_NAME:-library_db}"

if command -v mysql >/dev/null 2>&1; then
    MYSQL_BIN="mysql"
elif [ -x "/c/Program Files/MySQL/MySQL Server 8.0/bin/mysql.exe" ]; then
    MYSQL_BIN="/c/Program Files/MySQL/MySQL Server 8.0/bin/mysql.exe"
else
    echo "Khong tim thay client 'mysql'. Them mysql vao PATH hoac sua bien MYSQL_BIN trong reset.sh." >&2
    exit 1
fi

run_sql() {
    local file="$1"
    echo ">>> Dang chay $(basename "$file") ..."
    "$MYSQL_BIN" -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" --default-character-set=utf8mb4 < "$file"
}

echo "=== RESET DATABASE '$DB_NAME' tren $DB_HOST:$DB_PORT (user: $DB_USER) ==="

run_sql "$SCRIPT_DIR/01_schema_mysql.sql"
run_sql "$SCRIPT_DIR/02_triggers.sql"
run_sql "$SCRIPT_DIR/03_views.sql"
run_sql "$SCRIPT_DIR/04_seed.sql"
run_sql "$SCRIPT_DIR/05_verify.sql"

echo "=== HOAN TAT ==="
