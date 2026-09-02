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

import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from mintguard.gui.main_window import MainWindow

_ICON_PATH = Path(__file__).parent / "gui" / "assets" / "icons" / "mintguard.svg"


def main() -> None:
    app = QApplication(sys.argv)
    # Sans ceci, la fenêtre affiche l'icône générique de la barre des tâches — trouvé en
    # usage réel après installation du .deb : `Icon=mintguard` dans le .desktop ne suffit
    # pas à lui seul, la fenêtre elle-même doit porter son icône (dépend de l'association
    # StartupWMClass du bureau, pas garantie). Bundlée dans le paquet Python (voir
    # setup.py::package_data) plutôt que lue depuis /usr/share/icons : fonctionne aussi
    # en session de développement, sans installation système.
    if _ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(_ICON_PATH)))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
