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

import subprocess

import pytest

from mintguard.backend.firewall_controller import FirewallController
from mintguard.db.database import get_session, init_db
from mintguard.db.models import Child


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


class FakeIptables:
    """Simule `iptables` sans toucher au vrai système (nécessite root en réalité).

    `chain_exists`/`jump_exists` contrôlent la réponse aux commandes de vérification
    (-nL / -C), `fail_on` déclenche un CalledProcessError pour les commandes `check=True`
    dont les arguments contiennent tous les tokens de `fail_on`.
    """

    def __init__(self, chain_exists=False, jump_exists=False, fail_on=None):
        self.chain_exists = chain_exists
        self.jump_exists = jump_exists
        self.fail_on = fail_on or []
        self.calls: list[list[str]] = []

    def __call__(self, cmd, *args, **kwargs):
        args_list = cmd[1:]  # sans "iptables"
        self.calls.append(args_list)

        if self.fail_on and all(token in args_list for token in self.fail_on):
            if kwargs.get("check"):
                raise subprocess.CalledProcessError(1, cmd)
            return subprocess.CompletedProcess(cmd, 1)

        if "-nL" in args_list:
            return subprocess.CompletedProcess(cmd, 0 if self.chain_exists else 1)
        if "-C" in args_list:
            return subprocess.CompletedProcess(cmd, 0 if self.jump_exists else 1)
        return subprocess.CompletedProcess(cmd, 0)


def test_sync_creates_chain_and_jump_when_missing(monkeypatch):
    fake = FakeIptables(chain_exists=False, jump_exists=False)
    monkeypatch.setattr("mintguard.backend.firewall_controller.subprocess.run", fake)

    assert FirewallController().sync_child_dns_restriction() is True
    assert ["-N", "MINTGUARD"] in fake.calls
    assert ["-I", "OUTPUT", "-j", "MINTGUARD"] in fake.calls
    assert ["-F", "MINTGUARD"] in fake.calls


def test_sync_skips_creation_when_chain_and_jump_already_present(monkeypatch):
    fake = FakeIptables(chain_exists=True, jump_exists=True)
    monkeypatch.setattr("mintguard.backend.firewall_controller.subprocess.run", fake)

    assert FirewallController().sync_child_dns_restriction() is True
    assert ["-N", "MINTGUARD"] not in fake.calls
    assert ["-I", "OUTPUT", "-j", "MINTGUARD"] not in fake.calls


def test_sync_adds_udp_and_tcp_reject_rules_per_child(monkeypatch):
    fake = FakeIptables(chain_exists=True, jump_exists=True)
    monkeypatch.setattr("mintguard.backend.firewall_controller.subprocess.run", fake)

    session = get_session()
    session.add(Child(name="Test", username="mintguard-test-child"))
    session.commit()
    session.close()

    assert FirewallController().sync_child_dns_restriction() is True
    rule_calls = [c for c in fake.calls if c[:2] == ["-A", "MINTGUARD"]]
    assert len(rule_calls) == 2  # udp + tcp
    protos = {c[c.index("-p") + 1] for c in rule_calls}
    assert protos == {"udp", "tcp"}
    for c in rule_calls:
        assert "--uid-owner" in c
        assert c[c.index("--uid-owner") + 1] == "mintguard-test-child"
        assert "--dport" in c and c[c.index("--dport") + 1] == "53"
        assert "!" in c and "-d" in c and "127.0.0.1" in c
        assert c[-2:] == ["-j", "REJECT"]


def test_sync_returns_false_on_iptables_failure(monkeypatch):
    fake = FakeIptables(chain_exists=False, jump_exists=False, fail_on=["-N", "MINTGUARD"])
    monkeypatch.setattr("mintguard.backend.firewall_controller.subprocess.run", fake)

    assert FirewallController().sync_child_dns_restriction() is False


def test_remove_flushes_and_deletes_chain(monkeypatch):
    fake = FakeIptables(chain_exists=True, jump_exists=True)
    monkeypatch.setattr("mintguard.backend.firewall_controller.subprocess.run", fake)

    assert FirewallController().remove() is True
    assert ["-D", "OUTPUT", "-j", "MINTGUARD"] in fake.calls
    assert ["-F", "MINTGUARD"] in fake.calls
    assert ["-X", "MINTGUARD"] in fake.calls
