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

"""Détection des comptes Linux locaux plausibles pour un enfant, pour proposer un menu
déroulant plutôt qu'un champ de saisie libre à l'onboarding/l'ajout d'enfant (un parent
novice ne connaît pas toujours le nom exact du compte de session de son enfant).
"""

import getpass
import logging

logger = logging.getLogger("mintguard.backend.system_users")

# Convention Debian/Ubuntu/Mint (/etc/login.defs UID_MIN/UID_MAX) : les comptes humains
# créés via l'outil "Utilisateurs" démarrent à 1000, les comptes système restent en dessous.
MIN_UID = 1000
MAX_UID = 60000
NOLOGIN_SHELLS = {"/usr/sbin/nologin", "/sbin/nologin", "/bin/false", ""}


def list_candidate_usernames(exclude: set[str] | None = None) -> list[str]:
    """Liste triée des comptes locaux plausibles pour un enfant. Exclut le compte qui
    exécute la GUI (le parent) et tout nom passé dans `exclude` (ex: enfants déjà configurés).

    Retourne une liste vide hors Linux (module `pwd` absent, ex: dev Windows) ou en cas
    d'erreur système — le parent garde toujours la main pour taper un nom manuellement
    (voir le champ éditable dans onboarding.py/add_child_dialog.py).
    """
    try:
        import pwd
    except ImportError:
        return []

    exclude = set(exclude or ())
    try:
        exclude.add(getpass.getuser())
    except Exception:
        pass

    try:
        entries = pwd.getpwall()
    except Exception as e:
        logger.warning("Impossible de lister les comptes système: %s", e)
        return []

    candidates = {
        entry.pw_name
        for entry in entries
        if MIN_UID <= entry.pw_uid <= MAX_UID
        and entry.pw_shell not in NOLOGIN_SHELLS
        and entry.pw_name not in exclude
    }
    return sorted(candidates)
