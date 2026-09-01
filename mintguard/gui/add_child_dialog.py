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

from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from mintguard.backend.child_setup import create_child_with_age_preset
from mintguard.backend.system_users import list_candidate_usernames
from mintguard.db.database import get_session
from mintguard.db.models import Child
from mintguard.gui.widgets import Card, heading, small_label
from mintguard.locales.loader import I18nLoader


class AddChildDialog(QDialog):
    """Ajoute un enfant supplémentaire après l'onboarding initial.

    Trouvé en usage réel (voir SUIVI.md) : la BD et le sélecteur du Dashboard supportaient
    déjà plusieurs enfants, mais rien dans l'interface ne permettait d'en ajouter un second —
    seul `OnboardingWizard` créait un enfant, une seule fois. Réutilise le même préréglage
    d'âge que l'onboarding (`create_child_with_age_preset`), pas de nouvelle étape PIN
    (le PIN est un réglage parent global, déjà défini).
    """

    def __init__(self, i18n: I18nLoader, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setWindowTitle(i18n("add_child.title"))
        self.setMinimumWidth(360)
        self.created_child_id: int | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(heading(i18n("add_child.title"), "h2"))

        layout.addWidget(small_label(i18n("onboarding.child.name_label")))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        layout.addWidget(small_label(i18n("onboarding.child.username_label")))
        self.username_input = QComboBox()
        self.username_input.setEditable(True)
        self.username_input.addItems(list_candidate_usernames(exclude=self._existing_child_usernames()))
        self.username_input.setCurrentText("")
        layout.addWidget(self.username_input)
        layout.addWidget(small_label(i18n("onboarding.child.username_hint")))

        layout.addWidget(small_label(i18n("onboarding.child.age_label")))
        self.age_input = QSpinBox()
        self.age_input.setRange(4, 18)
        self.age_input.setValue(10)
        self.age_input.valueChanged.connect(self._suggest_age_bracket)
        layout.addWidget(self.age_input)

        self._age_group = QButtonGroup(self)

        young_card = Card()
        self.radio_young = QRadioButton(i18n("onboarding.quick_config.profile_young"))
        young_card.add(self.radio_young)
        young_card.add(small_label(i18n("onboarding.quick_config.profile_young_desc")))
        self._age_group.addButton(self.radio_young)
        layout.addWidget(young_card)

        teen_card = Card()
        self.radio_teen = QRadioButton(i18n("onboarding.quick_config.profile_teen"))
        teen_card.add(self.radio_teen)
        teen_card.add(small_label(i18n("onboarding.quick_config.profile_teen_desc")))
        self._age_group.addButton(self.radio_teen)
        layout.addWidget(teen_card)
        self.radio_young.setChecked(True)

        self._error_label = QLabel("")
        self._error_label.setObjectName("danger")
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        layout.addWidget(self._error_label)

        buttons_row = QHBoxLayout()
        cancel_button = QPushButton(i18n("common.cancel"))
        cancel_button.setObjectName("secondary")
        cancel_button.clicked.connect(self.reject)
        buttons_row.addWidget(cancel_button)

        add_button = QPushButton(i18n("add_child.add_button"))
        add_button.clicked.connect(self._create)
        buttons_row.addWidget(add_button)
        layout.addLayout(buttons_row)

    @staticmethod
    def _existing_child_usernames() -> set[str]:
        session = get_session()
        try:
            return {c.username for c in session.query(Child).all()}
        finally:
            session.close()

    def _suggest_age_bracket(self, age: int) -> None:
        (self.radio_young if age <= 12 else self.radio_teen).setChecked(True)

    def _create(self) -> None:
        name = self.name_input.text().strip()
        username = self.username_input.currentText().strip()
        if not name or not username:
            self._error_label.setText(self.i18n("onboarding.child.error_required"))
            self._error_label.show()
            return

        if username in self._existing_child_usernames():
            self._error_label.setText(self.i18n("add_child.error_duplicate"))
            self._error_label.show()
            return

        age_bracket = "young" if self.radio_young.isChecked() else "teen"
        self.created_child_id = create_child_with_age_preset(name, username, self.age_input.value(), age_bracket)
        self.accept()

    @staticmethod
    def prompt(i18n: I18nLoader, parent=None) -> int | None:
        """Affiche le dialogue et retourne l'id du nouvel enfant, ou None si annulé."""
        dialog = AddChildDialog(i18n, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.created_child_id
        return None
