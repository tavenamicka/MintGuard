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

from mintguard.utils.formatters import format_duration, format_percentage


def test_format_duration_hours_and_minutes():
    assert format_duration(6300) == "1h 45min"  # 1h45


def test_format_duration_hours_only():
    assert format_duration(7200) == "2h"


def test_format_duration_minutes_only():
    assert format_duration(300) == "5min"


def test_format_duration_zero():
    assert format_duration(0) == "0min"


def test_format_percentage_normal():
    assert format_percentage(105, 180) == 58  # 1h45 / 3h


def test_format_percentage_over_limit_clamped():
    assert format_percentage(400, 180) == 100


def test_format_percentage_zero_total():
    assert format_percentage(10, 0) == 0
