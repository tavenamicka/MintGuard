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

"""Système de design MintGuard — piste "Jardin Numérique" (palette, typographie, feuille de
style QSS). Thème unique, pas de mode sombre (demande explicite de l'utilisateur : une appli de
contrôle parental n'a pas besoin d'un sélecteur de thème, un seul rendu chaleureux/rassurant
suffit)."""

from pathlib import Path

from PyQt6.QtGui import QFontDatabase

COLORS = {
    # Palette crème/vert de la maquette, réassombrie sur `primary`/`warning` pour rester
    # ≥4.5:1 (WCAG AA) contre `bg` et en texte blanc sur bouton — vérifié dans
    # tests/test_styles.py (parents non-techniques/âgés, contrainte explicite du projet).
    "primary": "#447250",
    "primary_hover": "#396044",
    "success": "#447250",
    "warning": "#95591C",
    "danger": "#A5432F",
    "bg": "#F1F0E2",
    "surface": "#FAF9EE",
    "tile": "#E7E5D2",
    "border": "#D3D2BC",
    "text": "#2B3328",
    "text_muted": "#616B57",
    "on_primary": "#F7F6EA",
    # Purement décoratif (tige de croissance, badges) — jamais utilisé comme couleur de texte,
    # donc hors du périmètre du test de contraste WCAG.
    "accent": "#D98E5A",
}

# Serif chaleureux pour les titres + sans-serif humaniste pour le texte courant. Bundlées (voir
# assets/fonts/) car Qt ne charge pas les Google Fonts par lien CSS comme un navigateur ;
# téléchargement approuvé par l'utilisateur (SIL OFL, voir assets/fonts/OFL-Fraunces.txt et
# OFL-Karla.txt).
BODY_FONT_FAMILY = "'Karla', system-ui, sans-serif"
DISPLAY_FONT_FAMILY = f"'Fraunces', Georgia, {BODY_FONT_FAMILY}"
FONT_FAMILY = BODY_FONT_FAMILY  # alias : la plupart du QSS ci-dessous vise le texte courant

_FONT_DIR = Path(__file__).parent / "assets" / "fonts"
_fonts_loaded = False

# Échelle de rayons organique (coins généreux, boutons en pilule) — cf. maquette.
#
# `pill` n'est PAS 999 (l'idiome CSS web habituel) : trouvé en testant sur le vrai bureau
# (capture d'écran réelle, pas juste le QSS relu) que Qt n'arrondit QUE deux conditions à la
# fois réunies : (1) le widget a un `border` réel non "none" (même transparent/de la même
# couleur que le fond — un `border: none` fait tomber Qt en retour au rendu natif carré du
# style de base, border-radius entièrement ignoré) ET (2) le rayon ne dépasse pas nettement la
# moitié de la plus petite dimension du widget (un rayon disproportionné comme 999 fait aussi
# échouer l'arrondi, silencieusement — pas de clamp comme en CSS web). 16px reste sous la
# moitié de la hauteur des boutons de l'appli (~37-40px) avec une marge de sécurité.
RADII = {"control": 14, "card": 20, "pill": 16}


def load_fonts() -> None:
    """Enregistre les polices Fraunces/Karla auprès de Qt (QFontDatabase) — idempotent, sans
    effet si déjà chargées. À appeler après la création de QApplication et avant toute mise en
    forme QSS qui les référence (voir MainWindow.__init__)."""
    global _fonts_loaded
    if _fonts_loaded:
        return
    for filename in (
        "Fraunces-SemiBold.ttf",
        "Fraunces-Bold.ttf",
        "Karla-Regular.ttf",
        "Karla-Medium.ttf",
        "Karla-Bold.ttf",
    ):
        font_path = _FONT_DIR / filename
        if font_path.exists():
            QFontDatabase.addApplicationFont(str(font_path))
    _fonts_loaded = True


# Resserrée pour coller à la densité de la maquette (compacte, tuiles rapprochées) plutôt qu'à
# une échelle "SaaS aéré".
FONT_SIZES = {
    "h1": 22,
    "h2": 18,
    "h3": 16,
    "body": 14,
    "small": 13,
}


def build_stylesheet() -> str:
    """Génère la feuille de style QSS globale de l'application (thème unique)."""
    c = COLORS
    f = FONT_SIZES
    r = RADII
    gradient_bar = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6E9C6A, stop:1 {c['primary']})"
    return f"""
        /* `background` volontairement absent de la règle QWidget générique : Qt peint alors
        chaque widget (chaque QLabel y compris) avec ce fond, sur son propre rectangle — visible
        comme un rectangle à coins droits derrière chaque texte dès qu'il est posé sur une Card
        ou une tuile (fond différent de `bg`), au lieu de laisser transparaître le fond du parent.
        Seules les fenêtres de premier niveau peignent `bg` ; tout le reste en hérite par
        transparence. `color`/`font-*` restent sur QWidget : ces propriétés s'héritent
        normalement, sans cet effet de bord. */
        QWidget {{
            color: {c['text']};
            font-family: {BODY_FONT_FAMILY};
            font-size: {f['body']}px;
        }}
        QMainWindow, QDialog {{
            background: {c['bg']};
        }}
        QLabel#h1 {{ font-family: {DISPLAY_FONT_FAMILY}; font-size: {f['h1']}px; font-weight: 700; color: {c['text']}; }}
        QLabel#h2 {{ font-family: {DISPLAY_FONT_FAMILY}; font-size: {f['h2']}px; font-weight: 700; color: {c['text']}; }}
        QLabel#h3 {{ font-family: {DISPLAY_FONT_FAMILY}; font-size: {f['h3']}px; font-weight: 600; color: {c['text']}; }}
        QLabel#small {{ font-size: {f['small']}px; color: {c['text_muted']}; }}
        QLabel#success {{ color: {c['success']}; font-weight: 600; }}
        QLabel#warning {{ color: {c['warning']}; font-weight: 600; }}
        QLabel#danger {{ color: {c['danger']}; font-weight: 600; }}

        QPushButton {{
            background: {c['primary']};
            color: {c['on_primary']};
            border: 2px solid {c['primary']};
            border-radius: {r['pill']}px;
            padding: 8px 16px;
            font-size: {f['body']}px;
            font-weight: 700;
        }}
        QPushButton:hover {{ background: {c['primary_hover']}; border-color: {c['primary_hover']}; }}
        QPushButton:pressed {{ background: {c['primary_hover']}; border-color: {c['primary_hover']}; padding-top: 9px; padding-bottom: 7px; }}
        QPushButton:disabled {{ background: {c['border']}; color: {c['text_muted']}; border-color: {c['border']}; }}
        QPushButton#secondary {{
            background: {c['surface']};
            color: {c['primary']};
            border: 2px solid {c['primary']};
            padding: 8px 16px;
        }}
        QPushButton#secondary:hover {{ background: {c['tile']}; }}
        QPushButton#secondary:pressed {{ background: {c['tile']}; }}
        QPushButton#secondary:disabled {{ background: {c['surface']}; color: {c['text_muted']}; border-color: {c['border']}; }}
        /* Boutons "Fermer" (quitter un écran sans agir sur des données) — délibérément plus
        neutre que #secondary (Supprimer, Annuler...) : trouvé en usage réel, les deux se
        confondaient en bas de l'onglet Sites à éviter (même forme, même vert) alors que
        Fermer n'a pas les mêmes conséquences que Supprimer. */
        QPushButton#tertiary {{
            background: transparent;
            color: {c['text_muted']};
            border: 2px solid {c['border']};
            padding: 8px 16px;
        }}
        QPushButton#tertiary:hover {{ background: {c['tile']}; border-color: {c['text_muted']}; }}
        QPushButton#tertiary:pressed {{ background: {c['tile']}; }}
        QPushButton#segment {{
            background: {c['surface']};
            color: {c['text_muted']};
            border: 2px solid {c['border']};
            padding: 8px 16px;
        }}
        QPushButton#segment:hover {{ background: {c['tile']}; }}
        QPushButton#segment:checked {{ background: {c['primary']}; color: {c['on_primary']}; border-color: {c['primary']}; }}
        QPushButton#help {{
            background: {c['tile']};
            border: 2px solid {c['tile']};
            border-radius: 12px;
            min-width: 28px;
            max-width: 28px;
            min-height: 28px;
            max-height: 28px;
            padding: 0;
        }}
        QPushButton#help:hover {{ background: {c['border']}; border-color: {c['border']}; }}
        QPushButton#link {{
            background: transparent;
            color: {c['text_muted']};
            border: none;
            padding: 4px;
            font-weight: 600;
        }}
        QPushButton#link:hover {{ color: {c['primary']}; }}

        QFrame#card {{
            background: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: {r['card']}px;
        }}
        QFrame#tile {{
            background: {c['tile']};
            border: 1px solid {c['border']};
            border-radius: {r['control']}px;
        }}

        QProgressBar {{
            background: {c['tile']};
            border: none;
            border-radius: 7px;
            min-height: 14px;
            max-height: 14px;
            text-align: center;
        }}
        QProgressBar::chunk {{ background: {gradient_bar}; border-radius: 7px; }}

        QLineEdit {{
            border: 1px solid {c['border']};
            border-radius: {r['control']}px;
            padding: 8px 12px;
            background: {c['surface']};
            font-size: {f['body']}px;
        }}
        QLineEdit:hover {{ border-color: {c['primary']}; }}
        QLineEdit:focus {{ border-color: {c['primary']}; }}

        QComboBox {{
            background: {c['surface']};
            color: {c['text']};
            border: 1px solid {c['border']};
            border-radius: {r['control']}px;
            padding: 7px 12px;
            min-height: 18px;
        }}
        QComboBox:hover, QComboBox:focus {{ border-color: {c['primary']}; }}
        QComboBox::drop-down {{ border: none; width: 26px; }}
        QComboBox QAbstractItemView {{
            background: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: {r['control']}px;
            padding: 4px;
            outline: none;
            selection-background-color: {c['tile']};
            selection-color: {c['primary']};
        }}

        QCheckBox, QRadioButton {{ color: {c['text']}; spacing: 10px; padding: 2px 0; }}
        QCheckBox::indicator {{
            width: 20px; height: 20px;
            border: 2px solid {c['border']};
            border-radius: 8px;
            background: {c['surface']};
        }}
        QCheckBox::indicator:hover {{ border-color: {c['primary']}; }}
        QCheckBox::indicator:checked {{ background: {c['primary']}; border-color: {c['primary']}; }}
        QRadioButton::indicator {{
            width: 20px; height: 20px;
            border: 2px solid {c['border']};
            border-radius: 10px;
            background: {c['surface']};
        }}
        QRadioButton::indicator:hover {{ border-color: {c['primary']}; }}
        QRadioButton::indicator:checked {{ background: {c['primary']}; border-color: {c['primary']}; }}

        QSpinBox, QTimeEdit {{
            background: {c['surface']};
            color: {c['text']};
            border: 1px solid {c['border']};
            border-radius: {r['control']}px;
            padding: 7px 10px;
            min-height: 20px;
        }}
        QSpinBox:hover, QTimeEdit:hover {{ border-color: {c['primary']}; }}
        QSpinBox:focus, QTimeEdit:focus {{ border-color: {c['primary']}; }}

        QTabWidget::pane {{
            border: 1px solid {c['border']};
            border-radius: {r['card']}px;
            top: -1px;
            background: {c['surface']};
            padding: 6px;
        }}
        QTabBar::tab {{
            background: transparent;
            color: {c['text_muted']};
            padding: 10px 18px;
            margin: 4px 3px;
            border: 2px solid transparent;
            border-radius: {r['pill']}px;
            font-weight: 600;
        }}
        QTabBar::tab:selected {{ background: {c['tile']}; color: {c['primary']}; }}
        QTabBar::tab:hover:!selected {{ background: {c['bg']}; color: {c['text']}; }}

        QToolButton {{
            color: {c['text']};
            background: transparent;
            border: 2px solid transparent;
            border-radius: {r['pill']}px;
            padding: 6px 10px;
            font-weight: 600;
        }}
        QToolButton:hover {{ background: {c['tile']}; color: {c['primary']}; }}

        QListWidget {{
            background: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: {r['control']}px;
            padding: 4px;
        }}
        QListWidget::item {{ padding: 8px 10px; border-radius: 10px; }}
        QListWidget::item:selected {{ background: {c['tile']}; color: {c['primary']}; }}
        QListWidget::item:hover {{ background: {c['bg']}; }}

        QMenuBar {{ background: transparent; padding: 4px; }}
        QMenuBar::item {{ padding: 6px 12px; border-radius: {r['control']}px; }}
        QMenuBar::item:selected {{ background: {c['tile']}; color: {c['primary']}; }}
        QMenu {{
            background: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: {r['control']}px;
            padding: 6px;
        }}
        QMenu::item {{ padding: 8px 16px; border-radius: 10px; }}
        QMenu::item:selected {{ background: {c['tile']}; color: {c['primary']}; }}
        QMenu::separator {{ height: 1px; background: {c['border']}; margin: 6px 4px; }}

        QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px 4px 0; }}
        QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 5px; min-height: 24px; }}
        QScrollBar::handle:vertical:hover {{ background: {c['text_muted']}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0 4px 2px 4px; }}
        QScrollBar::handle:horizontal {{ background: {c['border']}; border-radius: 5px; min-width: 24px; }}
        QScrollBar::handle:horizontal:hover {{ background: {c['text_muted']}; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}
    """
