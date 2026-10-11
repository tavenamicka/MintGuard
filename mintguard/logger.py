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

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from mintguard.config import get_config

# Aucune rotation externe (logrotate) n'est installée : le fichier est plafonné ici.
_MAX_LOG_BYTES = 5 * 1024 * 1024
_LOG_BACKUPS = 3


def setup_logging(name: str = "mintguard") -> logging.Logger:
    """Configure et retourne le logger MintGuard (fichier + console).

    Les mêmes destinations sont attachées au logger parent "mintguard" : les modules
    (`mintguard.backend.dns`, `mintguard.backend.firewall`...) n'avaient jusqu'ici aucun
    gestionnaire - leurs avertissements n'atteignaient que le journal système via le repli
    de Python, et leurs messages d'information étaient perdus. Le fichier de log tourne à
    5 Mo (3 archives) au lieu de grossir indéfiniment.
    """
    config = get_config()
    level = getattr(logging, str(config.get("logging.level", "INFO")).upper(), logging.INFO)
    log_dir = Path(config.get("logging.path", "/var/log/mintguard/"))

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    handlers: list[logging.Handler] = []
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / f"{name}.log", maxBytes=_MAX_LOG_BYTES, backupCount=_LOG_BACKUPS, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    except OSError:
        file_handler = None

    for handler in handlers:
        logger.addHandler(handler)
    package_logger = logging.getLogger("mintguard")
    if name != "mintguard" and not package_logger.handlers:
        package_logger.setLevel(level)
        for handler in handlers:
            package_logger.addHandler(handler)

    if file_handler is None:
        logger.warning("Impossible d'écrire dans %s, logging fichier désactivé", log_dir)
    return logger
