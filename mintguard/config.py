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

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "app": {
        "language": "auto",
        "locale_fallback": "en",
        "theme": "auto",
    },
    "database": {
        "path": "/var/lib/mintguard/mintguard.db",
    },
    "dns": {
        "enabled": True,
        # 5354, PAS 5353 (port mDNS/Avahi standard, deja utilise par
        # avahi-daemon sur Linux Mint) - voir SUIVI.md Phase 3.
        "listen_port": 5354,
        # Repertoire separe de /var/lib/mintguard (verrouille 2770 pour la
        # BD/PIN) : dnsmasq tourne en utilisateur non-privilegie et ne
        # pourrait pas traverser un repertoire dont il n'a pas le droit
        # d'execution, meme si le fichier lui-meme etait lisible - voir
        # SUIVI.md Phase 3 (5e defaut de conception).
        # ".conf" et non ".hosts" : fragment de configuration dnsmasq
        # (`address=/domaine/0.0.0.0`), seul format qui bloque aussi les
        # sous-domaines - voir DNSController.
        "blocklist_path": "/var/lib/mintguard-dns/blocklist.conf",
        "refresh_interval": 30,
    },
    "monitoring": {
        "process_check_interval": 5,
        "session_check_interval": 60,
        # Delai entre le moment ou une session sort de sa plage horaire/depasse son quota et
        # la fermeture reelle (loginctl terminate-user) - laisse a l'enfant le temps de
        # sauvegarder son travail, voir Scheduler._grace_deadlines. Superieur a
        # session_check_interval pour garantir au moins un cycle complet de battement.
        "grace_period_seconds": 90,
    },
    "child_tray": {
        "poll_interval_seconds": 15,
        # Seuils (minutes restantes) auxquels mintguard-child-tray affiche un avertissement,
        # un par session (voir child_tray.py) - pas de compte a rebours seconde par seconde,
        # juste des paliers, coherent avec le polling (pas un besoin temps reel).
        "warning_thresholds_minutes": [10, 5, 1],
    },
    "logging": {
        "level": "INFO",
        "path": "/var/log/mintguard/",
    },
}

# Chemin du fichier config, avec override possible via MINTGUARD_CONFIG_PATH
# (utile en dev, notamment hors Linux où /etc/mintguard n'existe pas).
CONFIG_PATH = Path(os.environ.get("MINTGUARD_CONFIG_PATH", "/etc/mintguard/config.json"))


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


class Config:
    """Charge la configuration MintGuard depuis config.json, avec fallback sur les défauts."""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or CONFIG_PATH
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return dict(DEFAULT_CONFIG)
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            return _deep_merge(DEFAULT_CONFIG, user_config)
        except (OSError, json.JSONDecodeError):
            return dict(DEFAULT_CONFIG)

    def get(self, key: str, fallback: Any = None) -> Any:
        """Récupère une valeur par clé pointée (ex: 'app.language')."""
        value: Any = self.data
        for part in key.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return fallback
        return value if value is not None else fallback


_config_instance: Config | None = None


def get_config(config_path: Path | None = None) -> Config:
    """Obtient (ou crée) l'instance de configuration globale."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance
