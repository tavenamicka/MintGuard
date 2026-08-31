# MintGuard - Application de controle parental pour Linux Mint
# Copyright (C) 2026 Mickael Tavenart
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import hashlib
import hmac
import secrets

PBKDF2_ITERATIONS = 310_000


def hash_pin(pin: str, salt: bytes | None = None) -> str:
    """Hash un code PIN parent (PBKDF2-HMAC-SHA256). Retourne 'salt_hex:hash_hex'."""
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}:{digest.hex()}"


def verify_pin(pin: str, stored: str) -> bool:
    """Vérifie un code PIN contre une valeur hashée par hash_pin()."""
    try:
        salt_hex, digest_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, AttributeError):
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return hmac.compare_digest(candidate, expected)
