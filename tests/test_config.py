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

from mintguard.config import Config, DEFAULT_CONFIG


def test_defaults_when_no_file(tmp_path):
    config = Config(config_path=tmp_path / "does_not_exist.json")
    assert config.get("app.language") == "auto"
    assert config.get("database.path") == DEFAULT_CONFIG["database"]["path"]


def test_user_config_overrides_defaults(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"app": {"language": "fr"}}), encoding="utf-8")

    config = Config(config_path=config_file)
    assert config.get("app.language") == "fr"
    # Les autres clés restent celles par défaut (deep merge)
    assert config.get("app.theme") == "auto"
    assert config.get("database.path") == DEFAULT_CONFIG["database"]["path"]


def test_invalid_json_falls_back_to_defaults(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text("{not valid json", encoding="utf-8")

    config = Config(config_path=config_file)
    assert config.get("app.language") == "auto"


def test_get_unknown_key_returns_fallback(tmp_path):
    config = Config(config_path=tmp_path / "does_not_exist.json")
    assert config.get("does.not.exist", "fallback") == "fallback"
