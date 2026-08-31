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
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("mintguard.locales")

SUPPORTED_LANGUAGES = ("fr", "en", "de", "es")
DEFAULT_LANGUAGE = "en"


def detect_system_language() -> str:
    """Détecte la langue depuis les variables d'environnement système (LANG, LC_ALL)."""
    for var in ("LANGUAGE", "LC_ALL", "LANG"):
        value = os.environ.get(var)
        if not value:
            continue
        code = value.split(":")[0].split(".")[0].split("_")[0].lower()
        if code in SUPPORTED_LANGUAGES:
            return code
    return DEFAULT_LANGUAGE


class I18nLoader:
    """Charge les traductions multilingues depuis les fichiers JSON de locales/."""

    def __init__(self, lang: Optional[str] = None):
        self.lang = DEFAULT_LANGUAGE
        self.translations: Dict[str, Any] = {}
        self.load_language(lang or detect_system_language())

    def load_language(self, lang: str) -> bool:
        """Charge un fichier de langue, avec fallback vers l'anglais si absent."""
        if lang not in SUPPORTED_LANGUAGES:
            logger.warning("Langue non supportée: %s, fallback vers %s", lang, DEFAULT_LANGUAGE)
            lang = DEFAULT_LANGUAGE

        locale_path = Path(__file__).parent / f"{lang}.json"
        if not locale_path.exists():
            logger.warning("Fichier de langue introuvable: %s, fallback vers %s", locale_path, DEFAULT_LANGUAGE)
            locale_path = Path(__file__).parent / f"{DEFAULT_LANGUAGE}.json"
            lang = DEFAULT_LANGUAGE

        try:
            with open(locale_path, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
            self.lang = lang
            return True
        except (OSError, json.JSONDecodeError) as e:
            logger.error("Erreur de chargement du fichier de langue %s: %s", locale_path, e)
            return False

    def get(self, key: str, fallback: str = "") -> str:
        """Récupère une traduction par clé pointée (ex: 'dashboard.title')."""
        value: Any = self.translations
        for part in key.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return fallback
        return str(value) if value is not None else fallback

    def __call__(self, key: str) -> str:
        return self.get(key)


_i18n_instance: Optional[I18nLoader] = None


def get_i18n(lang: Optional[str] = None) -> I18nLoader:
    """Obtient (ou crée) l'instance i18n globale."""
    global _i18n_instance
    if _i18n_instance is None or (lang is not None and lang != _i18n_instance.lang):
        _i18n_instance = I18nLoader(lang)
    return _i18n_instance


# Usage: from mintguard.locales.loader import get_i18n
#        _ = get_i18n()
#        _("dashboard.title")
