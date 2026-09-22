"""Sinh cap RSA 2048 cho JWT RS256 vao thu muc keys/.

Dung thu vien cryptography (da la dependency cua pyjwt[crypto]) thay vi
openssl, de khong phu thuoc vao openssl co trong PATH hay khong - tren
Windows openssl thuong chi co trong Git Bash.

    python scripts/gen_keys.py
    python scripts/gen_keys.py --force
"""

from __future__ import annotations

import argparse
import stat
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parent.parent
KEYS_DIR = ROOT / "keys"
PRIVATE = KEYS_DIR / "jwt_private.pem"
PUBLIC = KEYS_DIR / "jwt_public.pem"


def generate(force: bool) -> int:
    if (PRIVATE.exists() or PUBLIC.exists()) and not force:
        print(f"Da co key trong {KEYS_DIR}, bo qua. Dung --force de ghi de.")
        return 0

    if force and PRIVATE.exists():
        print("CANH BAO: ghi de key cu. Moi access/refresh token da phat se het hieu luc.")

    KEYS_DIR.mkdir(parents=True, exist_ok=True)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    PRIVATE.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    # Tren Windows chmod gan nhu khong co tac dung, nhung dat van dung tren
    # Linux/macOS va khong gay loi o day.
    PRIVATE.chmod(stat.S_IRUSR | stat.S_IWUSR)

    PUBLIC.write_bytes(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    print(f"Da sinh {PRIVATE.relative_to(ROOT)} va {PUBLIC.relative_to(ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Sinh cap RSA cho JWT RS256")
    parser.add_argument("--force", action="store_true", help="Ghi de key da co")
    return generate(parser.parse_args().force)


if __name__ == "__main__":
    sys.exit(main())
