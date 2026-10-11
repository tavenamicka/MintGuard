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
from types import SimpleNamespace

import pytest

from mintguard.backend.firewall_controller import FirewallController
from mintguard.db.database import get_session, init_db
from mintguard.db.models import Child


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


TEST_UID = 1001


@pytest.fixture(autouse=True)
def fake_accounts(monkeypatch):
    """Les comptes enfants des tests n'existent pas sur la machine : tout nom se résout en
    TEST_UID, sauf ceux listés dans `missing` (compte supprimé du système)."""
    missing: set[str] = set()

    def getpwnam(name):
        if name in missing:
            raise KeyError(name)
        return SimpleNamespace(pw_uid=TEST_UID)

    monkeypatch.setattr("mintguard.backend.firewall_controller.pwd.getpwnam", getpwnam)
    return missing


class FakeIptables:
    """Simule `iptables`/`ip6tables` sans toucher au vrai système (nécessite root en réalité).

    `chain_exists`/`jump_exists` contrôlent la réponse aux commandes de vérification
    (-nL / -C), `fail_on` déclenche un CalledProcessError pour les commandes `check=True`
    dont les arguments contiennent tous les tokens de `fail_on`. `existing_rules` est le
    nombre de règles que `-S` (état actuel de la chaîne) doit rapporter, toutes pour TEST_UID.
    """

    def __init__(self, chain_exists=False, jump_exists=False, fail_on=None, existing_rules=0):
        self.chain_exists = chain_exists
        self.jump_exists = jump_exists
        self.fail_on = fail_on or []
        self.existing_rules = existing_rules
        self.calls: list[list[str]] = []          # arguments seuls (toutes familles confondues)
        self.calls_by_command: list[tuple[str, list[str]]] = []

    def __call__(self, cmd, *args, **kwargs):
        command, args_list = cmd[0], cmd[1:]
        self.calls.append(args_list)
        self.calls_by_command.append((command, args_list))

        if self.fail_on and all(token in args_list for token in self.fail_on):
            if kwargs.get("check"):
                raise subprocess.CalledProcessError(1, cmd)
            return subprocess.CompletedProcess(cmd, 1)

        if "-nL" in args_list:
            return subprocess.CompletedProcess(cmd, 0 if self.chain_exists else 1)
        if "-C" in args_list:
            return subprocess.CompletedProcess(cmd, 0 if self.jump_exists else 1)
        if "-S" in args_list:
            rule = f"-A MINTGUARD -m owner --uid-owner {TEST_UID} -j REJECT\n"
            listing = "-N MINTGUARD\n" + rule * self.existing_rules
            return subprocess.CompletedProcess(cmd, 0, stdout=listing)
        return subprocess.CompletedProcess(cmd, 0)

    def args_for(self, command: str) -> list[list[str]]:
        return [args for name, args in self.calls_by_command if name == command]


def test_sync_creates_chain_and_jump_when_missing(monkeypatch):
    fake = FakeIptables(chain_exists=False, jump_exists=False, existing_rules=1)
    monkeypatch.setattr("mintguard.backend.firewall_controller.subprocess.run", fake)

    assert FirewallController().sync_child_dns_restriction() is True
    assert ["-N", "MINTGUARD"] in fake.calls
    assert ["-I", "OUTPUT", "-j", "MINTGUARD"] in fake.calls
    assert ["-F", "MINTGUARD"] in fake.calls


def test_sync_creates_chain_in_both_address_families(monkeypatch):
    """IPv6 aussi : un simple `nameserver 2001:4860:4860::8888` suffisait sinon à
    contourner tout le blocage DNS (Linux Mint active IPv6 par défaut)."""
    fake = FakeIptables(chain_exists=False, jump_exists=False, existing_rules=1)
    monkeypatch.setattr("mintguard.backend.firewall_controller.subprocess.run", fake)

    assert FirewallController().sync_child_dns_restriction() is True
    assert ["-N", "MINTGUARD"] in fake.args_for("iptables")
    assert ["-N", "MINTGUARD"] in fake.args_for("ip6tables")


def test_sync_skips_creation_when_chain_and_jump_already_present(monkeypatch):
    fake = FakeIptables(chain_exists=True, jump_exists=True, existing_rules=1)
    monkeypatch.setattr("mintguard.backend.firewall_controller.subprocess.run", fake)

    assert FirewallController().sync_child_dns_restriction() is True
    assert ["-N", "MINTGUARD"] not in fake.calls
    assert ["-I", "OUTPUT", "-j", "MINTGUARD"] not in fake.calls


def test_sync_leaves_chain_untouched_when_already_up_to_date(monkeypatch):
    """Sans cette comparaison, le daemon vidait la chaîne (`-F`) toutes les 30 s, rouvrant
    à chaque fois une fenêtre pendant laquelle l'enfant n'était plus filtré."""
    session = get_session()
    session.add(Child(name="Test", username="mintguard-test-child"))
    session.commit()
    session.close()

    fake = FakeIptables(chain_exists=True, jump_exists=True, existing_rules=2)  # udp + tcp
    monkeypatch.setattr("mintguard.backend.firewall_controller.subprocess.run", fake)

    assert FirewallController().sync_child_dns_restriction() is True
    assert ["-F", "MINTGUARD"] not in fake.calls
    assert not [c for c in fake.calls if c[:2] == ["-A", "MINTGUARD"]]


def test_sync_adds_udp_and_tcp_reject_rules_per_child(monkeypatch):
    fake = FakeIptables(chain_exists=True, jump_exists=True, existing_rules=0)
    monkeypatch.setattr("mintguard.backend.firewall_controller.subprocess.run", fake)

    session = get_session()
    session.add(Child(name="Test", username="mintguard-test-child"))
    session.commit()
    session.close()

    assert FirewallController().sync_child_dns_restriction() is True
    rule_calls = [c for c in fake.args_for("iptables") if c[:2] == ["-A", "MINTGUARD"]]
    assert len(rule_calls) == 2  # udp + tcp
    protos = {c[c.index("-p") + 1] for c in rule_calls}
    assert protos == {"udp", "tcp"}
    for c in rule_calls:
        assert "--uid-owner" in c
        assert c[c.index("--uid-owner") + 1] == "mintguard-test-child"
        assert "--dport" in c and c[c.index("--dport") + 1] == "53"
        assert "!" in c and "-d" in c and "127.0.0.1" in c
        assert c[-2:] == ["-j", "REJECT"]

    v6_rules = [c for c in fake.args_for("ip6tables") if c[:2] == ["-A", "MINTGUARD"]]
    assert len(v6_rules) == 2
    assert all("::1" in c for c in v6_rules)


def test_sync_skips_child_with_implausible_username(monkeypatch):
    """Ces noms partent tels quels dans `iptables --uid-owner` : un nom commençant par
    « - » y serait lu comme une option."""
    session = get_session()
    session.add(Child(name="Bidon", username="--jump=ACCEPT"))
    session.commit()
    session.close()

    fake = FakeIptables(chain_exists=True, jump_exists=True, existing_rules=1)
    monkeypatch.setattr("mintguard.backend.firewall_controller.subprocess.run", fake)

    assert FirewallController().sync_child_dns_restriction() is True
    assert not [c for c in fake.calls if "--jump=ACCEPT" in c]


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


def _add_child(username):
    session = get_session()
    session.add(Child(name=username, username=username))
    session.commit()
    session.close()


def test_sync_rebuilds_when_same_count_but_different_child(monkeypatch):
    """Supprimer un enfant puis en ajouter un autre garde le même nombre de règles : la
    chaîne doit quand même être reconstruite pour le nouveau compte."""
    _add_child("nouvel-enfant")
    fake = FakeIptables(chain_exists=True, jump_exists=True, existing_rules=2)
    monkeypatch.setattr(
        "mintguard.backend.firewall_controller.pwd.getpwnam", lambda name: SimpleNamespace(pw_uid=TEST_UID + 1)
    )
    monkeypatch.setattr("mintguard.backend.firewall_controller.subprocess.run", fake)

    assert FirewallController().sync_child_dns_restriction() is True
    assert ["-F", "MINTGUARD"] in fake.calls
    assert [c for c in fake.args_for("iptables") if c[:2] == ["-A", "MINTGUARD"]]


def test_sync_skips_deleted_linux_account_but_filters_the_others(monkeypatch, fake_accounts):
    _add_child("compte-supprime")
    _add_child("emma")
    fake_accounts.add("compte-supprime")
    fake = FakeIptables(chain_exists=True, jump_exists=True, existing_rules=0)
    monkeypatch.setattr("mintguard.backend.firewall_controller.subprocess.run", fake)

    assert FirewallController().sync_child_dns_restriction() is True
    owners = {c[c.index("--uid-owner") + 1] for c in fake.args_for("iptables") if c[:2] == ["-A", "MINTGUARD"]}
    assert owners == {"emma"}


def test_sync_keeps_filtering_other_children_when_one_rule_fails(monkeypatch):
    _add_child("alice")
    _add_child("bob")
    fake = FakeIptables(chain_exists=True, jump_exists=True, existing_rules=0, fail_on=["-A", "alice"])
    monkeypatch.setattr("mintguard.backend.firewall_controller.subprocess.run", fake)

    assert FirewallController().sync_child_dns_restriction() is False
    assert [c for c in fake.args_for("iptables") if c[:2] == ["-A", "MINTGUARD"] and "bob" in c]
