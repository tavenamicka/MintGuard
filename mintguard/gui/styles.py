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
    # Trouvé à l'audit d'accessibilité Phase 4 (voir SUIVI.md) : la palette d'origine
    # (#0EA5E9/#10B981/#F59E0B/#EF4444, cf. STRATEGIE_UX_UI.html) ne passait pas le contraste
    # WCAG AA (4.5:1) requis — explicitement listé comme "point critique" du projet pour des
    # parents âgés (CLAUDE_CODE_BRIEFING.md). Le pire cas : texte blanc sur "primary" (boutons
    # principaux, partout dans l'app) ne faisait que 2.77:1. Nuances assombries en conservant
    # la même famille de teinte (bleu/vert/ambre/rouge reste reconnaissable) ; toutes vérifiées
    # ≥4.5:1 à la fois en texte sur fond clair ET en texte blanc sur fond coloré (boutons).
    "primary": "#0369A1",
    "primary_hover": "#075985",
    "success": "#047857",
    "warning": "#B45309",
    "danger": "#DC2626",
    "bg": "#F9FAFB",
    "surface": "#FFFFFF",
    "border": "#E5E7EB",
    "text": "#111827",
    "text_muted": "#4B5563",
}

FONT_FAMILY = "Inter, Roboto, 'Segoe UI', system-ui, sans-serif"

# Piste "Néon" proposée via /innovative-design (voir historique de conversation) : thème sombre
# dégradé cyan/magenta pour un rendu plus actuel. Choisi par l'utilisateur parmi 3 pistes, avec
# contrainte dure : rester conforme WCAG AA malgré le fond quasi noir. Chaque couleur ci-dessous
# a été vérifiée à la main (ratios calculés, voir tests/test_styles.py::test_dark_*) contre bg
# ET surface — un fond sombre "safe" sur bg peut ne plus l'être sur une carte plus claire.
# Appliqué pour l'instant uniquement sur DashboardScreen (setStyleSheet local, pas
# app.setStyleSheet) : les autres écrans n'ont pas encore été validés dans cette direction.
DARK_COLORS = {
    "bg": "#0B0B14",
    "surface": "#1B1E29",
    "border": "#33364A",
    "text": "#EDEFF6",
    "text_muted": "#9CA0D6",
    "primary_from": "#00F0FF",
    "primary_to": "#FF2E9A",
    "primary_text": "#0B0B14",
    "success": "#00FFC2",
    "warning": "#FFD23F",
    "danger": "#FF3B5C",
}

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


def build_dark_stylesheet() -> str:
    """Feuille de style QSS de la piste "Néon" (cf. DARK_COLORS). À appliquer localement sur
    un écran (widget.setStyleSheet), jamais sur QApplication tant que seul le Dashboard a été
    validé dans cette direction."""
    c = DARK_COLORS
    f = FONT_SIZES
    gradient = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['primary_from']}, stop:1 {c['primary_to']})"

    def pill(color_key: str) -> str:
        return f"""
        QLabel#{color_key} {{
            background: rgba({_rgba(c[color_key])}, 0.12);
            color: {c[color_key]};
            border: 1px solid rgba({_rgba(c[color_key])}, 0.35);
            border-radius: 11px;
            padding: 4px 14px;
            font-weight: 700;
        }}"""

    return f"""
        QWidget {{
            background: {c['bg']};
            color: {c['text']};
            font-family: {FONT_FAMILY};
            font-size: {f['body']}px;
        }}
        QLabel#h1 {{ font-size: {f['h1']}px; font-weight: 700; color: {c['text']}; }}
        QLabel#h2 {{ font-size: {f['h2']}px; font-weight: 700; color: {c['text']}; }}
        QLabel#h3 {{ font-size: {f['h3']}px; font-weight: 600; color: {c['text']}; }}
        QLabel#small {{ font-size: {f['small']}px; color: {c['text_muted']}; }}
        {pill('success')}
        {pill('warning')}
        {pill('danger')}

        QPushButton {{
            background: {gradient};
            color: {c['primary_text']};
            border: none;
            border-radius: 10px;
            padding: 10px 22px;
            font-size: {f['body']}px;
            font-weight: 700;
        }}
        QPushButton:disabled {{ background: {c['border']}; color: {c['text_muted']}; }}
        QPushButton#secondary {{
            background: transparent;
            color: {c['text']};
            border: 1px solid {c['border']};
            padding: 9px 20px;
        }}
        QPushButton#secondary:hover {{ border-color: {c['primary_from']}; }}

        QFrame#card {{
            background: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 16px;
        }}

        QComboBox {{
            background: {c['surface']};
            color: {c['text']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 8px 12px;
        }}
        QComboBox:hover {{ border-color: {c['primary_from']}; }}
        QComboBox QAbstractItemView {{
            background: {c['surface']};
            color: {c['text']};
            selection-background-color: {c['border']};
        }}

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
        QPushButton#help:hover {{ background: {c['primary_from']}; color: {c['primary_text']}; }}

        QCheckBox, QRadioButton {{ color: {c['text']}; spacing: 8px; }}
        QCheckBox::indicator {{
            width: 18px; height: 18px;
            border: 1px solid {c['border']};
            border-radius: 5px;
            background: {c['surface']};
        }}
        QCheckBox::indicator:checked {{ background: {c['primary_from']}; border-color: {c['primary_from']}; }}
        QCheckBox::indicator:hover {{ border-color: {c['primary_from']}; }}
        QRadioButton::indicator {{
            width: 18px; height: 18px;
            border: 1px solid {c['border']};
            border-radius: 9px;
            background: {c['surface']};
        }}
        QRadioButton::indicator:checked {{ background: {c['primary_from']}; border-color: {c['primary_from']}; }}
        QRadioButton::indicator:hover {{ border-color: {c['primary_from']}; }}

        QSpinBox, QTimeEdit {{
            background: {c['surface']};
            color: {c['text']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 6px 8px;
        }}
        QSpinBox:focus, QTimeEdit:focus {{ border-color: {c['primary_from']}; }}

        QTabWidget::pane {{
            border: 1px solid {c['border']};
            border-radius: 12px;
            top: -1px;
            background: {c['surface']};
        }}
        QTabBar::tab {{
            background: transparent;
            color: {c['text_muted']};
            padding: 9px 18px;
            border: none;
            font-weight: 600;
        }}
        QTabBar::tab:selected {{ color: {c['text']}; border-bottom: 2px solid {c['primary_from']}; }}
        QTabBar::tab:hover {{ color: {c['text']}; }}

        QToolButton {{
            color: {c['text']};
            background: transparent;
            border: none;
            font-weight: 600;
        }}
        QToolButton:hover {{ color: {c['primary_from']}; }}

        QListWidget {{
            background: {c['surface']};
            color: {c['text']};
            border: 1px solid {c['border']};
            border-radius: 10px;
            padding: 4px;
        }}
        QListWidget::item {{ padding: 6px 8px; border-radius: 6px; }}
        QListWidget::item:selected {{ background: rgba({_rgba(c['primary_from'])}, 0.18); color: {c['text']}; }}

        QLineEdit {{
            border: 1px solid {c['border']};
            border-radius: 6px;
            padding: 8px 10px;
            background: {c['surface']};
            color: {c['text']};
            font-size: {f['body']}px;
        }}
        QLineEdit:focus {{ border-color: {c['primary_from']}; }}
    """


def _rgba(hex_color: str) -> str:
    """'#00FFC2' -> '0, 255, 194' pour les rgba() de build_dark_stylesheet()."""
    h = hex_color.lstrip("#")
    return ", ".join(str(int(h[i : i + 2], 16)) for i in (0, 2, 4))


# Registre pour le sélecteur de thème (voir MainWindow.set_theme) : "light"/"dark" sont les
# seules valeurs valides stockées dans ParentConfig(key="theme").
THEMES = {"light": build_stylesheet, "dark": build_dark_stylesheet}
DEFAULT_THEME = "dark"
