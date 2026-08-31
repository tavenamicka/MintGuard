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

from mintguard.locales.loader import I18nLoader, SUPPORTED_LANGUAGES, detect_system_language


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_all_languages_load(lang):
    i18n = I18nLoader(lang)
    assert i18n.lang == lang
    assert i18n("app.name") == "MintGuard"


def test_get_nested_key():
    i18n = I18nLoader("fr")
    assert i18n.get("dashboard.title") == "Tableau de Bord"


def test_get_unknown_key_returns_fallback():
    i18n = I18nLoader("fr")
    assert i18n.get("does.not.exist", "fallback") == "fallback"


def test_unsupported_language_falls_back_to_english():
    i18n = I18nLoader("xx")
    assert i18n.lang == "en"


def test_detect_system_language_defaults_to_english(monkeypatch):
    monkeypatch.delenv("LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LANGUAGE", raising=False)
    assert detect_system_language() == "en"


def test_detect_system_language_from_lang_env(monkeypatch):
    monkeypatch.setenv("LANG", "fr_FR.UTF-8")
    assert detect_system_language() == "fr"


def test_all_languages_have_same_keys():
    reference = I18nLoader("en").translations

    def flatten_keys(d, prefix=""):
        keys = set()
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                keys |= flatten_keys(v, full_key)
            else:
                keys.add(full_key)
        return keys

    reference_keys = flatten_keys(reference)
    for lang in SUPPORTED_LANGUAGES:
        keys = flatten_keys(I18nLoader(lang).translations)
        assert keys == reference_keys, f"Clés manquantes/différentes pour '{lang}'"
