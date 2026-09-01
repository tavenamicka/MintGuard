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

"""Limitation des tentatives de saisie du code PIN parent.

Trouvé à l'analyse de sécurité : `PinDialog` acceptait un nombre illimité d'essais, et
fermer puis rouvrir la fenêtre repartait de zéro. Un PIN de 4 chiffres (le minimum autorisé
par `is_valid_pin`) tient en 10 000 combinaisons — largement à portée de quelqu'un qui a
accès à la session parent quelques dizaines de minutes, ce qui est précisément le scénario
contre lequel le PIN protège.

Le compteur est stocké en BD (`ParentConfig`) et non en mémoire : il doit survivre à la
fermeture de la fenêtre et au redémarrage de l'application, sinon il ne freine personne.
"""

from datetime import datetime, timedelta, timezone

from mintguard.db.database import session_scope
from mintguard.db.models import ParentConfig

ATTEMPTS_KEY = "pin_failed_attempts"
LOCKOUT_KEY = "pin_lockout_until"

# Nombre d'échecs tolérés avant le premier verrouillage. Assez large pour ne pas punir un
# parent qui se trompe de chiffre, assez bas pour rendre la recherche exhaustive inutile.
MAX_ATTEMPTS = 5
# Le délai double à chaque palier de MAX_ATTEMPTS échecs (30 s, 1 min, 2 min...) et sature :
# 10 000 essais demanderaient alors des semaines, sans jamais verrouiller définitivement le
# parent hors de ses réglages.
BASE_LOCKOUT_SECONDS = 30
MAX_LOCKOUT_SECONDS = 15 * 60


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get(session, key: str) -> str | None:
    row = session.query(ParentConfig).filter_by(key=key).first()
    return row.value if row is not None else None


def lockout_remaining() -> int:
    """Secondes restantes avant de pouvoir réessayer (0 si aucune attente en cours)."""
    with session_scope() as session:
        raw = _get(session, LOCKOUT_KEY)
    if not raw:
        return 0
    try:
        until = datetime.fromisoformat(raw)
    except ValueError:
        return 0
    return max(0, int((until - _utcnow()).total_seconds()))


def register_failure() -> int:
    """Enregistre un échec. Retourne le nombre de secondes d'attente imposées (0 si aucune)."""
    with session_scope() as session:
        try:
            attempts = int(_get(session, ATTEMPTS_KEY) or 0)
        except ValueError:
            attempts = 0
        attempts += 1

        wait = 0
        if attempts % MAX_ATTEMPTS == 0:
            steps = attempts // MAX_ATTEMPTS - 1
            wait = min(BASE_LOCKOUT_SECONDS * (2**steps), MAX_LOCKOUT_SECONDS)
            session.merge(
                ParentConfig(
                    key=LOCKOUT_KEY,
                    value=(_utcnow() + timedelta(seconds=wait)).isoformat(),
                )
            )

        session.merge(ParentConfig(key=ATTEMPTS_KEY, value=str(attempts)))
        session.commit()
    return wait


def reset() -> None:
    """Remet le compteur à zéro (PIN correct saisi, ou nouveau PIN défini)."""
    with session_scope() as session:
        session.merge(ParentConfig(key=ATTEMPTS_KEY, value="0"))
        session.merge(ParentConfig(key=LOCKOUT_KEY, value=""))
        session.commit()
