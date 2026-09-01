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

from mintguard.gui.styles import COLORS, DARK_COLORS, build_dark_stylesheet, build_stylesheet


def test_stylesheet_contains_primary_color():
    css = build_stylesheet()
    assert COLORS["primary"] in css


def test_stylesheet_defines_heading_classes():
    css = build_stylesheet()
    for selector in ("QLabel#h1", "QLabel#h2", "QLabel#h3", "QPushButton", "QProgressBar"):
        assert selector in css


# Trouvé à l'audit d'accessibilité Phase 4 (voir SUIVI.md) : la palette d'origine ne passait
# pas le contraste WCAG AA (4.5:1), un "point critique" explicite du projet (parents âgés).
# Ces tests évitent une régression silencieuse si la palette est retouchée plus tard.

WCAG_AA_NORMAL_TEXT = 4.5


def _relative_luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = channel(r), channel(g), channel(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(hex_a: str, hex_b: str) -> float:
    l1, l2 = sorted((_relative_luminance(hex_a), _relative_luminance(hex_b)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def test_status_colors_meet_wcag_aa_against_background():
    for key in ("primary", "success", "warning", "danger", "text_muted"):
        ratio = _contrast_ratio(COLORS[key], COLORS["bg"])
        assert ratio >= WCAG_AA_NORMAL_TEXT, f"{key} on bg: {ratio:.2f}:1 < {WCAG_AA_NORMAL_TEXT}:1"


def test_button_text_meets_wcag_aa_against_primary_backgrounds():
    # QPushButton texte blanc sur fond {primary,primary_hover} (boutons principaux, partout).
    for key in ("primary", "primary_hover"):
        ratio = _contrast_ratio("#FFFFFF", COLORS[key])
        assert ratio >= WCAG_AA_NORMAL_TEXT, f"white on {key}: {ratio:.2f}:1 < {WCAG_AA_NORMAL_TEXT}:1"


# Piste "Néon" (DashboardScreen, voir styles.py::DARK_COLORS) : même contrainte dure WCAG AA,
# choisie explicitement malgré le fond quasi noir. Un fond "safe" sur bg peut ne plus l'être sur
# une carte plus claire (surface) — les deux sont donc vérifiés séparément.


def test_dark_status_colors_meet_wcag_aa_against_background_and_surface():
    for key in ("success", "warning", "danger", "text_muted"):
        for bg_key in ("bg", "surface"):
            ratio = _contrast_ratio(DARK_COLORS[key], DARK_COLORS[bg_key])
            assert ratio >= WCAG_AA_NORMAL_TEXT, f"{key} on {bg_key}: {ratio:.2f}:1 < {WCAG_AA_NORMAL_TEXT}:1"


def test_dark_button_text_meets_wcag_aa_against_gradient_stops():
    # QPushButton texte {primary_text} sur le dégradé {primary_from} -> {primary_to} : les deux
    # extrémités doivent passer (le dégradé n'est pas garanti monotone en luminance au milieu).
    for key in ("primary_from", "primary_to"):
        ratio = _contrast_ratio(DARK_COLORS["primary_text"], DARK_COLORS[key])
        assert ratio >= WCAG_AA_NORMAL_TEXT, f"{DARK_COLORS['primary_text']} on {key}: {ratio:.2f}:1"


def test_dark_stylesheet_contains_gradient_and_card_rules():
    css = build_dark_stylesheet()
    for selector in ("QLabel#h1", "QPushButton", "QFrame#card", "QComboBox", "qlineargradient"):
        assert selector in css
