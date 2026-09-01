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

from mintguard.backend import installed_apps


def write_desktop_file(directory, filename, *, name, exec_line, categories, no_display=False, type_="Application"):
    content = (
        "[Desktop Entry]\n"
        f"Type={type_}\n"
        f"Name={name}\n"
        f"Exec={exec_line}\n"
        f"Categories={categories}\n"
    )
    if no_display:
        content += "NoDisplay=true\n"
    (directory / filename).write_text(content, encoding="utf-8")


def test_detects_game_entertainment_and_social_apps(tmp_path, monkeypatch):
    write_desktop_file(tmp_path, "supertux.desktop", name="SuperTux", exec_line="supertux2", categories="Game;")
    write_desktop_file(
        tmp_path, "vlc.desktop", name="VLC", exec_line="/usr/bin/vlc %U", categories="AudioVideo;Player;"
    )
    write_desktop_file(
        tmp_path, "discord.desktop", name="Discord", exec_line="discord", categories="Network;InstantMessaging;"
    )
    monkeypatch.setattr(installed_apps, "DESKTOP_DIRS", [tmp_path])

    result = installed_apps.list_installed_apps()

    assert result["gaming"] == [("supertux2", "SuperTux")]
    assert result["entertainment"] == [("vlc", "VLC")]
    assert result["social"] == [("discord", "Discord")]


def test_excludes_apps_with_no_matching_category(tmp_path, monkeypatch):
    write_desktop_file(tmp_path, "firefox.desktop", name="Firefox", exec_line="firefox %u", categories="Network;")
    write_desktop_file(
        tmp_path, "libreoffice.desktop", name="LibreOffice Writer", exec_line="soffice --writer", categories="Office;"
    )
    monkeypatch.setattr(installed_apps, "DESKTOP_DIRS", [tmp_path])

    result = installed_apps.list_installed_apps()

    all_names = {name for apps in result.values() for _, name in apps}
    assert "Firefox" not in all_names
    assert "LibreOffice Writer" not in all_names


def test_excludes_hidden_and_non_application_entries(tmp_path, monkeypatch):
    write_desktop_file(
        tmp_path, "hidden-game.desktop", name="Hidden Game", exec_line="hiddengame", categories="Game;", no_display=True
    )
    write_desktop_file(
        tmp_path, "game-dir.desktop", name="Game Directory", exec_line="somegame", categories="Game;", type_="Directory"
    )
    monkeypatch.setattr(installed_apps, "DESKTOP_DIRS", [tmp_path])

    result = installed_apps.list_installed_apps()

    all_names = {name for apps in result.values() for _, name in apps}
    assert "Hidden Game" not in all_names
    assert "Game Directory" not in all_names


def test_excludes_system_settings_categories(tmp_path, monkeypatch):
    write_desktop_file(
        tmp_path,
        "bluetooth.desktop",
        name="Bluetooth Manager",
        exec_line="blueman-manager",
        categories="Settings;HardwareSettings;",
    )
    monkeypatch.setattr(installed_apps, "DESKTOP_DIRS", [tmp_path])

    result = installed_apps.list_installed_apps()

    all_names = {name for apps in result.values() for _, name in apps}
    assert "Bluetooth Manager" not in all_names


def test_deduplicates_same_process_name_across_directories(tmp_path, monkeypatch):
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    write_desktop_file(dir_a, "game.desktop", name="SuperTux", exec_line="supertux2", categories="Game;")
    write_desktop_file(dir_b, "game-dup.desktop", name="SuperTux (copie)", exec_line="supertux2", categories="Game;")
    monkeypatch.setattr(installed_apps, "DESKTOP_DIRS", [dir_a, dir_b])

    result = installed_apps.list_installed_apps()

    assert len(result["gaming"]) == 1


def test_returns_empty_lists_when_no_desktop_dir_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(installed_apps, "DESKTOP_DIRS", [tmp_path / "does-not-exist"])

    result = installed_apps.list_installed_apps()

    assert result == {"gaming": [], "entertainment": [], "social": []}


def test_process_name_extraction_strips_path_and_arguments():
    assert installed_apps._process_name_from_exec("/opt/discord/Discord --no-sandbox %U") == "discord"
    assert installed_apps._process_name_from_exec("steam %U") == "steam"
    assert installed_apps._process_name_from_exec("") == ""
