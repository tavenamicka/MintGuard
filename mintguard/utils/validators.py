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

import re

DOMAIN_RE = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$"
)
TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def is_valid_domain(domain: str) -> bool:
    return bool(domain) and bool(DOMAIN_RE.match(domain.strip().lower()))


def is_valid_time_string(value: str) -> bool:
    return bool(TIME_RE.match(value))


def is_valid_pin(pin: str) -> bool:
    """Code de sécurité parent: 4 à 8 chiffres."""
    return bool(re.fullmatch(r"\d{4,8}", pin))
