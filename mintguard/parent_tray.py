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

import logging
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from mintguard.child_tray import query_status
from mintguard.config import get_config
from mintguard.locales.loader import get_i18n

logger = logging.getLogger("mintguard.parent_tray")

_ICONS_DIR = Path(__file__).parent / "gui" / "assets" / "icons"
# Chemins de fichiers bundlés (package_data, voir setup.py), pas QIcon.fromTheme() : ne
# depend pas du cache d'icones du theme systeme (qui pourrait ne pas connaitre "mintguard"
# tant que gtk-update-icon-cache n'a pas tourne), et permet deux variantes distinctes selon
# l'etat du daemon. Construits en instance (pas au niveau module) : QIcon peut necessiter
# QApplication deja instanciee pour le rendu SVG selon la plateforme.
_ICON_PATH_ACTIVE = str(_ICONS_DIR / "tray-active.svg")
_ICON_PATH_INACTIVE = str(_ICONS_DIR / "tray-inactive.svg")


class ParentTray:
    """Icône de zone de notification côté parent : seul moyen visuel, sans ouvrir
    l'application, de savoir que MintGuard est installé et que le daemon tourne (demande
    utilisateur directe après l'installation du .deb, voir SUIVI.md). Purement informatif -
    aucune action de contrôle parental ici, tout se fait dans la fenêtre principale
    (mintguard/main_gui.py), accessible via le menu.

    S'auto-désactive si le compte courant est un compte enfant (déjà couvert par ChildTray,
    voir child_tray.py) - aucun marqueur OS pour "compte parent", déployé en autostart pour
    toutes les sessions comme ChildTray."""

    def __init__(self, app: QApplication):
        self.app = app
        self._ = get_i18n()
        config = get_config()
        self.poll_interval_ms = int(config.get("child_tray.poll_interval_seconds", 15)) * 1000
        self._daemon_was_active: bool | None = None

        self._icon_active = QIcon(_ICON_PATH_ACTIVE)
        self._icon_inactive = QIcon(_ICON_PATH_INACTIVE)

        self.tray = QSystemTrayIcon(self._icon_active)
        self.tray.setToolTip(self._("parent_tray.tooltip_checking"))
        self.tray.activated.connect(self._on_activated)

        menu = QMenu()
        open_action = menu.addAction(self._("parent_tray.open_action"))
        open_action.triggered.connect(self._open_main_gui)
        menu.addSeparator()
        quit_action = menu.addAction(self._("common.close"))
        quit_action.triggered.connect(self.app.quit)
        self.tray.setContextMenu(menu)

        self.timer = QTimer()
        self.timer.timeout.connect(self.poll)
        self.timer.start(self.poll_interval_ms)

    def start(self) -> None:
        # Voir ChildTray.start() : QApplication.quit() appele avant app.exec() est ignore,
        # le premier poll() doit donc etre differe au prochain tour de boucle.
        QTimer.singleShot(0, self.poll)

    def poll(self) -> None:
        status = query_status()
        if status is not None and status.get("is_child"):
            logger.info("Compte enfant détecté, arrêt (déjà couvert par ChildTray).")
            self.app.quit()
            return

        if not self.tray.isVisible():
            self.tray.show()

        daemon_active = status is not None
        self._update_tooltip(daemon_active)
        self._notify_if_state_changed(daemon_active)

    def _update_tooltip(self, daemon_active: bool) -> None:
        key = "parent_tray.tooltip_active" if daemon_active else "parent_tray.tooltip_inactive"
        self.tray.setToolTip(self._(key))
        self.tray.setIcon(self._icon_active if daemon_active else self._icon_inactive)

    def _notify_if_state_changed(self, daemon_active: bool) -> None:
        # Pas de notification au tout premier poll (etat inconnu avant) - seulement sur un
        # vrai changement d'etat, pour ne pas alerter "actif" a chaque demarrage de session.
        if self._daemon_was_active is not None and self._daemon_was_active != daemon_active:
            key = "parent_tray.notif_active" if daemon_active else "parent_tray.notif_inactive"
            icon = QSystemTrayIcon.MessageIcon.Information if daemon_active else QSystemTrayIcon.MessageIcon.Warning
            self.tray.showMessage(self._("app.name"), self._(key), icon)
        self._daemon_was_active = daemon_active

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._open_main_gui()

    @staticmethod
    def _open_main_gui() -> None:
        # Chemin absolu, pas juste "mintguard" : lance depuis l'autostart, ce process n'a pas
        # /opt/mintguard/venv/bin dans son PATH (venv non active), meme emplacement que les
        # autres executables du paquet (voir packaging/deb/mintguard.desktop).
        gui_path = str(Path(sys.executable).parent / "mintguard")
        QProcess.startDetached(gui_path, [])


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    tray = ParentTray(app)
    tray.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
