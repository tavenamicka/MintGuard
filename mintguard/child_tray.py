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

import json
import logging
import socket
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from mintguard.config import get_config
from mintguard.locales.loader import get_i18n

logger = logging.getLogger("mintguard.child_tray")

SOCKET_PATH = "/run/mintguard/status.sock"


def query_status() -> dict | None:
    """Interroge le daemon (StatusServer). None si le daemon est injoignable (pas encore
    démarré, ou machine hors cible Linux - échec silencieux, ce composant ne doit jamais
    faire planter la session de l'enfant)."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            sock.connect(SOCKET_PATH)
            sock.sendall((json.dumps({"cmd": "status"}) + "\n").encode("utf-8"))
            raw = sock.recv(4096)
            return json.loads(raw.decode("utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as e:
        logger.warning("StatusServer injoignable: %s", e)
        return None


class ChildTray:
    """Icône de zone de notification côté enfant : avertit avant la coupure de session (temps
    écoulé) ou informe qu'une application vient d'être fermée (bloquée). Purement informatif
    - l'application des règles reste entièrement côté daemon (Scheduler/ProcessMonitor),
    voir SUIVI.md. S'auto-désactive si le compte courant n'est pas un compte enfant (aucun
    marqueur OS pour "compte enfant" - déployé en autostart pour toutes les sessions, voir
    packaging/deb/mintguard-child-tray.desktop)."""

    def __init__(self, app: QApplication):
        self.app = app
        self._ = get_i18n()
        config = get_config()
        self.poll_interval_ms = int(config.get("child_tray.poll_interval_seconds", 15)) * 1000
        self.thresholds = sorted(config.get("child_tray.warning_thresholds_minutes", [10, 5, 1]), reverse=True)
        self._warned_thresholds: set[int] = set()
        self._seen_blocks: set[str] = set()

        self.tray = QSystemTrayIcon(QIcon.fromTheme("mintguard"))
        self.tray.setToolTip(self._("app.name"))

        self.timer = QTimer()
        self.timer.timeout.connect(self.poll)
        self.timer.start(self.poll_interval_ms)

    def start(self) -> None:
        # Different du prochain tour de boucle (et non un appel direct) : QApplication.quit()
        # appele avant que app.exec() n'ait demarre la boucle d'evenements est ignore (constat
        # direct - voir SUIVI.md), ce qui empechait l'auto-desactivation immediate pour un
        # compte non-enfant de fonctionner.
        QTimer.singleShot(0, self.poll)

    def poll(self) -> None:
        status = query_status()
        if status is None:
            return
        if not status.get("is_child"):
            logger.info("Compte non-enfant détecté, arrêt.")
            self.app.quit()
            return

        if not self.tray.isVisible():
            self.tray.show()

        self._update_tooltip(status.get("minutes_remaining"))
        self._warn_if_threshold_crossed(status.get("minutes_remaining"))
        self._notify_new_blocks(status.get("recent_blocks") or [])

    def _update_tooltip(self, minutes_remaining: int | None) -> None:
        if minutes_remaining is None:
            self.tray.setToolTip(self._("app.name"))
        else:
            self.tray.setToolTip(self._("child_tray.tooltip_minutes").format(minutes_remaining))

    def _warn_if_threshold_crossed(self, minutes_remaining: int | None) -> None:
        if minutes_remaining is None:
            return
        for threshold in self.thresholds:
            if minutes_remaining <= threshold and threshold not in self._warned_thresholds:
                self._warned_thresholds.add(threshold)
                self.tray.showMessage(
                    self._("app.name"),
                    self._("child_tray.warning_minutes_left").format(threshold),
                    QSystemTrayIcon.MessageIcon.Warning,
                )

    def _notify_new_blocks(self, recent_blocks: list[str]) -> None:
        for details in recent_blocks:
            if details in self._seen_blocks:
                continue
            self._seen_blocks.add(details)
            self.tray.showMessage(
                self._("app.name"),
                self._("child_tray.app_blocked").format(details),
                QSystemTrayIcon.MessageIcon.Information,
            )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    tray = ChildTray(app)
    tray.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
