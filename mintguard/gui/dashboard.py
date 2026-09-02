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

from datetime import datetime
from datetime import time as dt_time

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mintguard.backend.usage_tracker import UsageTracker
from mintguard.db.database import get_session
from mintguard.db.models import ActivityLog, BlockedSite, Child, TimeRule
from mintguard.gui.daemon_control import is_daemon_active, start_daemon_via_polkit
from mintguard.gui.styles import COLORS, DISPLAY_FONT_FAMILY, FONT_SIZES
from mintguard.gui.widgets import (
    Card,
    Tile,
    growth_stem,
    heading,
    icon_badge,
    icon_label,
    set_icon_badge,
    small_label,
    wrap_layout,
)
from mintguard.locales.loader import I18nLoader
from mintguard.utils.formatters import format_duration, format_percentage, utc_to_local

# Cadence de rafraîchissement du Dashboard pendant qu'il reste affiché — même principe que le
# daemon (voir SUIVI.md, décision d'architecture Semaine 5) : la BD partagée tient lieu de canal
# GUI<->daemon, un délai de quelques secondes est imperceptible pour ce besoin.
_LIVE_REFRESH_INTERVAL_MS = 5000


class DashboardScreen(QWidget):
    """Écran 1 (Dashboard) — vue d'ensemble en un coup d'œil, cf. PROJECT_BRIEF.md 'Écrans Principaux'.

    Note d'architecture : le blocage de sites (BlockedSite) est global à la machine, pas par
    enfant (un seul résolveur DNS pour tout le poste) — seule la limite de temps (TimeRule) est
    propre à l'enfant sélectionné. Le statut « Protection: ACTIVE » reflète la présence de règles
    configurées en BD, pas un signal live du daemon (pas de bus D-Bus — voir SUIVI.md). Le temps
    utilisé aujourd'hui, lui, vient bien du daemon (`UsageTracker`, table `DailyUsage`) : un
    QTimer relit la BD toutes les `_LIVE_REFRESH_INTERVAL_MS` pour que la barre avance pendant
    que le parent regarde l'écran, sans canal IPC dédié.
    """

    def __init__(self, i18n: I18nLoader, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._usage_tracker = UsageTracker()
        self._build_ui()
        self.reload()

        self._live_refresh_timer = QTimer(self)
        self._live_refresh_timer.timeout.connect(self._refresh)
        self._live_refresh_timer.start(_LIVE_REFRESH_INTERVAL_MS)

    def _build_ui(self) -> None:
        colors = COLORS
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.addWidget(icon_label("shield-check", colors["primary"], 22))
        title_row.addWidget(heading(self.i18n("dashboard.title"), "h1"))
        title_row.addStretch(1)
        layout.addLayout(title_row)

        layout.addWidget(small_label(self.i18n("dashboard.child_select")))
        selector_row = QHBoxLayout()
        self.child_combo = QComboBox()
        self.child_combo.currentIndexChanged.connect(self._refresh)
        selector_row.addWidget(self.child_combo, stretch=1)

        self.add_child_button = QPushButton(self.i18n("dashboard.add_child"))
        self.add_child_button.setObjectName("secondary")
        self.add_child_button.clicked.connect(self.open_add_child)
        selector_row.addWidget(self.add_child_button)
        layout.addLayout(selector_row)

        # Carte d'activation : distincte de status_card ci-dessous (qui reflète les règles en
        # BD, pas le daemon - voir sa docstring de classe). Sans elle, l'étape "sudo systemctl
        # start mintguard-daemon" du manuel d'installation restait une commande de terminal
        # hors de portée d'un parent non-technique (voir SUIVI.md). Masquée dès que le daemon
        # répond, montrée sinon - vérifié au même rythme que le reste (_live_refresh_timer).
        self.daemon_card = Card()
        daemon_title_row = QHBoxLayout()
        daemon_title_row.setSpacing(8)
        daemon_title_row.addWidget(icon_badge("shield-alert", size=32, icon_size=18, color=colors["warning"]))
        self.daemon_title = heading(self.i18n("dashboard.daemon_inactive_title"), "h3")
        daemon_title_row.addWidget(self.daemon_title)
        daemon_title_row.addStretch(1)
        self.daemon_card.add(wrap_layout(daemon_title_row))
        self.daemon_body = QLabel(self.i18n("dashboard.daemon_inactive_body"))
        self.daemon_body.setWordWrap(True)
        self.daemon_card.add(self.daemon_body)
        self.daemon_activate_button = QPushButton(self.i18n("dashboard.daemon_activate_button"))
        self.daemon_activate_button.clicked.connect(self._activate_daemon)
        self.daemon_card.add(self.daemon_activate_button)
        self.daemon_card.hide()
        layout.addWidget(self.daemon_card)

        # Carte "héro" pleine largeur : statut de protection, le signal de confiance principal
        # de l'appli — icône + titre + sous-titre, comme la maquette. `status_icon` change de
        # couleur/icône selon l'état (bouclier vert coché / orange alerte) via set_icon_badge().
        self.status_card = Card()
        status_row = QHBoxLayout()
        status_row.setSpacing(10)
        self.status_icon = icon_badge("shield-check", size=40, icon_size=22, color=colors["success"])
        status_row.addWidget(self.status_icon)
        status_text_col = QVBoxLayout()
        status_text_col.setSpacing(2)
        self.status_label = heading("", "h3")
        status_text_col.addWidget(self.status_label)
        self.status_subtitle = small_label("")
        status_text_col.addWidget(self.status_subtitle)
        status_row.addLayout(status_text_col, 1)
        self.status_card.add(wrap_layout(status_row))
        layout.addWidget(self.status_card)

        # Deux tuiles côte à côte (fenêtre d'accès du jour / dernière restriction) plutôt que
        # deux cartes empilées — densité et disposition de la maquette.
        tiles_row = QHBoxLayout()
        tiles_row.setSpacing(10)

        self.window_tile = Tile()
        self.window_tile.add(small_label(self.i18n("dashboard.window_tile_title")))
        self.window_label = QLabel("")
        self.window_label.setWordWrap(True)
        self.window_tile.add(self.window_label)
        tiles_row.addWidget(self.window_tile, 1)

        self.restriction_tile = Tile()
        self.restriction_tile.add(small_label(self.i18n("dashboard.last_restriction")))
        self.restriction_value = QLabel("")
        self.restriction_value.setWordWrap(True)
        self.restriction_tile.add(self.restriction_value)
        tiles_row.addWidget(self.restriction_tile, 1)

        layout.addLayout(tiles_row)

        # Tige en dégradé vert à côté de la barre : repère "ça pousse" de cette piste visuelle,
        # plutôt qu'une simple barre plate.
        self.usage_card = Card()
        usage_row = QHBoxLayout()
        usage_row.setSpacing(12)
        usage_row.addWidget(growth_stem(40))
        usage_col = QVBoxLayout()
        usage_col.setSpacing(6)
        usage_col.addWidget(small_label(self.i18n("dashboard.time_today")))
        self.usage_bar = QProgressBar()
        self.usage_bar.setTextVisible(False)
        usage_col.addWidget(self.usage_bar)
        self.usage_value = QLabel("")
        usage_col.addWidget(self.usage_value)
        usage_row.addLayout(usage_col, 1)
        self.usage_card.add(wrap_layout(usage_row))
        layout.addWidget(self.usage_card)

        layout.addStretch(1)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)
        self.settings_button = QPushButton(self.i18n("common.settings"))
        self.settings_button.clicked.connect(self.open_settings)
        actions_row.addWidget(self.settings_button)

        self.reports_button = QPushButton(self.i18n("common.reports"))
        self.reports_button.setObjectName("secondary")
        self.reports_button.clicked.connect(self.open_reports)
        actions_row.addWidget(self.reports_button)
        layout.addLayout(actions_row)

    # -- Data loading -----------------------------------------------------

    def reload(self) -> None:
        """Recharge la liste des enfants depuis la BD (ex: après fermeture des Settings)."""
        previous_id = self.selected_child_id
        self.child_combo.blockSignals(True)
        self.child_combo.clear()
        session = get_session()
        try:
            children = session.query(Child).order_by(Child.name).all()
            for child in children:
                self.child_combo.addItem(child.name, child.id)
        finally:
            session.close()

        if previous_id is not None:
            index = self.child_combo.findData(previous_id)
            if index >= 0:
                self.child_combo.setCurrentIndex(index)
        self.child_combo.blockSignals(False)
        self._refresh()

    @property
    def selected_child_id(self):
        return self.child_combo.currentData()

    def _refresh(self) -> None:
        self._refresh_daemon_status()
        child_id = self.selected_child_id
        if child_id is None:
            self.status_label.setText(self.i18n("dashboard.no_children"))
            self._style_status_label(COLORS["warning"])
            set_icon_badge(self.status_icon, "shield-alert", COLORS["warning"], 40, 22)
            self.status_subtitle.setText("")
            self.window_label.setText("")
            self.usage_card.hide()
            self.restriction_value.setText("")
            self.settings_button.setEnabled(False)
            self.reports_button.setEnabled(False)
            return

        self.settings_button.setEnabled(True)
        self.reports_button.setEnabled(True)
        active = self._is_protection_active(child_id)
        self.status_label.setText(
            self.i18n("dashboard.protection_active" if active else "dashboard.protection_inactive")
        )
        self.status_subtitle.setText(
            self.i18n("dashboard.protection_active_subtitle" if active else "dashboard.protection_inactive_subtitle")
        )
        status_color = COLORS["success"] if active else COLORS["warning"]
        self._style_status_label(status_color)
        set_icon_badge(self.status_icon, "shield-check" if active else "shield-alert", status_color, 40, 22)

        window = self._today_rule_window(child_id)
        self.window_label.setText(self._today_window_text(window))
        self._refresh_usage(child_id, window)
        self.restriction_value.setText(self._last_restriction_text(child_id))

    def _style_status_label(self, color: str) -> None:
        """Colore le titre de la carte statut en gardant sa taille/police h3 — appliqué en
        style direct plutôt que via objectName pour éviter d'avoir à choisir entre le
        sélecteur QSS `#h3` (taille) et un sélecteur de couleur (les deux ne peuvent pas
        cohabiter proprement sur un seul objectName)."""
        self.status_label.setStyleSheet(
            f"font-family: {DISPLAY_FONT_FAMILY}; font-size: {FONT_SIZES['h3']}px; "
            f"font-weight: 600; color: {color};"
        )

    def _refresh_daemon_status(self) -> None:
        # N'écrase pas la carte pendant qu'une activation est en cours (bouton désactivé,
        # voir _activate_daemon) : un poll du timer de rafraîchissement (5s) pendant que
        # pkexec attend une saisie ne doit pas remettre le bouton dans son état initial.
        if not self.daemon_activate_button.isEnabled() and self.daemon_card.isVisible():
            return
        self.daemon_card.setVisible(not is_daemon_active())

    def _activate_daemon(self) -> None:
        self.daemon_activate_button.setEnabled(False)
        self.daemon_activate_button.setText(self.i18n("dashboard.daemon_activating"))
        # `pkexec` bloque le thread GUI le temps que le parent réponde à la fenêtre système
        # (comme la réinitialisation du PIN, voir dialogs.py) - acceptable pour une action
        # ponctuelle et volontaire déclenchée par un clic, pas un besoin d'asynchronisme ici.
        QApplication.processEvents()
        result = start_daemon_via_polkit()

        if result is None:
            self.daemon_body.setText(self.i18n("dashboard.daemon_activation_unavailable"))
        elif result:
            self.daemon_body.setText(self.i18n("dashboard.daemon_activated"))
            self.daemon_card.hide()
        else:
            self.daemon_body.setText(self.i18n("dashboard.daemon_activation_failed"))

        self.daemon_activate_button.setEnabled(True)
        self.daemon_activate_button.setText(self.i18n("dashboard.daemon_activate_button"))

    def _is_protection_active(self, child_id: int) -> bool:
        session = get_session()
        try:
            has_time_rule = session.query(TimeRule).filter_by(child_id=child_id, enabled=True).count() > 0
            has_blocked_site = session.query(BlockedSite).filter_by(blocked=True).count() > 0
            return has_time_rule or has_blocked_site
        finally:
            session.close()

    def _today_rule_window(self, child_id: int) -> tuple[dt_time, dt_time] | None:
        today = datetime.now().weekday()
        session = get_session()
        try:
            rule = (
                session.query(TimeRule)
                .filter_by(child_id=child_id, day_of_week=today, enabled=True)
                .first()
            )
            # Extraire les valeurs pendant que la session est ouverte : après close(), les
            # attributs ne sont accessibles que par chance (tant qu'aucun commit ne les a
            # expirés) — mieux vaut ne pas dépendre de ce détail d'implémentation SQLAlchemy.
            return (rule.start_hour, rule.end_hour) if rule is not None else None
        finally:
            session.close()

    def _today_window_text(self, window: tuple[dt_time, dt_time] | None) -> str:
        if window is None:
            return self.i18n("dashboard.no_rule_today")
        start_hour, end_hour = window
        return self.i18n("dashboard.today_window").format(start_hour.strftime("%H:%M"), end_hour.strftime("%H:%M"))

    def _refresh_usage(self, child_id: int, window: tuple[dt_time, dt_time] | None) -> None:
        """Barre de progression du temps utilisé aujourd'hui — seulement quand une plage horaire
        est définie pour aujourd'hui (sinon pas de "maximum" auquel comparer, cf. accès libre)."""
        if window is None:
            self.usage_card.hide()
            return

        start_hour, end_hour = window
        limit_seconds = self._seconds_since_midnight(end_hour) - self._seconds_since_midnight(start_hour)
        used_seconds = self._usage_tracker.get_seconds_used_today(child_id)

        self.usage_card.show()
        self.usage_bar.setValue(format_percentage(used_seconds, limit_seconds))
        self.usage_value.setText(
            self.i18n("dashboard.time_used_of_limit").format(
                format_duration(used_seconds), format_duration(limit_seconds)
            )
        )

    @staticmethod
    def _seconds_since_midnight(value: dt_time) -> int:
        return value.hour * 3600 + value.minute * 60 + value.second

    def _last_restriction_text(self, child_id: int) -> str:
        session = get_session()
        try:
            log = (
                session.query(ActivityLog)
                .filter((ActivityLog.child_id == child_id) | (ActivityLog.child_id.is_(None)))
                .order_by(ActivityLog.timestamp.desc())
                .first()
            )
            entry = (log.action, log.details, log.timestamp) if log is not None else None
        finally:
            session.close()
        if entry is None:
            return self.i18n("dashboard.no_restrictions")

        action, details, timestamp = entry
        time_str = utc_to_local(timestamp).strftime("%H:%M")
        if action == "app_blocked":
            label = self.i18n("dashboard.restriction_app_blocked").format(details or "?")
        elif action == "time_limit_hit":
            label = self.i18n("dashboard.restriction_time_limit_hit")
        elif action == "daily_budget_hit":
            label = self.i18n("dashboard.restriction_daily_budget_hit")
        else:
            label = action
        return f"{label} ({time_str})"

    # -- Actions ------------------------------------------------------------

    def open_add_child(self) -> None:
        from mintguard.gui.add_child_dialog import AddChildDialog
        from mintguard.gui.dialogs import PinDialog

        if not PinDialog.prompt(self.i18n, self):
            return
        new_child_id = AddChildDialog.prompt(self.i18n, self)
        if new_child_id is None:
            return
        self.reload()
        index = self.child_combo.findData(new_child_id)
        if index >= 0:
            self.child_combo.setCurrentIndex(index)

    def open_settings(self) -> None:
        from mintguard.gui.dialogs import PinDialog
        from mintguard.gui.settings import SettingsWindow

        if not PinDialog.prompt(self.i18n, self):
            return
        dialog = SettingsWindow(self.i18n, self.selected_child_id, self)
        dialog.exec()
        self.reload()

    def open_reports(self) -> None:
        from mintguard.gui.dialogs import PinDialog
        from mintguard.gui.reports import ReportsWindow

        if not PinDialog.prompt(self.i18n, self):
            return
        dialog = ReportsWindow(self.i18n, self.selected_child_id, self)
        dialog.exec()
