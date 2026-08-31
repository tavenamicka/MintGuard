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

from mintguard.gui.styles import COLORS, build_stylesheet


def test_stylesheet_contains_primary_color():
    css = build_stylesheet()
    assert COLORS["primary"] in css


def test_stylesheet_defines_heading_classes():
    css = build_stylesheet()
    for selector in ("QLabel#h1", "QLabel#h2", "QLabel#h3", "QPushButton", "QProgressBar"):
        assert selector in css
