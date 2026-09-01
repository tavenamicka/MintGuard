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
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from mintguard.backend.installed_apps import list_installed_apps
from mintguard.backend.site_categories import CATEGORIES
from mintguard.db.database import get_session
from mintguard.db.models import BlockedApp, BlockedSite, TimeRule
from mintguard.gui.widgets import CollapsibleSection, HelpButton, heading, small_label
from mintguard.locales.loader import I18nLoader
from mintguard.utils.formatters import weekday_key
from mintguard.utils.validators import is_valid_domain


def _scrollable_layout(container: QWidget) -> QVBoxLayout:
    """Place le contenu de `container` dans un QScrollArea au lieu de son layout direct.

    Trouvé en vérifiant le thème Néon (voir historique de conversation) : un QTabWidget ne
    redimensionne pas la fenêtre quand on bascule sur un onglet plus grand que celui affiché à
    l'ouverture — son contenu se retrouve alors compressé sous la hauteur minimale de ses
    widgets (cases à cocher illisibles, texte superposé). SitesTab et AppsTab sont les deux
    onglets dont le contenu grandit avec les données (catégories de sites, applications
    détectées) et peuvent dépasser la fenêtre ; le scroll évite la compression quel que soit
    le nombre d'éléments, plutôt qu'une taille minimale fixe qui redeviendrait insuffisante.
    """
    outer = QVBoxLayout(container)
    outer.setContentsMargins(0, 0, 0, 0)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    outer.addWidget(scroll)

    content = QWidget()
    scroll.setWidget(content)
    return QVBoxLayout(content)


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

        # Trouvé en usage réel (voir SUIVI.md) : configurer les 7 jours un par un est
        # répétitif quand le parent veut le même horaire toute la semaine, ou juste en
        # semaine/le week-end. Ces boutons pré-remplissent plusieurs jours d'un coup — les
        # cases et horaires par jour restent modifiables individuellement après coup, rien
        # n'est retiré de la finesse existante.
        layout.addWidget(small_label(self.i18n("settings.quick_apply")))
        quick_row = QHBoxLayout()
        self.quick_start = QTimeEdit(QTime(16, 0))
        self.quick_start.setDisplayFormat("HH:mm")
        self.quick_end = QTimeEdit(QTime(20, 0))
        self.quick_end.setDisplayFormat("HH:mm")
        quick_row.addWidget(self.quick_start)
        quick_row.addWidget(self.quick_end)
        layout.addLayout(quick_row)

        quick_buttons_row = QHBoxLayout()
        whole_week_button = QPushButton(self.i18n("settings.apply_whole_week"))
        whole_week_button.setObjectName("secondary")
        whole_week_button.clicked.connect(lambda: self._apply_quick(range(7)))
        quick_buttons_row.addWidget(whole_week_button)

        weekdays_button = QPushButton(self.i18n("settings.apply_weekdays"))
        weekdays_button.setObjectName("secondary")
        weekdays_button.clicked.connect(lambda: self._apply_quick(range(0, 5)))
        quick_buttons_row.addWidget(weekdays_button)

        weekend_button = QPushButton(self.i18n("settings.apply_weekend"))
        weekend_button.setObjectName("secondary")
        weekend_button.clicked.connect(lambda: self._apply_quick(range(5, 7)))
        quick_buttons_row.addWidget(weekend_button)
        layout.addLayout(quick_buttons_row)

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

    def _apply_quick(self, day_indices: range) -> None:
        start_time = self.quick_start.time()
        end_time = self.quick_end.time()
        for day_index in day_indices:
            checkbox, start_edit, end_edit = self._day_widgets[day_index]
            checkbox.setChecked(True)
            start_edit.setTime(start_time)
            end_edit.setTime(end_time)

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
        self._domain_checkboxes: dict[str, QCheckBox] = {}
        self._sections: list[CollapsibleSection] = []

        layout = _scrollable_layout(self)

        title_row = QHBoxLayout()
        title_row.addWidget(heading(self.i18n("settings.blocked_sites"), "h2"))
        title_row.addWidget(HelpButton(self.i18n("help.what_is_blocking"), self.i18n("help.blocking_explanation")))
        title_row.addStretch(1)
        layout.addLayout(title_row)

        # Trouvé en usage réel (voir SUIVI.md) : une case à cocher par catégorie entière ne
        # montrait jamais quels sites précis elle bloquait, ni ne permettait d'en retirer un
        # seul. Une case par site (regroupées par catégorie, comme AppsTab) rend le contenu
        # visible et modifiable individuellement. Section repliable + "Tout sélectionner"
        # dans l'en-tête (visible même repliée) pour retrouver un bascule rapide de toute la
        # catégorie sans perdre la visibilité individuelle.
        for category, domains in CATEGORIES.items():
            section = CollapsibleSection(
                self.i18n(f"settings.category_{category}"), self.i18n("settings.select_all")
            )
            layout.addWidget(section)
            self._sections.append(section)
            for domain in domains:
                checkbox = QCheckBox(domain)
                checkbox.toggled.connect(lambda checked, d=domain, c=category: self._toggle_domain(d, c, checked))
                section.add(checkbox)
                self._domain_checkboxes[domain] = checkbox

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

        for domain, checkbox in self._domain_checkboxes.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(domain in blocked_domains)
            checkbox.blockSignals(False)
        # blockSignals() ci-dessus empêche aussi la mise à jour de la case "Tout sélectionner"
        # de chaque section (qui écoute le même signal) — rafraîchie explicitement ici.
        for section in self._sections:
            section.refresh_select_all()

        predefined_domains = {d for domains in CATEGORIES.values() for d in domains}
        self.custom_list.clear()
        for domain in sorted(blocked_domains - predefined_domains):
            self.custom_list.addItem(domain)

    def _toggle_domain(self, domain: str, category: str, checked: bool) -> None:
        session = get_session()
        try:
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

        layout = _scrollable_layout(self)

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
        # `split() != [name]` couvre tous les blancs (tabulation, saut de ligne collé depuis
        # un autre document), pas seulement l'espace : un nom contenant un blanc ne
        # correspondra jamais à un `proc.info["name"]`, la règle serait silencieusement morte.
        if not name or name.split() != [name]:
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
