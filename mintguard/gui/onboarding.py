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

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from mintguard.backend.child_setup import create_child_with_age_preset
from mintguard.backend.system_users import list_candidate_usernames
from mintguard.db.database import get_session
from mintguard.db.models import Child, ParentConfig
from mintguard.gui.widgets import Card, HelpButton, heading, small_label
from mintguard.locales.loader import I18nLoader
from mintguard.utils.security import hash_pin
from mintguard.utils.validators import is_valid_pin

STEP_COUNT = 6


class OnboardingWizard(QWidget):
    """Assistant de première configuration en 6 étapes (~2 min), cf. STRATEGIE_UX_UI.html
    section 'Onboarding pour Parents Novices'. Émet `finished` une fois la protection activée."""

    finished = pyqtSignal()

    def __init__(self, i18n: I18nLoader, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.data = {"name": "", "username": "", "age": 10, "age_bracket": "young", "pin": ""}

        self._age_group: QButtonGroup | None = None
        self._radio_young: QRadioButton | None = None
        self._radio_teen: QRadioButton | None = None
        self._child_error: QLabel | None = None
        self._pin_error: QLabel | None = None

        layout = QVBoxLayout(self)
        self.step_label = small_label("")
        layout.addWidget(self.step_label)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, stretch=1)

        for build_page in (
            self._build_welcome_page,
            self._build_child_page,
            self._build_quick_config_page,
            self._build_pin_page,
            self._build_how_it_works_page,
            self._build_success_page,
        ):
            self.stack.addWidget(build_page())

        self._update_step_indicator()

    # -- Navigation -----------------------------------------------------

    def _update_step_indicator(self) -> None:
        index = self.stack.currentIndex()
        self.step_label.setText(self.i18n("onboarding.step_indicator").format(index + 1, STEP_COUNT))

    def _go_to(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self._update_step_indicator()

    def _go_next(self) -> None:
        index = self.stack.currentIndex()
        if index == 1 and not self._validate_child_page():
            return
        if index == 2:
            self._apply_age_bracket_selection()
        if index == 3 and not self._validate_pin_page():
            return
        self._go_to(index + 1)

    def _go_back(self) -> None:
        self._go_to(self.stack.currentIndex() - 1)

    # -- Page 1: Bienvenue ------------------------------------------------

    def _build_welcome_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(heading(self.i18n("onboarding.welcome.title"), "h1"))
        subtitle = heading(self.i18n("onboarding.welcome.subtitle"), "h3")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        layout.addStretch(1)

        start_button = QPushButton(self.i18n("common.start"))
        start_button.clicked.connect(self._go_next)
        layout.addWidget(start_button)
        return page

    # -- Page 2: Compte enfant --------------------------------------------

    def _build_child_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(heading(self.i18n("onboarding.child.title"), "h2"))

        layout.addWidget(small_label(self.i18n("onboarding.child.name_label")))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        layout.addWidget(small_label(self.i18n("onboarding.child.username_label")))
        self.username_input = QComboBox()
        self.username_input.setEditable(True)
        # Comptes Linux locaux detectes (UID standard, pas systeme) : un parent novice ne
        # connait pas toujours le nom exact de la session de son enfant. Liste vide hors
        # Linux ou si la detection echoue - champ editable, saisie manuelle toujours possible.
        self.username_input.addItems(list_candidate_usernames())
        self.username_input.setCurrentText("")
        layout.addWidget(self.username_input)
        layout.addWidget(small_label(self.i18n("onboarding.child.username_hint")))

        layout.addWidget(small_label(self.i18n("onboarding.child.age_label")))
        self.age_input = QSpinBox()
        self.age_input.setRange(4, 18)
        self.age_input.setValue(self.data["age"])
        layout.addWidget(self.age_input)

        self._child_error = small_label("")
        self._child_error.setObjectName("danger")
        self._child_error.hide()
        layout.addWidget(self._child_error)

        layout.addStretch(1)
        layout.addLayout(self._nav_row(back=True, next_label=self.i18n("common.next")))
        return page

    def _validate_child_page(self) -> bool:
        name = self.name_input.text().strip()
        username = self.username_input.currentText().strip()
        if not name or not username:
            self._child_error.setText(self.i18n("onboarding.child.error_required"))
            self._child_error.show()
            return False
        # Trouve en usage reel (voir SUIVI.md) : sans cette verification, un nom de compte
        # deja utilise par un autre enfant provoquait une IntegrityError SQLite non rattrapee
        # au moment de _persist() (page Succes), plantant toute l'application.
        if self._username_already_used(username):
            self._child_error.setText(self.i18n("add_child.error_duplicate"))
            self._child_error.show()
            return False
        self._child_error.hide()
        self.data["name"] = name
        self.data["username"] = username
        self.data["age"] = self.age_input.value()
        return True

    @staticmethod
    def _username_already_used(username: str) -> bool:
        session = get_session()
        try:
            return session.query(Child).filter_by(username=username).first() is not None
        finally:
            session.close()

    # -- Page 3: Configuration rapide -------------------------------------

    def _build_quick_config_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(heading(self.i18n("onboarding.quick_config.title"), "h2"))
        subtitle = small_label(self.i18n("onboarding.quick_config.subtitle"))
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self._age_group = QButtonGroup(page)

        young_card = Card()
        self._radio_young = QRadioButton(self.i18n("onboarding.quick_config.profile_young"))
        young_card.add(self._radio_young)
        young_card.add(small_label(self.i18n("onboarding.quick_config.profile_young_desc")))
        self._age_group.addButton(self._radio_young)
        layout.addWidget(young_card)

        teen_card = Card()
        self._radio_teen = QRadioButton(self.i18n("onboarding.quick_config.profile_teen"))
        teen_card.add(self._radio_teen)
        teen_card.add(small_label(self.i18n("onboarding.quick_config.profile_teen_desc")))
        self._age_group.addButton(self._radio_teen)
        layout.addWidget(teen_card)

        layout.addStretch(1)
        layout.addLayout(self._nav_row(back=True, next_label=self.i18n("common.next")))
        return page

    def _apply_age_bracket_selection(self) -> None:
        # Pré-sélection intelligente selon l'âge saisi à l'étape précédente,
        # modifiable par le parent avant de continuer.
        if self._radio_young.isChecked():
            self.data["age_bracket"] = "young"
        elif self._radio_teen.isChecked():
            self.data["age_bracket"] = "teen"
        else:
            bracket = "young" if self.data["age"] <= 12 else "teen"
            self.data["age_bracket"] = bracket
            (self._radio_young if bracket == "young" else self._radio_teen).setChecked(True)

    # -- Page 4: Code de sécurité ------------------------------------------

    def _build_pin_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        title_row = QHBoxLayout()
        title_row.addWidget(heading(self.i18n("onboarding.pin.title"), "h2"))
        title_row.addWidget(
            HelpButton(self.i18n("help.why_pin_title"), self.i18n("help.why_pin_explanation"))
        )
        title_row.addStretch(1)
        layout.addLayout(title_row)

        subtitle = small_label(self.i18n("onboarding.pin.subtitle"))
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addWidget(small_label(self.i18n("onboarding.pin.pin_label")))
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setMaxLength(8)
        layout.addWidget(self.pin_input)

        layout.addWidget(small_label(self.i18n("onboarding.pin.confirm_label")))
        self.pin_confirm_input = QLineEdit()
        self.pin_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_confirm_input.setMaxLength(8)
        layout.addWidget(self.pin_confirm_input)

        self._pin_error = small_label("")
        self._pin_error.setObjectName("danger")
        self._pin_error.hide()
        layout.addWidget(self._pin_error)

        layout.addStretch(1)
        layout.addLayout(self._nav_row(back=True, next_label=self.i18n("common.next")))
        return page

    def _validate_pin_page(self) -> bool:
        pin = self.pin_input.text()
        confirm = self.pin_confirm_input.text()
        if not is_valid_pin(pin):
            self._pin_error.setText(self.i18n("onboarding.pin.error_invalid"))
            self._pin_error.show()
            return False
        if pin != confirm:
            self._pin_error.setText(self.i18n("onboarding.pin.error_mismatch"))
            self._pin_error.show()
            return False
        self._pin_error.hide()
        self.data["pin"] = pin
        return True

    # -- Page 5: Comment ça marche ------------------------------------------

    def _build_how_it_works_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(heading(self.i18n("onboarding.how_it_works.title"), "h2"))
        for key in ("step1", "step2", "step3", "step4"):
            label = small_label(f"→ {self.i18n(f'onboarding.how_it_works.{key}')}")
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addStretch(1)
        layout.addLayout(self._nav_row(back=True, next_label=self.i18n("common.next")))
        return page

    # -- Page 6: Succès -------------------------------------------------

    def _build_success_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(heading(self.i18n("onboarding.success.title"), "h1"))

        self._success_subtitle = heading("", "h3")
        self._success_subtitle.setWordWrap(True)
        layout.addWidget(self._success_subtitle)
        layout.addStretch(1)

        finish_button = QPushButton(self.i18n("onboarding.success.cta"))
        finish_button.clicked.connect(self._finish)
        layout.addWidget(finish_button)

        self.stack.currentChanged.connect(self._maybe_refresh_success_page)
        return page

    def _maybe_refresh_success_page(self, index: int) -> None:
        if index == 5:
            self._persist()
            self._success_subtitle.setText(
                self.i18n("onboarding.success.subtitle").format(self.data["name"])
            )

    # -- Persistance ------------------------------------------------------

    def _persist(self) -> None:
        """Crée le profil enfant, applique le préréglage d'âge, enregistre le PIN parent."""
        create_child_with_age_preset(
            self.data["name"], self.data["username"], self.data["age"], self.data["age_bracket"]
        )

        session = get_session()
        try:
            session.merge(ParentConfig(key="parent_pin_hash", value=hash_pin(self.data["pin"])))
            session.merge(ParentConfig(key="onboarding_complete", value="1"))
            session.commit()
        finally:
            session.close()

    def _finish(self) -> None:
        self.finished.emit()

    # -- Helpers ----------------------------------------------------------

    def _nav_row(self, back: bool, next_label: str) -> QHBoxLayout:
        row = QHBoxLayout()
        if back:
            back_button = QPushButton(self.i18n("common.back"))
            back_button.setObjectName("secondary")
            back_button.clicked.connect(self._go_back)
            row.addWidget(back_button)
        row.addStretch(1)
        next_button = QPushButton(next_label)
        next_button.clicked.connect(self._go_next)
        row.addWidget(next_button)
        return row
