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

from PyQt6.QtWidgets import QApplication  # noqa: E402

from mintguard.db.database import get_session, init_db  # noqa: E402
from mintguard.db.models import BlockedSite, Child, ParentConfig, TimeRule  # noqa: E402
from mintguard.gui.onboarding import OnboardingWizard  # noqa: E402
from mintguard.locales.loader import I18nLoader  # noqa: E402
from mintguard.utils.security import verify_pin  # noqa: E402


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return QApplication.instance() or QApplication([])


def make_wizard() -> OnboardingWizard:
    return OnboardingWizard(I18nLoader("fr"))


def test_wizard_has_six_pages():
    wizard = make_wizard()
    assert wizard.stack.count() == 6


def test_step_indicator_starts_at_one():
    wizard = make_wizard()
    assert wizard.step_label.text() == "Étape 1 sur 6"


def test_child_page_rejects_empty_fields():
    wizard = make_wizard()
    wizard.name_input.setText("")
    wizard.username_input.setCurrentText("")
    assert wizard._validate_child_page() is False
    # isHidden() reflète l'appel explicite à show()/hide() dans le code, contrairement
    # à isVisible() qui dépend aussi de la fenêtre parente (jamais affichée en test).
    assert wizard._child_error.isHidden() is False


def test_child_page_accepts_valid_input():
    wizard = make_wizard()
    wizard.name_input.setText("Alice")
    wizard.username_input.setCurrentText("alice")
    wizard.age_input.setValue(9)
    assert wizard._validate_child_page() is True
    assert wizard.data["name"] == "Alice"
    assert wizard.data["username"] == "alice"
    assert wizard.data["age"] == 9


def test_child_page_rejects_username_already_used_by_another_child():
    # Trouve en usage reel (voir SUIVI.md) : sans cette verification, l'onboarding plantait
    # (IntegrityError SQLite non rattrapee) en tentant de reutiliser un nom de compte deja
    # associe a un autre enfant.
    session = get_session()
    try:
        session.add(Child(name="Test", username="mintguard-test-child", age=10))
        session.commit()
    finally:
        session.close()

    wizard = make_wizard()
    wizard.name_input.setText("Elisa")
    wizard.username_input.setCurrentText("mintguard-test-child")
    assert wizard._validate_child_page() is False
    assert wizard._child_error.isHidden() is False


def test_age_bracket_defaults_to_young_for_child():
    wizard = make_wizard()
    wizard.data["age"] = 9
    wizard._apply_age_bracket_selection()
    assert wizard.data["age_bracket"] == "young"
    assert wizard._radio_young.isChecked()


def test_age_bracket_defaults_to_teen_for_teenager():
    wizard = make_wizard()
    wizard.data["age"] = 15
    wizard._apply_age_bracket_selection()
    assert wizard.data["age_bracket"] == "teen"
    assert wizard._radio_teen.isChecked()


def test_pin_page_rejects_non_digit_pin():
    wizard = make_wizard()
    wizard.pin_input.setText("abcd")
    wizard.pin_confirm_input.setText("abcd")
    assert wizard._validate_pin_page() is False


def test_pin_page_rejects_mismatched_pins():
    wizard = make_wizard()
    wizard.pin_input.setText("1234")
    wizard.pin_confirm_input.setText("5678")
    assert wizard._validate_pin_page() is False


def test_pin_page_accepts_matching_valid_pins():
    wizard = make_wizard()
    wizard.pin_input.setText("1234")
    wizard.pin_confirm_input.setText("1234")
    assert wizard._validate_pin_page() is True
    assert wizard.data["pin"] == "1234"


def test_finished_signal_emitted():
    wizard = make_wizard()
    received = []
    wizard.finished.connect(lambda: received.append(True))
    wizard._finish()
    assert received == [True]


def test_persist_creates_child_rules_and_pin():
    wizard = make_wizard()
    wizard.data.update(name="Alice", username="alice", age=9, age_bracket="young", pin="1234")
    wizard._persist()

    session = get_session()
    try:
        child = session.query(Child).filter_by(username="alice").one()
        assert child.name == "Alice"

        rules = session.query(TimeRule).filter_by(child_id=child.id).all()
        assert len(rules) == 7

        sites = session.query(BlockedSite).all()
        assert {s.domain for s in sites} >= {"tiktok.com", "facebook.com", "steampowered.com"}

        onboarding_flag = session.query(ParentConfig).filter_by(key="onboarding_complete").one()
        assert onboarding_flag.value == "1"

        pin_hash = session.query(ParentConfig).filter_by(key="parent_pin_hash").one()
        assert verify_pin("1234", pin_hash.value) is True
    finally:
        session.close()
