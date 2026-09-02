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

"""Petit jeu d'icônes vectorielles dessinées à la main (grammaire "type Lucide" : viewBox
24x24, trait 2px, sans remplissage, coins arrondis) — pas de téléchargement d'un jeu externe,
juste assez d'icônes pour guider l'œil sur les libellés importants de l'appli (demande
utilisateur). Rendu à la couleur du thème actif via QSvgRenderer, pas de fichier par couleur."""

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

_SVG_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{path}</svg>'
)

_ICONS: dict[str, str] = {
    "shield-check": (
        '<path d="M12 3.2 5 6v5.5c0 4.6 3 8.3 7 9.3 4-1 7-4.7 7-9.3V6z"/>'
        '<path d="M8.7 12.2l2.1 2.1 4.3-4.3"/>'
    ),
    "shield-alert": (
        '<path d="M12 3.2 5 6v5.5c0 4.6 3 8.3 7 9.3 4-1 7-4.7 7-9.3V6z"/>'
        '<path d="M12 8.5v4"/><path d="M12 15.8h.01"/>'
    ),
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "globe": (
        '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17"/>'
        '<path d="M12 3.5c2.4 2.3 3.7 5.2 3.7 8.5s-1.3 6.2-3.7 8.5c-2.4-2.3-3.7-5.2-3.7-8.5S9.6 5.8 12 3.5z"/>'
    ),
    "app-window": (
        '<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/>'
        '<path d="M3.5 8.8h17"/><circle cx="6.3" cy="6.6" r="0.6" fill="{color}" stroke="none"/>'
    ),
    "settings": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M12 3.5v2.1M12 18.4v2.1M4.6 7.3l1.8 1.1M17.6 15.6l1.8 1.1M3.5 12h2.1'
        'M18.4 12h2.1M4.6 16.7l1.8-1.1M17.6 8.4l1.8-1.1M7.3 4.6l1.1 1.8M15.6 17.6l1.1 1.8"/>'
    ),
    "bar-chart": '<path d="M4.5 19.5v-6M12 19.5v-11M19.5 19.5v-8.5"/><path d="M3 19.5h18"/>',
    "lock": (
        '<rect x="4.5" y="10.5" width="15" height="9.5" rx="2.2"/>'
        '<path d="M7.5 10.5V7.2a4.5 4.5 0 0 1 9 0v3.3"/>'
    ),
    "user-plus": (
        '<circle cx="9.5" cy="8" r="3.5"/><path d="M3.5 20c0-3.6 2.7-6 6-6s6 2.4 6 6"/>'
        '<path d="M18.5 8v5M16 10.5h5"/>'
    ),
    "check-circle": '<circle cx="12" cy="12" r="8.5"/><path d="M8.2 12.3l2.4 2.4 5.2-5.2"/>',
    "help-circle": (
        '<circle cx="12" cy="12" r="8.5"/>'
        '<path d="M9.4 9.6a2.7 2.7 0 0 1 5.2 1c0 1.8-2.6 1.9-2.6 3.6"/><path d="M12 16.9h.01"/>'
    ),
    "chevron-down": '<path d="M5.5 8.5l6.5 7 6.5-7"/>',
    "chevron-right": '<path d="M8.5 5.5l7 6.5-7 6.5"/>',
    "arrow-right": '<path d="M4 12h16M13 6l6 6-6 6"/>',
    "users": (
        '<circle cx="8.5" cy="8" r="3"/><path d="M2.5 19c0-3.3 2.5-5.5 6-5.5s6 2.2 6 5.5"/>'
        '<circle cx="16.5" cy="9" r="2.6"/><path d="M14.8 13.6c2.9.3 4.7 2.3 4.7 5.4"/>'
    ),
    "play-circle": '<circle cx="12" cy="12" r="8.5"/><path d="M10 8.5l6 3.5-6 3.5z"/>',
    "gamepad": (
        '<rect x="3" y="8" width="18" height="9" rx="4"/><path d="M7.5 10.5v4M5.5 12.5h4"/>'
        '<circle cx="15.5" cy="11" r="0.9" fill="{color}" stroke="none"/>'
        '<circle cx="17.5" cy="13" r="0.9" fill="{color}" stroke="none"/>'
    ),
}


def icon(name: str, color: str, size: int = 20) -> QIcon:
    """Rend une icône du jeu ci-dessus à la taille/couleur demandée. `color` doit être un code
    hex (ex. '#0369A1') — appeler avec la couleur active du thème pour rester cohérent."""
    path = _ICONS.get(name)
    if path is None:
        raise KeyError(f"Icône inconnue : {name}")
    svg = _SVG_TEMPLATE.format(color=color, path=path.replace("{color}", color))
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)
