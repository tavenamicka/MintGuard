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
from PyQt6.QtWidgets import QApplication, QMessageBox

from mintguard.config import get_config
from mintguard.db.database import has_data_dir_access
from mintguard.gui.main_window import MainWindow
from mintguard.locales.loader import get_i18n

_ICON_PATH = Path(__file__).parent / "gui" / "assets" / "icons" / "mintguard.svg"


def _show_permission_error() -> None:
    lang = get_config().get("app.language", "auto")
    i18n = get_i18n(None if lang == "auto" else lang)
    box = QMessageBox()
    box.setIcon(QMessageBox.Icon.Critical)
    box.setWindowTitle(i18n("startup_error.permission_title"))
    box.setText(i18n("startup_error.permission_body"))
    box.exec()


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

    if not has_data_dir_access():
        # Cas attendu juste après l'installation du .deb, pas une erreur à investiguer
        # plus loin : le groupe mintguard-admin (ajouté par postinst) n'est actif qu'après
        # une nouvelle session (voir SUIVI.md).
        _show_permission_error()
        sys.exit(1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
