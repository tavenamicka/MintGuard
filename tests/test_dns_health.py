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

"""dns_health : détecte un /etc/resolv.conf qui ne passe pas par dnsmasq - cas réel où le
blocage des sites était inopérant sans aucun signal."""

from mintguard.backend.dns_health import system_resolver_uses_mintguard


def write(tmp_path, content):
    path = tmp_path / "resolv.conf"
    path.write_text(content)
    return path


def test_only_dnsmasq_is_ok(tmp_path):
    assert system_resolver_uses_mintguard(write(tmp_path, "# commentaire\nnameserver 127.0.0.1\n")) is True


def test_external_resolver_is_not_ok(tmp_path):
    assert system_resolver_uses_mintguard(write(tmp_path, "nameserver 8.8.8.8\nnameserver 1.1.1.1\n")) is False


def test_systemd_resolved_stub_is_not_ok(tmp_path):
    assert system_resolver_uses_mintguard(write(tmp_path, "nameserver 127.0.0.53\noptions edns0\n")) is False


def test_dnsmasq_plus_fallback_is_not_ok(tmp_path):
    """Un second serveur suffit à contourner : la libc bascule dessus dès que dnsmasq
    répond NXDOMAIN... ou tarde un peu."""
    assert system_resolver_uses_mintguard(write(tmp_path, "nameserver 127.0.0.1\nnameserver 8.8.8.8\n")) is False


def test_no_nameserver_is_not_ok(tmp_path):
    assert system_resolver_uses_mintguard(write(tmp_path, "search home\n")) is False


def test_unreadable_file_is_unknown(tmp_path):
    assert system_resolver_uses_mintguard(tmp_path / "absent") is None
