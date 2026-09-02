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

"""start_daemon_via_polkit() : remplace la commande de terminal `sudo systemctl start
mintguard-daemon` par un clic dans la GUI (voir SUIVI.md, point 2 de la revue UX)."""

import subprocess

from mintguard.gui import daemon_control


def test_is_daemon_active_reflects_query_status(monkeypatch):
    monkeypatch.setattr("mintguard.child_tray.query_status", lambda: {"is_child": False})
    assert daemon_control.is_daemon_active() is True


def test_is_daemon_active_false_when_unreachable(monkeypatch):
    monkeypatch.setattr("mintguard.child_tray.query_status", lambda: None)
    assert daemon_control.is_daemon_active() is False


def test_start_daemon_success(monkeypatch):
    monkeypatch.setattr(
        daemon_control.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, returncode=0),
    )
    assert daemon_control.start_daemon_via_polkit() is True


def test_start_daemon_cancelled_or_denied(monkeypatch):
    monkeypatch.setattr(
        daemon_control.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, returncode=1),
    )
    assert daemon_control.start_daemon_via_polkit() is False


def test_start_daemon_pkexec_missing(monkeypatch):
    def raise_not_found(*a, **k):
        raise FileNotFoundError()

    monkeypatch.setattr(daemon_control.subprocess, "run", raise_not_found)
    assert daemon_control.start_daemon_via_polkit() is None


def test_start_daemon_timeout_is_treated_as_failure(monkeypatch):
    def raise_timeout(*a, **k):
        raise subprocess.TimeoutExpired(cmd="pkexec", timeout=120)

    monkeypatch.setattr(daemon_control.subprocess, "run", raise_timeout)
    assert daemon_control.start_daemon_via_polkit() is False
