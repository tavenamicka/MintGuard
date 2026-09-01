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

from datetime import time as dt_time

from PyQt6.QtCore import QTime
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTabWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from mintguard.backend.installed_apps import list_installed_apps
from mintguard.backend.site_categories import CATEGORIES
from mintguard.db.database import get_session
from mintguard.db.models import BlockedApp, BlockedSite, TimeRule
from mintguard.gui.widgets import HelpButton, heading, small_label
from mintguard.locales.loader import I18nLoader
from mintguard.utils.formatters import weekday_key
from mintguard.utils.validators import is_valid_domain


class TimeTab(QWidget):
    """Onglet 'Limite de Temps' — un créneau par jour, cf. wireframe PROJECT_BRIEF.md 'Écran 2'."""

    def __init__(self, i18n: I18nLoader, child_id: int | None, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.child_id = child_id
        self._day_widgets: list[tuple[QCheckBox, QTimeEdit, QTimeEdit]] = []

        layout = QVBoxLayout(self)

        title_row = QHBoxLayout()
        title_row.addWidget(heading(self.i18n("settings.time_limits"), "h2"))
        title_row.addWidget(
            HelpButton(self.i18n("help.what_is_time_limit"), self.i18n("help.time_limit_explanation"))
        )
        title_row.addStretch(1)
        layout.addLayout(title_row)

        for day_index in range(7):
            row = QHBoxLayout()
            checkbox = QCheckBox(self.i18n(f"time.{weekday_key(day_index)}"))
            start_edit = QTimeEdit(QTime(16, 0))
            start_edit.setDisplayFormat("HH:mm")
            end_edit = QTimeEdit(QTime(20, 0))
            end_edit.setDisplayFormat("HH:mm")
            row.addWidget(checkbox)
            row.addWidget(start_edit)
            row.addWidget(end_edit)
            layout.addLayout(row)
            self._day_widgets.append((checkbox, start_edit, end_edit))

        layout.addStretch(1)

        self.saved_label = small_label(self.i18n("settings.saved_confirmation"))
        self.saved_label.setObjectName("success")
        self.saved_label.hide()
        layout.addWidget(self.saved_label)

        save_button = QPushButton(self.i18n("common.save"))
        save_button.clicked.connect(self._save)
        layout.addWidget(save_button)

        self._load()

    def _load(self) -> None:
        if self.child_id is None:
            self.setEnabled(False)
            return
        session = get_session()
        try:
            rules_by_day = {
                r.day_of_week: (r.enabled, r.start_hour, r.end_hour)
                for r in session.query(TimeRule).filter_by(child_id=self.child_id).all()
            }
        finally:
            session.close()

        for day_index, (checkbox, start_edit, end_edit) in enumerate(self._day_widgets):
            rule = rules_by_day.get(day_index)
            checkbox.setChecked(rule is not None and rule[0])
            if rule is not None:
                _, start_hour, end_hour = rule
                start_edit.setTime(QTime(start_hour.hour, start_hour.minute))
                end_edit.setTime(QTime(end_hour.hour, end_hour.minute))

    def _save(self) -> None:
        if self.child_id is None:
            return
        session = get_session()
        try:
            session.query(TimeRule).filter_by(child_id=self.child_id).delete()
            for day_index, (checkbox, start_edit, end_edit) in enumerate(self._day_widgets):
                if checkbox.isChecked():
                    start_time = start_edit.time()
                    end_time = end_edit.time()
                    session.add(
                        TimeRule(
                            child_id=self.child_id,
                            day_of_week=day_index,
                            start_hour=dt_time(start_time.hour(), start_time.minute()),
                            end_hour=dt_time(end_time.hour(), end_time.minute()),
                            enabled=True,
                        )
                    )
            session.commit()
        finally:
            session.close()
        self.saved_label.show()


class SitesTab(QWidget):
    """Onglet 'Sites à Bloquer' — catégories + liste personnalisée, cf. wireframe 'Écran 3'.

    Le blocage de sites est global (un seul résolveur DNS pour la machine), pas par enfant.
    """

    def __init__(self, i18n: I18nLoader, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._category_checkboxes: dict[str, QCheckBox] = {}

        layout = QVBoxLayout(self)

        title_row = QHBoxLayout()
        title_row.addWidget(heading(self.i18n("settings.blocked_sites"), "h2"))
        title_row.addWidget(HelpButton(self.i18n("help.what_is_blocking"), self.i18n("help.blocking_explanation")))
        title_row.addStretch(1)
        layout.addLayout(title_row)

        for category in CATEGORIES:
            checkbox = QCheckBox(self.i18n(f"settings.category_{category}"))
            checkbox.toggled.connect(lambda checked, c=category: self._toggle_category(c, checked))
            layout.addWidget(checkbox)
            self._category_checkboxes[category] = checkbox

        layout.addWidget(small_label(self.i18n("settings.custom_sites")))
        self.custom_list = QListWidget()
        layout.addWidget(self.custom_list)

        add_row = QHBoxLayout()
        self.add_input = QLineEdit()
        self.add_input.setPlaceholderText(self.i18n("settings.add_site_placeholder"))
        add_row.addWidget(self.add_input)
        add_button = QPushButton(self.i18n("settings.add_site_button"))
        add_button.clicked.connect(self._add_custom_site)
        add_row.addWidget(add_button)
        layout.addLayout(add_row)

        remove_button = QPushButton(self.i18n("settings.remove_site_button"))
        remove_button.setObjectName("secondary")
        remove_button.clicked.connect(self._remove_selected_site)
        layout.addWidget(remove_button)

        self.error_label = small_label("")
        self.error_label.setObjectName("danger")
        self.error_label.hide()
        layout.addWidget(self.error_label)

        layout.addStretch(1)
        self._load()

    def _load(self) -> None:
        session = get_session()
        try:
            blocked_domains = {s.domain for s in session.query(BlockedSite).filter_by(blocked=True).all()}
        finally:
            session.close()

        for category, checkbox in self._category_checkboxes.items():
            domains = set(CATEGORIES[category])
            checkbox.blockSignals(True)
            checkbox.setChecked(bool(domains) and domains.issubset(blocked_domains))
            checkbox.blockSignals(False)

        predefined_domains = {d for domains in CATEGORIES.values() for d in domains}
        self.custom_list.clear()
        for domain in sorted(blocked_domains - predefined_domains):
            self.custom_list.addItem(domain)

    def _toggle_category(self, category: str, checked: bool) -> None:
        session = get_session()
        try:
            for domain in CATEGORIES[category]:
                existing = session.query(BlockedSite).filter_by(domain=domain).first()
                if checked and existing is None:
                    session.add(BlockedSite(domain=domain, category=category, blocked=True))
                elif not checked and existing is not None:
                    session.delete(existing)
            session.commit()
        finally:
            session.close()

    def _add_custom_site(self) -> None:
        domain = self.add_input.text().strip().lower()
        if not is_valid_domain(domain):
            self.error_label.setText(self.i18n("settings.invalid_domain_error"))
            self.error_label.show()
            return
        self.error_label.hide()

        session = get_session()
        try:
            if session.query(BlockedSite).filter_by(domain=domain).first() is None:
                session.add(BlockedSite(domain=domain, category="custom", blocked=True))
                session.commit()
        finally:
            session.close()

        self.add_input.clear()
        self._load()

    def _remove_selected_site(self) -> None:
        item = self.custom_list.currentItem()
        if item is None:
            return
        session = get_session()
        try:
            existing = session.query(BlockedSite).filter_by(domain=item.text()).first()
            if existing is not None:
                session.delete(existing)
                session.commit()
        finally:
            session.close()
        self._load()


class AppsTab(QWidget):
    """Onglet 'Applications à Bloquer' — apps suggérées + liste personnalisée, cf. 'Écran 3'."""

    def __init__(self, i18n: I18nLoader, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._app_checkboxes: dict[str, QCheckBox] = {}

        layout = QVBoxLayout(self)

        title_row = QHBoxLayout()
        title_row.addWidget(heading(self.i18n("settings.blocked_apps"), "h2"))
        title_row.addWidget(
            HelpButton(self.i18n("help.what_is_app_blocking"), self.i18n("help.app_blocking_explanation"))
        )
        title_row.addStretch(1)
        layout.addLayout(title_row)

        # Détection réelle des applications installées (fichiers .desktop) plutôt qu'une
        # liste figée de 4 applis — voir SUIVI.md. Groupées par catégorie, mêmes libellés
        # que l'onglet Sites pour rester cohérent. Une appli qui ne correspond à aucune des
        # 3 catégories n'apparaît pas ici (ex: navigateurs) — la saisie manuelle ci-dessous
        # reste le filet de sécurité, comme pour les sites personnalisés.
        detected = list_installed_apps()
        self._detected_process_names: set[str] = {name for apps in detected.values() for name, _ in apps}
        if any(detected.values()):
            layout.addWidget(small_label(self.i18n("settings.suggested_apps")))
        for category, apps in detected.items():
            if not apps:
                continue
            layout.addWidget(heading(self.i18n(f"settings.category_{category}"), "h3"))
            for process_name, label in apps:
                checkbox = QCheckBox(label)
                checkbox.toggled.connect(lambda checked, p=process_name: self._toggle_app(p, checked))
                layout.addWidget(checkbox)
                self._app_checkboxes[process_name] = checkbox

        layout.addWidget(small_label(self.i18n("settings.custom_apps")))
        self.custom_list = QListWidget()
        layout.addWidget(self.custom_list)

        add_row = QHBoxLayout()
        self.add_input = QLineEdit()
        self.add_input.setPlaceholderText(self.i18n("settings.add_app_placeholder"))
        add_row.addWidget(self.add_input)
        add_button = QPushButton(self.i18n("settings.add_site_button"))
        add_button.clicked.connect(self._add_custom_app)
        add_row.addWidget(add_button)
        layout.addLayout(add_row)

        remove_button = QPushButton(self.i18n("settings.remove_site_button"))
        remove_button.setObjectName("secondary")
        remove_button.clicked.connect(self._remove_selected_app)
        layout.addWidget(remove_button)

        self.error_label = small_label("")
        self.error_label.setObjectName("danger")
        self.error_label.hide()
        layout.addWidget(self.error_label)

        layout.addStretch(1)
        self._load()

    def _load(self) -> None:
        session = get_session()
        try:
            blocked_names = {a.app_name for a in session.query(BlockedApp).filter_by(enabled=True).all()}
        finally:
            session.close()

        for process_name, checkbox in self._app_checkboxes.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(process_name in blocked_names)
            checkbox.blockSignals(False)

        self.custom_list.clear()
        for name in sorted(blocked_names - self._detected_process_names):
            self.custom_list.addItem(name)

    def _toggle_app(self, process_name: str, checked: bool) -> None:
        session = get_session()
        try:
            existing = session.query(BlockedApp).filter_by(app_name=process_name).first()
            if checked and existing is None:
                session.add(BlockedApp(app_name=process_name, enabled=True))
            elif not checked and existing is not None:
                session.delete(existing)
            session.commit()
        finally:
            session.close()

    def _add_custom_app(self) -> None:
        name = self.add_input.text().strip().lower()
        if not name or " " in name:
            self.error_label.setText(self.i18n("settings.invalid_app_error"))
            self.error_label.show()
            return
        self.error_label.hide()

        session = get_session()
        try:
            if session.query(BlockedApp).filter_by(app_name=name).first() is None:
                session.add(BlockedApp(app_name=name, enabled=True))
                session.commit()
        finally:
            session.close()

        self.add_input.clear()
        self._load()

    def _remove_selected_app(self) -> None:
        item = self.custom_list.currentItem()
        if item is None:
            return
        session = get_session()
        try:
            existing = session.query(BlockedApp).filter_by(app_name=item.text()).first()
            if existing is not None:
                session.delete(existing)
                session.commit()
        finally:
            session.close()
        self._load()


class SettingsWindow(QDialog):
    """Fenêtre Paramètres (Écran 2) — onglets Temps, Sites et Applications."""

    def __init__(self, i18n: I18nLoader, child_id: int | None, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setWindowTitle(self.i18n("settings.title"))
        self.setMinimumSize(420, 560)

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.time_tab = TimeTab(i18n, child_id)
        self.tabs.addTab(self.time_tab, self.i18n("settings.time_limits"))

        self.sites_tab = SitesTab(i18n)
        self.tabs.addTab(self.sites_tab, self.i18n("settings.blocked_sites"))

        self.apps_tab = AppsTab(i18n)
        self.tabs.addTab(self.apps_tab, self.i18n("settings.blocked_apps"))

        close_button = QPushButton(self.i18n("common.close"))
        close_button.setObjectName("secondary")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
