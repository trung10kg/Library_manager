#!/usr/bin/env python3
"""task.py - dieu phoi dev cho library-system.

Thay cho Makefile. Chay giong nhau o PowerShell va Git Bash, chi can Python
3.12 - khong can make, uv hay openssl.

    python task.py setup        # tao .venv va cai dependency
    python task.py keys         # sinh cap RSA cho JWT
    python task.py test         # chay pytest cho libs/common va 5 service
    python task.py --help

MySQL KHONG chay trong Docker: dung ban cai san tren may (127.0.0.1:3306).
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
IS_WIN = os.name == "nt"

# Ten service -> cong khi chay tren host. Prefix gateway suy ra tu ten.
SERVICES: dict[str, int] = {
    "auth-service": 8001,
    "catalog-service": 8002,
    "reader-service": 8003,
    "circulation-service": 8004,
    "billing-service": 8005,
}

# Prefix duoi gateway, dung cho lenh smoke.
PREFIXES = {
    "auth-service": "auth",
    "catalog-service": "catalog",
    "reader-service": "readers",
    "circulation-service": "circulation",
    "billing-service": "billing",
}

# Thu tu nap schema. 05_verify.sql co y chay cac cau lenh vi pham rang buoc
# de kiem tra, nen khong nam trong danh sach nay.
SCHEMA_FILES = [
    "01_schema_mysql.sql",
    "02_triggers.sql",
    "03_views.sql",
    "04_seed.sql",
]

MYSQL_FALLBACK = Path(r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe")


# --------------------------------------------------------------------------
# Tien ich
# --------------------------------------------------------------------------


def fail(msg: str) -> NoReturn:  # type: ignore[name-defined]  # noqa: F821
    print(f"LOI: {msg}", file=sys.stderr)
    sys.exit(1)


def venv_python() -> Path:
    p = VENV / ("Scripts/python.exe" if IS_WIN else "bin/python")
    if not p.exists():
        fail("Chua co .venv. Chay truoc: python task.py setup")
    return p


def load_env() -> dict[str, str]:
    """Doc .env; neu chua co thi tao tu .env.example."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        example = ROOT / ".env.example"
        if not example.exists():
            fail("Thieu ca .env va .env.example")
        shutil.copyfile(example, env_file)
        print("Da tao .env tu .env.example")

    values: dict[str, str] = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip()
    return values


def database_url(env: dict[str, str], db_name: str | None = None) -> str:
    return (
        f"mysql+aiomysql://{env['MYSQL_USER']}:{quote(env['MYSQL_PASSWORD'])}"
        f"@{env['MYSQL_HOST']}:{env['MYSQL_PORT']}"
        f"/{db_name or env['MYSQL_DB']}?charset=utf8mb4"
    )


def mysql_tool(name: str) -> str:
    """Tim mysql / mysqldump: trong PATH, hoac canh ban cai mac dinh."""
    found = shutil.which(name)
    if found:
        return found
    fallback = MYSQL_FALLBACK.with_name(f"{name}.exe")
    if fallback.exists():
        return str(fallback)
    fail(f"Khong tim thay '{name}'. Them thu muc bin cua MySQL vao PATH.")


def mysql_client() -> str:
    return mysql_tool("mysql")


def mysql_auth(env: dict[str, str]) -> list[str]:
    return [
        f"-h{env['MYSQL_HOST']}",
        f"-P{env['MYSQL_PORT']}",
        f"-u{env['MYSQL_USER']}",
        f"-p{env['MYSQL_PASSWORD']}",
        "--default-character-set=utf8mb4",
    ]


def run_sql_file(path: Path, env: dict[str, str], db: str | None = None) -> None:
    cmd = [mysql_client(), *mysql_auth(env)]
    if db:
        cmd.append(db)
    print(f">>> {path.name}")
    with path.open("rb") as fh:
        rc = subprocess.call(cmd, stdin=fh, cwd=ROOT)
    if rc != 0:
        fail(f"Chay {path.name} that bai (ma {rc})")


# --------------------------------------------------------------------------
# Lenh
# --------------------------------------------------------------------------


def cmd_setup(args: argparse.Namespace) -> int:
    if not VENV.exists():
        print("Tao .venv ...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
    py = VENV / ("Scripts/python.exe" if IS_WIN else "bin/python")
    subprocess.check_call([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call(
        [str(py), "-m", "pip", "install", "-r", str(ROOT / "requirements-dev.txt")]
    )
    load_env()
    print("\nXong. Tiep theo: python task.py keys")
    return 0


def cmd_keys(args: argparse.Namespace) -> int:
    cmd = [str(venv_python()), str(ROOT / "scripts" / "gen_keys.py")]
    if args.force:
        cmd.append("--force")
    return subprocess.call(cmd, cwd=ROOT)


def _targets(svc: str | None) -> list[Path]:
    if svc:
        name = svc if svc.endswith("-service") or svc == "common" else f"{svc}-service"
        if name == "common":
            return [ROOT / "libs" / "common"]
        if name not in SERVICES:
            fail(f"Khong biet service '{svc}'. Chon: common, {', '.join(SERVICES)}")
        return [ROOT / "services" / name]
    return [ROOT / "libs" / "common"] + [ROOT / "services" / s for s in SERVICES]


def cmd_test(args: argparse.Namespace) -> int:
    env = load_env()
    py = venv_python()
    base = dict(os.environ)
    base.update(
        {
            "DATABASE_URL": database_url(env, env["MYSQL_TEST_DB"]),
            "MYSQL_TEST_DB": env["MYSQL_TEST_DB"],
            "SCHEMA_DIR": str(ROOT / "db"),
            "LOG_LEVEL": "WARNING",
        }
    )
    failed: list[str] = []
    for path in _targets(args.service):
        if not (path / "tests").exists():
            print(f"-- bo qua {path.name}: chua co tests/")
            continue
        print(f"\n=== {path.relative_to(ROOT)}")
        rc = subprocess.call([str(py), "-m", "pytest", "-q"], cwd=path, env=base)
        if rc != 0:
            failed.append(path.name)
    if failed:
        fail(f"Test that bai: {', '.join(failed)}")
    print("\nTat ca test xanh.")
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    py = venv_python()
    rc = subprocess.call([str(py), "-m", "ruff", "check", "."], cwd=ROOT)
    rc |= subprocess.call([str(py), "-m", "ruff", "format", "--check", "."], cwd=ROOT)
    return rc


def cmd_fmt(args: argparse.Namespace) -> int:
    py = venv_python()
    subprocess.call([str(py), "-m", "ruff", "check", "--fix", "."], cwd=ROOT)
    return subprocess.call([str(py), "-m", "ruff", "format", "."], cwd=ROOT)


def cmd_db_verify(args: argparse.Namespace) -> int:
    env = load_env()
    run_sql_file(ROOT / "db" / "05_verify.sql", env)
    return 0


def cmd_db_cli(args: argparse.Namespace) -> int:
    env = load_env()
    return subprocess.call(
        [
            mysql_client(),
            f"-h{env['MYSQL_HOST']}",
            f"-P{env['MYSQL_PORT']}",
            f"-u{env['MYSQL_USER']}",
            f"-p{env['MYSQL_PASSWORD']}",
            "--default-character-set=utf8mb4",
            env["MYSQL_DB"],
        ]
    )


def cmd_db_reset(args: argparse.Namespace) -> int:
    env = load_env()
    db = env["MYSQL_DB"]
    if not args.yes_wipe_library_db:
        print(
            f"CHAN: lenh nay chay db/01_schema_mysql.sql, bat dau bang\n"
            f"  DROP DATABASE IF EXISTS {db};\n"
            f"Toan bo du lieu hien co trong {db} se mat.\n\n"
            f"Neu that su muon, chay lai voi: --yes-wipe-library-db"
        )
        return 1
    for name in SCHEMA_FILES:
        run_sql_file(ROOT / "db" / name, env)
    print(f"\nDa dung lai {db} tu db/*.sql.")
    return 0


# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python task.py",
        description="Dieu phoi dev cho library-system.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="<lenh>")

    def add(name: str, func, help_: str) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help_)
        p.set_defaults(func=func)
        return p

    add("setup", cmd_setup, "Tao .venv va cai dependency")
    add("keys", cmd_keys, "Sinh cap RSA cho JWT").add_argument(
        "--force", action="store_true", help="Ghi de key da co"
    )
    add("test", cmd_test, "Chay pytest").add_argument(
        "service", nargs="?", help="common hoac ten service, bo trong de chay het"
    )
    add("lint", cmd_lint, "ruff check + format --check")
    add("fmt", cmd_fmt, "ruff format")
    add("db-verify", cmd_db_verify, "Chay db/05_verify.sql tren MySQL local")
    add("db-cli", cmd_db_cli, "Mo mysql client vao library_db")
    add("db-reset", cmd_db_reset, "NAP LAI schema - XOA du lieu hien co").add_argument(
        "--yes-wipe-library-db", action="store_true", help="Xac nhan xoa du lieu"
    )
    return parser


def main() -> int:
    if IS_WIN:
        signal.signal(signal.SIGINT, signal.default_int_handler)
    args = build_parser().parse_args()
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
