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

"""Applications suggérées dans Settings > Applications, cf. PROJECT_BRIEF.md 'Écran 3'.
(process_name, libellé affiché) — process_name doit correspondre au nom de processus réel
sous Linux (comparé en minuscules par ProcessMonitor). Noms de marque non traduits (i18n)."""

PREDEFINED_APPS = [
    ("firefox", "Firefox"),
    ("chrome", "Google Chrome"),
    ("discord", "Discord"),
    ("steam", "Steam"),
]
