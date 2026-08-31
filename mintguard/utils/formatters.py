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

from datetime import timedelta

DAY_KEYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def weekday_key(day_index: int) -> str:
    """Clé i18n 'time.<jour>' pour un index de jour SQLAlchemy/datetime.weekday() (0=lundi)."""
    return DAY_KEYS[day_index]


def format_duration(seconds: int) -> str:
    """Formate une durée en secondes en 'Xh YYmin' (ex: 1h 45min)."""
    total_minutes = max(0, seconds) // 60
    hours, minutes = divmod(total_minutes, 60)
    if hours and minutes:
        return f"{hours}h {minutes:02d}min"
    if hours:
        return f"{hours}h"
    return f"{minutes}min"


def format_percentage(used: int, total: int) -> int:
    """Calcule un pourcentage borné entre 0 et 100."""
    if total <= 0:
        return 0
    return max(0, min(100, round((used / total) * 100)))


def timedelta_to_hm(delta: timedelta) -> str:
    return format_duration(int(delta.total_seconds()))
