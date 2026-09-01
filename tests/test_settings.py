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

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtCore import QTime, Qt  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from mintguard.backend.site_categories import SOCIAL_MEDIA_DOMAINS  # noqa: E402
from mintguard.db.database import get_session, init_db  # noqa: E402
from mintguard.db.models import BlockedApp, BlockedSite, Child, TimeRule  # noqa: E402
from mintguard.gui.settings import AppsTab, SettingsWindow, SitesTab, TimeTab  # noqa: E402
from mintguard.locales.loader import I18nLoader  # noqa: E402


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return QApplication.instance() or QApplication([])


def make_child() -> int:
    session = get_session()
    try:
        child = Child(name="Alice", username="alice", age=10)
        session.add(child)
        session.commit()
        return child.id
    finally:
        session.close()


# -- TimeTab --------------------------------------------------------------


def test_time_tab_starts_with_no_days_checked():
    child_id = make_child()
    tab = TimeTab(I18nLoader("fr"), child_id)
    assert all(not checkbox.isChecked() for checkbox, _, _ in tab._day_widgets)


def test_time_tab_save_persists_checked_days():
    child_id = make_child()
    tab = TimeTab(I18nLoader("fr"), child_id)

    checkbox, start_edit, end_edit = tab._day_widgets[0]
    checkbox.setChecked(True)
    start_edit.setTime(QTime(10, 0))
    end_edit.setTime(QTime(12, 0))
    tab._save()

    session = get_session()
    try:
        rules = session.query(TimeRule).filter_by(child_id=child_id).all()
        assert len(rules) == 1
        assert rules[0].day_of_week == 0
        assert rules[0].start_hour.hour == 10
        assert rules[0].end_hour.hour == 12
    finally:
        session.close()
    assert tab.saved_label.isHidden() is False


def test_time_tab_save_removes_unchecked_days():
    child_id = make_child()
    session = get_session()
    try:
        from datetime import time as dt_time

        session.add(TimeRule(child_id=child_id, day_of_week=2, start_hour=dt_time(9, 0), end_hour=dt_time(11, 0)))
        session.commit()
    finally:
        session.close()

    tab = TimeTab(I18nLoader("fr"), child_id)  # loads existing rule
    checkbox, _, _ = tab._day_widgets[2]
    assert checkbox.isChecked() is True
    checkbox.setChecked(False)
    tab._save()

    session = get_session()
    try:
        assert session.query(TimeRule).filter_by(child_id=child_id).count() == 0
    finally:
        session.close()


def test_time_tab_disabled_without_child():
    tab = TimeTab(I18nLoader("fr"), None)
    assert tab.isEnabled() is False


# -- SitesTab --------------------------------------------------------------


# Trouvé en usage réel (voir SUIVI.md) : une case par catégorie entière ne montrait jamais
# quels sites précis elle bloquait, ni ne permettait d'en retirer un seul. Remplacé par une
# case par site, regroupées par catégorie (comme AppsTab).


def test_sites_tab_shows_one_checkbox_per_reference_domain():
    tab = SitesTab(I18nLoader("fr"))
    assert set(SOCIAL_MEDIA_DOMAINS) <= set(tab._domain_checkboxes)


def test_sites_tab_toggle_single_domain_creates_row():
    tab = SitesTab(I18nLoader("fr"))
    tab._domain_checkboxes["tiktok.com"].setChecked(True)

    session = get_session()
    try:
        site = session.query(BlockedSite).filter_by(domain="tiktok.com").first()
        other_social = session.query(BlockedSite).filter_by(domain="facebook.com").first()
    finally:
        session.close()
    assert site is not None
    assert site.category == "social"
    assert other_social is None  # les autres sites de la categorie restent non bloques


def test_sites_tab_untoggle_single_domain_removes_row():
    tab = SitesTab(I18nLoader("fr"))
    tab._domain_checkboxes["tiktok.com"].setChecked(True)
    tab._domain_checkboxes["tiktok.com"].setChecked(False)

    session = get_session()
    try:
        count = session.query(BlockedSite).filter_by(domain="tiktok.com").count()
    finally:
        session.close()
    assert count == 0


def test_sites_tab_select_all_reflects_state_loaded_from_db():
    # Bug trouve en verification visuelle (voir SUIVI.md) : le blockSignals() utilise dans
    # _load() pour eviter des ecritures BD au chargement empechait aussi la case "Tout
    # selectionner" de chaque section de se mettre a jour - elle restait decochee meme quand
    # tous les sites d'une categorie etaient deja bloques en BD avant l'ouverture de l'onglet.
    session = get_session()
    try:
        for domain in ("youtube.com", "netflix.com", "twitch.tv"):  # toute la categorie "entertainment"
            session.add(BlockedSite(domain=domain, category="entertainment", blocked=True))
        session.commit()
    finally:
        session.close()

    tab = SitesTab(I18nLoader("fr"))
    entertainment_section = next(s for s in tab._sections if s._toggle_button.text() == "Divertissement")
    assert entertainment_section.select_all_checkbox.checkState() == Qt.CheckState.Checked


def test_sites_tab_add_valid_custom_site():
    tab = SitesTab(I18nLoader("fr"))
    tab.add_input.setText("example.com")
    tab._add_custom_site()

    session = get_session()
    try:
        site = session.query(BlockedSite).filter_by(domain="example.com").first()
    finally:
        session.close()
    assert site is not None
    assert site.category == "custom"
    assert tab.custom_list.count() == 1


def test_sites_tab_rejects_invalid_domain():
    tab = SitesTab(I18nLoader("fr"))
    tab.add_input.setText("not a domain")
    tab._add_custom_site()

    assert tab.error_label.isHidden() is False
    session = get_session()
    try:
        assert session.query(BlockedSite).count() == 0
    finally:
        session.close()


def test_sites_tab_remove_custom_site():
    tab = SitesTab(I18nLoader("fr"))
    tab.add_input.setText("example.com")
    tab._add_custom_site()
    tab.custom_list.setCurrentRow(0)
    tab._remove_selected_site()

    session = get_session()
    try:
        assert session.query(BlockedSite).filter_by(domain="example.com").first() is None
    finally:
        session.close()
    assert tab.custom_list.count() == 0


# -- AppsTab --------------------------------------------------------------
#
# Détection réelle (fichiers .desktop) plutôt qu'une liste figée (voir SUIVI.md) : les
# applis réellement détectées dépendent de la machine qui exécute les tests, donc
# `list_installed_apps` est mockée ici pour un résultat déterministe.

FAKE_DETECTED_APPS = {
    "social": [("thunderbird", "Thunderbird Mail")],
    "entertainment": [("rhythmbox", "Rhythmbox")],
    "gaming": [("supertux", "SuperTux")],
}


@pytest.fixture(autouse=True)
def fake_installed_apps(monkeypatch):
    import mintguard.gui.settings as settings_module

    monkeypatch.setattr(settings_module, "list_installed_apps", lambda: FAKE_DETECTED_APPS)


def test_apps_tab_groups_detected_apps_by_category():
    tab = AppsTab(I18nLoader("fr"))
    assert set(tab._app_checkboxes) == {"thunderbird", "rhythmbox", "supertux"}


def test_apps_tab_toggle_detected_app_creates_row():
    tab = AppsTab(I18nLoader("fr"))
    tab._app_checkboxes["supertux"].setChecked(True)

    session = get_session()
    try:
        app = session.query(BlockedApp).filter_by(app_name="supertux").first()
    finally:
        session.close()
    assert app is not None
    assert app.enabled is True


def test_apps_tab_untoggle_detected_app_removes_row():
    tab = AppsTab(I18nLoader("fr"))
    tab._app_checkboxes["supertux"].setChecked(True)
    tab._app_checkboxes["supertux"].setChecked(False)

    session = get_session()
    try:
        assert session.query(BlockedApp).filter_by(app_name="supertux").first() is None
    finally:
        session.close()


def test_apps_tab_no_apps_detected_shows_no_checkboxes(monkeypatch):
    import mintguard.gui.settings as settings_module

    monkeypatch.setattr(
        settings_module, "list_installed_apps", lambda: {"social": [], "entertainment": [], "gaming": []}
    )
    tab = AppsTab(I18nLoader("fr"))
    assert tab._app_checkboxes == {}


def test_apps_tab_add_valid_custom_app():
    tab = AppsTab(I18nLoader("fr"))
    tab.add_input.setText("telegram-desktop")
    tab._add_custom_app()

    session = get_session()
    try:
        app = session.query(BlockedApp).filter_by(app_name="telegram-desktop").first()
    finally:
        session.close()
    assert app is not None
    assert tab.custom_list.count() == 1


def test_apps_tab_rejects_name_with_spaces():
    tab = AppsTab(I18nLoader("fr"))
    tab.add_input.setText("not a process")
    tab._add_custom_app()

    assert tab.error_label.isHidden() is False
    session = get_session()
    try:
        assert session.query(BlockedApp).count() == 0
    finally:
        session.close()


def test_apps_tab_remove_custom_app():
    tab = AppsTab(I18nLoader("fr"))
    tab.add_input.setText("telegram-desktop")
    tab._add_custom_app()
    tab.custom_list.setCurrentRow(0)
    tab._remove_selected_app()

    session = get_session()
    try:
        assert session.query(BlockedApp).filter_by(app_name="telegram-desktop").first() is None
    finally:
        session.close()
    assert tab.custom_list.count() == 0


# -- SettingsWindow ---------------------------------------------------------


def test_settings_window_has_three_tabs():
    child_id = make_child()
    window = SettingsWindow(I18nLoader("fr"), child_id)
    assert window.tabs.count() == 3
    window.close()
