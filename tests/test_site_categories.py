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

from mintguard.backend.site_categories import AGE_PRESETS, CATEGORIES, category_for_domain


def test_category_for_known_domain():
    assert category_for_domain("tiktok.com") == "social"
    assert category_for_domain("steampowered.com") == "gaming"


def test_category_for_unknown_domain():
    assert category_for_domain("example.com") == "custom"


def test_age_presets_have_expected_shape():
    for bracket in ("young", "teen"):
        assert "daily_hours" in AGE_PRESETS[bracket]
        assert "blocked_domains" in AGE_PRESETS[bracket]
        assert len(AGE_PRESETS[bracket]["blocked_domains"]) > 0


def test_categories_are_non_empty():
    for domains in CATEGORIES.values():
        assert len(domains) > 0
