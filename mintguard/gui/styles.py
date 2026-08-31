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

"""Système de design MintGuard (palette, typographie, feuille de style QSS)
conforme à STRATEGIE_UX_UI.html section "Design Graphique"."""

COLORS = {
    "primary": "#0EA5E9",
    "primary_hover": "#0284C7",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "bg": "#F9FAFB",
    "surface": "#FFFFFF",
    "border": "#E5E7EB",
    "text": "#111827",
    "text_muted": "#4B5563",
}

FONT_FAMILY = "Inter, Roboto, 'Segoe UI', system-ui, sans-serif"

FONT_SIZES = {
    "h1": 28,
    "h2": 22,
    "h3": 18,
    "body": 16,
    "small": 14,
}


def build_stylesheet() -> str:
    """Génère la feuille de style QSS globale de l'application."""
    c = COLORS
    f = FONT_SIZES
    return f"""
        QWidget {{
            background: {c['bg']};
            color: {c['text']};
            font-family: {FONT_FAMILY};
            font-size: {f['body']}px;
        }}
        QLabel#h1 {{ font-size: {f['h1']}px; font-weight: 700; color: {c['primary']}; }}
        QLabel#h2 {{ font-size: {f['h2']}px; font-weight: 700; }}
        QLabel#h3 {{ font-size: {f['h3']}px; font-weight: 600; }}
        QLabel#small {{ font-size: {f['small']}px; color: {c['text_muted']}; }}
        QLabel#success {{ color: {c['success']}; font-weight: 600; }}
        QLabel#warning {{ color: {c['warning']}; font-weight: 600; }}
        QLabel#danger {{ color: {c['danger']}; font-weight: 600; }}

        QPushButton {{
            background: {c['primary']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 22px;
            font-size: {f['body']}px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background: {c['primary_hover']}; }}
        QPushButton:disabled {{ background: {c['border']}; color: {c['text_muted']}; }}
        QPushButton#secondary {{
            background: {c['surface']};
            color: {c['primary']};
            border: 2px solid {c['primary']};
            padding: 8px 20px;
        }}
        QPushButton#secondary:hover {{ background: #F0F9FF; }}
        QPushButton#help {{
            background: {c['border']};
            color: {c['text_muted']};
            border-radius: 12px;
            min-width: 24px;
            max-width: 24px;
            min-height: 24px;
            max-height: 24px;
            padding: 0;
            font-weight: 700;
        }}
        QPushButton#help:hover {{ background: {c['primary']}; color: white; }}

        QFrame#card {{
            background: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 10px;
        }}

        QProgressBar {{
            background: {c['border']};
            border-radius: 4px;
            max-height: 8px;
            text-align: center;
        }}
        QProgressBar::chunk {{ background: {c['primary']}; border-radius: 4px; }}

        QLineEdit {{
            border: 1px solid {c['border']};
            border-radius: 6px;
            padding: 8px 10px;
            background: {c['surface']};
            font-size: {f['body']}px;
        }}
        QLineEdit:focus {{ border-color: {c['primary']}; }}
    """
