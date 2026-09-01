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

"""Création d'un enfant avec le préréglage d'âge (horaires + sites bloqués) appliqué.
Partagé entre `OnboardingWizard` (premier enfant) et `AddChildDialog` (enfants suivants —
la BD/le Dashboard supportaient déjà plusieurs enfants, mais rien dans l'interface ne
permettait d'en ajouter après l'onboarding initial) pour ne pas dupliquer cette logique.
"""

from datetime import time as dt_time

from mintguard.backend.site_categories import AGE_PRESETS, category_for_domain
from mintguard.db.database import get_session
from mintguard.db.models import BlockedSite, Child, TimeRule


class DuplicateUsernameError(ValueError):
    """Un enfant avec ce nom d'utilisateur existe déjà (contrainte UNIQUE sur `Child.username`)."""


def create_child_with_age_preset(name: str, username: str, age: int, age_bracket: str) -> int:
    """Crée l'enfant, applique le préréglage d'âge (7 `TimeRule`, `BlockedSite` par domaine
    déjà défini par catégorie). Retourne l'id du nouvel enfant.

    Lève `DuplicateUsernameError` plutôt que de laisser remonter l'`IntegrityError` SQLite
    brute — trouvé en usage réel (voir SUIVI.md) : un appelant qui oublie de vérifier les
    doublons en amont (c'était le cas de l'onboarding) plantait toute l'application au lieu
    d'afficher un message. Vérification défensive ici en plus de celle des appelants GUI,
    pour que cette fonction reste sûre quel que soit l'appelant.
    """
    session = get_session()
    try:
        if session.query(Child).filter_by(username=username).first() is not None:
            raise DuplicateUsernameError(username)

        child = Child(name=name, username=username, age=age)
        session.add(child)
        session.flush()

        preset = AGE_PRESETS[age_bracket]
        daily_hours = preset["daily_hours"]
        start = dt_time(16, 0)
        end = dt_time((16 + daily_hours) % 24, 0)
        for day in range(7):
            session.add(
                TimeRule(child_id=child.id, day_of_week=day, start_hour=start, end_hour=end, enabled=True)
            )

        for domain in preset["blocked_domains"]:
            if session.query(BlockedSite).filter_by(domain=domain).first() is None:
                session.add(BlockedSite(domain=domain, category=category_for_domain(domain), blocked=True))

        session.commit()
        return child.id
    finally:
        session.close()
