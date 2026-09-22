"""Canh gac ranh gioi du lieu giua 5 service.

Ca 5 service noi vao mot database duy nhat, nen khong co gi o tang DB ngan
circulation-service query thang bang `books`. Ranh gioi chi la quy uoc - va
test nay la thu duy nhat thuc thi no.

Test doc file bang AST/regex chu khong import: 5 service deu co package ten
`app`, import ca 5 trong cung mot tien trinh se dam nhau.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from common.testing import SCHEMA_FILES

ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = ROOT / "services"
DB_DIR = ROOT / "db"

# Bang nao thuoc service nao. Sua o day khi doi ranh gioi - co y de viec do
# phai la mot quyet dinh tuong minh.
OWNERSHIP: dict[str, set[str]] = {
    "auth-service": {
        "users",
        "roles",
        "user_roles",
        "audit_logs",
        "refresh_tokens",
    },
    "catalog-service": {
        "books",
        "authors",
        "book_authors",
        "publishers",
        "categories",
        "shelves",
        "book_copies",
    },
    "reader-service": {
        "readers",
        "library_cards",
    },
    "circulation-service": {
        "loans",
        "loan_items",
        "loan_renewals",
        "reservations",
        "loan_policies",
        "processed_events",
    },
    "billing-service": {
        "fines",
        "payments",
        "processed_events",
    },
}

# Bang duoc phep xuat hien o nhieu service. processed_events dung khoa chinh
# ghep (consumer, event_id) nen circulation va billing khong dam nhau.
SHARED_TABLES = {"processed_events"}

# Bang se them o phase sau, chua co trong db/*.sql.
PLANNED_TABLES = {"refresh_tokens", "processed_events"}

# Ngoai le DOC cheo da duoc duyet: (service, bang, file duy nhat duoc cham).
# Moi ngoai le phai kem ly do ngay tren dong cua no.
ALLOWED_CROSS_READS: set[tuple[str, str, str]] = set()

ALL_TABLES = set().union(*OWNERSHIP.values())

# SQL tho trong text(...): tu khoa viet hoa theo sau la ten bang.
RAW_SQL_TABLE = re.compile(r"\b(?:FROM|JOIN|INTO|UPDATE)\s+`?([a-z_]+)`?")


def declared_tables(service: str) -> dict[str, Path]:
    """Ten bang -> file khai bao, doc tu services/<svc>/app/models/.

    Bat ca `__tablename__ = "..."` lan `Table("...", ...)` (bang noi).
    """
    models_dir = SERVICES_DIR / service / "app" / "models"
    found: dict[str, Path] = {}
    if not models_dir.is_dir():
        return found

    for path in sorted(models_dir.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                is_tablename = any(
                    isinstance(t, ast.Name) and t.id == "__tablename__" for t in node.targets
                )
                if (
                    is_tablename
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    found[node.value.value] = path
            elif isinstance(node, ast.Call):
                func = node.func
                name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
                if (
                    name == "Table"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    found[node.args[0].value] = path
    return found


@pytest.mark.parametrize("service", sorted(OWNERSHIP))
def test_service_chi_khai_bao_bang_no_so_huu(service: str):
    allowed = OWNERSHIP[service]
    for table, path in declared_tables(service).items():
        assert table in allowed, (
            f"{path.relative_to(ROOT)} khai bao bang '{table}' khong thuoc {service}.\n"
            f"Muon du lieu cua service khac thi goi API cua no, dung query thang."
        )


@pytest.mark.parametrize("service", sorted(OWNERSHIP))
def test_sql_tho_chi_cham_bang_so_huu(service: str):
    app_dir = SERVICES_DIR / service / "app"
    if not app_dir.is_dir():
        return
    for path in sorted(app_dir.rglob("*.py")):
        rel = path.relative_to(SERVICES_DIR / service).as_posix()
        for table in RAW_SQL_TABLE.findall(path.read_text(encoding="utf-8")):
            if table not in ALL_TABLES or table in OWNERSHIP[service]:
                continue
            assert (service, table, rel) in ALLOWED_CROSS_READS, (
                f"services/{service}/{rel} cham bang '{table}' cua service khac.\n"
                f"Goi API cua service so huu, hoac them ngoai le co ly do vao "
                f"ALLOWED_CROSS_READS."
            )


def test_ngoai_le_doc_cheo_van_con_can_thiet():
    """Ngoai le khong con dung toi thi phai xoa, khong de treo."""
    for service, table, rel in ALLOWED_CROSS_READS:
        path = SERVICES_DIR / service / rel
        assert path.exists(), f"Ngoai le tro toi file khong ton tai: {service}/{rel}"
        assert table in RAW_SQL_TABLE.findall(path.read_text(encoding="utf-8")), (
            f"{service}/{rel} khong con cham '{table}' - xoa ngoai le nay."
        )


def test_khong_co_bang_nao_bi_hai_service_cung_khai_bao():
    owner_of: dict[str, str] = {}
    for service, tables in OWNERSHIP.items():
        for table in tables:
            if table in SHARED_TABLES:
                continue
            assert table not in owner_of, (
                f"Bang '{table}' duoc gan cho ca {owner_of[table]} va {service}."
            )
            owner_of[table] = service


def test_map_phu_het_cac_bang_trong_schema():
    """Them bang moi vao db/*.sql ma quen gan chu so huu thi test nay do."""
    if not DB_DIR.is_dir():
        pytest.skip("Khong tim thay thu muc db/")

    files = [DB_DIR / name for name in SCHEMA_FILES]
    in_schema: set[str] = set()
    for path in files:
        sql = path.read_text(encoding="utf-8")
        in_schema |= set(
            re.findall(r"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?`?(\w+)`?", sql, flags=re.IGNORECASE)
        )
    assert in_schema, "Khong doc duoc bang nao tu schema"

    assert in_schema - ALL_TABLES == set(), "Bang co trong schema nhung chua co chu so huu"
    assert ALL_TABLES - in_schema == PLANNED_TABLES, "Map co bang khong ton tai trong schema"
