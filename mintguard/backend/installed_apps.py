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

"""Détection des applications installées (fichiers `.desktop`, mécanisme standard des
environnements de bureau Linux) pour proposer une liste plutôt qu'un champ de saisie libre
dans Settings > Applications — même logique que `system_users.py` pour les comptes.

Classées dans les mêmes catégories que `site_categories.py` (social/entertainment/gaming)
via le champ `Categories=` (spec freedesktop.org), pour un affichage cohérent avec l'onglet
Sites. Une application qui ne correspond à aucune de ces 3 catégories n'est pas proposée ici
(la saisie manuelle du nom de processus reste le filet de sécurité, comme pour les sites).

Limite connue et acceptée : le nom de processus déduit de `Exec=` ne correspond pas toujours
exactement au nom réellement observé par `ProcessMonitor` (ex: un script de lancement qui
exécute un binaire différent) — best effort, pas une garantie.
"""

import configparser
import logging
from pathlib import Path

logger = logging.getLogger("mintguard.backend.installed_apps")

DESKTOP_DIRS = [
    Path("/usr/share/applications"),
    Path("/usr/local/share/applications"),
    Path.home() / ".local/share/applications",
    Path("/var/lib/snapd/desktop/applications"),
    Path("/var/lib/flatpak/exports/share/applications"),
]

# Categories principales/additionnelles freedesktop.org mappees sur les buckets deja
# utilises pour les sites bloques (site_categories.CATEGORIES).
CATEGORY_KEYWORDS: dict[str, set[str]] = {
    "gaming": {"Game"},
    "entertainment": {"AudioVideo", "Video", "Audio", "Player"},
    "social": {"InstantMessaging", "Chat", "VideoConference", "Email"},
}

# Utilitaires systeme/reglages : jamais des "applications" qu'un parent voudrait bloquer.
EXCLUDED_CATEGORIES = {"Settings", "System", "HardwareSettings", "Core", "ConsoleOnly"}


def _process_name_from_exec(exec_line: str) -> str:
    tokens = exec_line.split()
    if not tokens:
        return ""
    return Path(tokens[0]).name.lower()


def _category_for(categories: set[str]) -> str | None:
    for bucket, keywords in CATEGORY_KEYWORDS.items():
        if categories & keywords:
            return bucket
    return None


def _parse_desktop_file(path: Path) -> dict | None:
    parser = configparser.RawConfigParser(strict=False)
    try:
        parser.read(path, encoding="utf-8")
    except (OSError, UnicodeDecodeError, configparser.Error) as e:
        logger.debug("Impossible de lire %s: %s", path, e)
        return None

    if "Desktop Entry" not in parser:
        return None
    entry = parser["Desktop Entry"]

    if entry.get("Type", "Application") != "Application":
        return None
    if entry.get("NoDisplay", "false").strip().lower() == "true":
        return None

    name = entry.get("Name", "").strip()
    exec_line = entry.get("Exec", "").strip()
    categories = {c for c in entry.get("Categories", "").split(";") if c}

    if not name or not exec_line or categories & EXCLUDED_CATEGORIES:
        return None

    process_name = _process_name_from_exec(exec_line)
    if not process_name:
        return None

    return {"name": name, "process_name": process_name, "categories": categories}


def list_installed_apps() -> dict[str, list[tuple[str, str]]]:
    """Retourne `{"social": [...], "entertainment": [...], "gaming": [...]}`, chaque liste
    contenant des tuples `(process_name, nom_affiché)` triés par nom, sans doublon de
    process_name. Dictionnaire de listes vides si aucun répertoire `.desktop` trouvé (ex:
    dev Windows) ou en cas d'erreur — la saisie manuelle reste toujours possible côté GUI.
    """
    seen: set[str] = set()
    result: dict[str, list[tuple[str, str]]] = {bucket: [] for bucket in CATEGORY_KEYWORDS}

    for directory in DESKTOP_DIRS:
        if not directory.is_dir():
            continue
        try:
            desktop_files = sorted(directory.glob("*.desktop"))
        except OSError as e:
            logger.warning("Impossible de lister %s: %s", directory, e)
            continue

        for desktop_file in desktop_files:
            entry = _parse_desktop_file(desktop_file)
            if entry is None:
                continue
            bucket = _category_for(entry["categories"])
            if bucket is None or entry["process_name"] in seen:
                continue
            seen.add(entry["process_name"])
            result[bucket].append((entry["process_name"], entry["name"]))

    for apps in result.values():
        apps.sort(key=lambda item: item[1].lower())
    return result
