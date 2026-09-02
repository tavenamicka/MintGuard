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

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QLabel, QSystemTrayIcon, QVBoxLayout, QWidget

from mintguard.config import get_config
from mintguard.gui.styles import COLORS
from mintguard.locales.loader import get_i18n

logger = logging.getLogger("mintguard.child_tray")

SOCKET_PATH = "/run/mintguard/status.sock"

# Distincts du popup système (QSystemTrayIcon.showMessage) : celui-ci dépend du support
# systray du bureau et peut passer inaperçu (documenté aux parents, voir USER_MANUAL_*.md) -
# ces deux fenêtres Qt banales (toujours au premier plan, indépendantes du systray) donnent
# une seconde chance à l'enfant de voir l'avertissement, notamment le compte à rebours final.


class _TopBanner(QWidget):
    """Bandeau discret et temporaire en haut de l'écran, pour les avertissements à 10/5/1 min
    (voir _warn_if_threshold_crossed) - se ferme seul, ne bloque jamais l'enfant."""

    AUTO_HIDE_MS = 6000

    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet(
            f"background-color: {COLORS['warning']}; border-radius: 8px;"
            f"QLabel {{ color: white; font-size: 14px; padding: 12px 20px; }}"
        )
        self._label = QLabel()
        self._label.setStyleSheet("color: white; font-size: 14px;")
        self._label.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    def show_message(self, text: str) -> None:
        self._label.setText(text)
        self.adjustSize()
        screen = self.screen() or QApplication.primaryScreen()
        if screen is not None:
            geometry = screen.availableGeometry()
            self.move(geometry.center().x() - self.width() // 2, geometry.top() + 24)
        self.show()
        self.raise_()
        self._hide_timer.start(self.AUTO_HIDE_MS)


class _SessionEndingOverlay(QWidget):
    """Écran de transition affiché pendant la période de grâce (voir Scheduler._apply_grace),
    à la place d'une coupure de session (`loginctl terminate-user`) sans aucun avertissement
    visuel : laisse à l'enfant le temps de voir venir la fermeture et d'enregistrer son
    travail plutôt que de le découvrir en étant brutalement ramené à l'écran de connexion."""

    def __init__(self, i18n):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        self._ = i18n
        self.setFixedSize(480, 220)
        self.setStyleSheet(
            f"background-color: {COLORS['surface']}; border: 2px solid {COLORS['warning']}; border-radius: 12px;"
        )

        self._title = QLabel()
        self._title.setStyleSheet(f"color: {COLORS['text']}; font-size: 20px; font-weight: bold;")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setWordWrap(True)

        self._body = QLabel()
        self._body.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 15px;")
        self._body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._body.setWordWrap(True)

        self._footer = QLabel(self._("child_tray.session_ending_footer"))
        self._footer.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px;")
        self._footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._body)
        layout.addWidget(self._footer)

        self._title.setText(self._("child_tray.session_ending_title"))

    def show_centered(self) -> None:
        screen = self.screen() or QApplication.primaryScreen()
        if screen is not None:
            geometry = screen.availableGeometry()
            self.move(
                geometry.center().x() - self.width() // 2,
                geometry.center().y() - self.height() // 2,
            )
        self.show()
        self.raise_()
        self.activateWindow()

    def update_seconds(self, seconds: int) -> None:
        if seconds > 0:
            self._body.setText(self._("child_tray.session_ending_body").format(seconds))
        else:
            self._body.setText(self._("child_tray.session_ending_body_now"))


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

        self.banner = _TopBanner()
        self.grace_overlay = _SessionEndingOverlay(self._)
        # Compte à rebours local à la seconde entre deux sondages du daemon (poll_interval_ms,
        # 15s par défaut) : le nombre de secondes restantes vient du serveur (source de
        # vérité, voir Scheduler.get_grace_seconds_remaining), mais l'affichage est rafraîchi
        # localement chaque seconde pour un compte à rebours lisible plutôt qu'un chiffre figé
        # 15 secondes d'affilée.
        self._grace_seconds_left: int | None = None
        self.grace_tick_timer = QTimer()
        self.grace_tick_timer.timeout.connect(self._tick_grace_countdown)

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
        self._update_grace(status.get("grace_seconds_remaining"))

    def _update_grace(self, grace_seconds_remaining: int | None) -> None:
        if grace_seconds_remaining is None:
            # Le parent a corrigé les réglages pendant la grâce, ou un nouveau jour a démarré
            # (voir Scheduler.check_all_children) : plus de coupure imminente, on referme.
            if self._grace_seconds_left is not None:
                self._grace_seconds_left = None
                self.grace_tick_timer.stop()
                self.grace_overlay.hide()
            return

        self._grace_seconds_left = grace_seconds_remaining
        self.grace_overlay.update_seconds(self._grace_seconds_left)
        if not self.grace_overlay.isVisible():
            self.grace_overlay.show_centered()
            self.grace_tick_timer.start(1000)

    def _tick_grace_countdown(self) -> None:
        if self._grace_seconds_left is None:
            self.grace_tick_timer.stop()
            return
        self._grace_seconds_left = max(0, self._grace_seconds_left - 1)
        self.grace_overlay.update_seconds(self._grace_seconds_left)

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
                message = self._("child_tray.warning_minutes_left").format(threshold)
                self.tray.showMessage(self._("app.name"), message, QSystemTrayIcon.MessageIcon.Warning)
                # Le popup systray ci-dessus n'est pas garanti visible (dépend du support du
                # bureau, voir USER_MANUAL_*.md) : le bandeau est une fenêtre Qt ordinaire,
                # toujours affichée, en plus - pas à la place.
                self.banner.show_message(message)

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
