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

from mintguard.utils.security import hash_pin, verify_pin
from mintguard.utils.validators import is_valid_domain, is_valid_pin, is_valid_time_string


def test_hash_pin_is_not_plaintext():
    stored = hash_pin("1234")
    assert "1234" not in stored
    assert ":" in stored


def test_verify_correct_pin():
    stored = hash_pin("1234")
    assert verify_pin("1234", stored) is True


def test_verify_incorrect_pin():
    stored = hash_pin("1234")
    assert verify_pin("0000", stored) is False


def test_hash_pin_uses_random_salt():
    assert hash_pin("1234") != hash_pin("1234")


def test_valid_domain():
    assert is_valid_domain("tiktok.com") is True
    assert is_valid_domain("sub.example.co.uk") is True


def test_invalid_domain():
    assert is_valid_domain("not a domain") is False
    assert is_valid_domain("") is False
    assert is_valid_domain("-bad.com") is False


def test_valid_time_string():
    assert is_valid_time_string("16:00") is True
    assert is_valid_time_string("23:59") is True


def test_invalid_time_string():
    assert is_valid_time_string("25:00") is False
    assert is_valid_time_string("16h00") is False


def test_valid_pin():
    assert is_valid_pin("1234") is True
    assert is_valid_pin("12345678") is True


def test_invalid_pin():
    assert is_valid_pin("123") is False
    assert is_valid_pin("abcd") is False
