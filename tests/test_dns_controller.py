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

"""Blocklist DNS : format, robustesse d'écriture et déclenchement du redémarrage dnsmasq."""

import pytest

from mintguard.backend.dns_controller import DNSController
from mintguard.db.database import get_session, init_db
from mintguard.db.models import BlockedSite


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


@pytest.fixture
def controller(tmp_path):
    return DNSController(blocklist_path=tmp_path / "blocklist.conf")


def add_sites(*domains, blocked=True):
    session = get_session()
    for domain in domains:
        session.add(BlockedSite(domain=domain, category="custom", blocked=blocked))
    session.commit()
    session.close()


def test_blocklist_uses_wildcard_format_covering_subdomains(controller):
    """Le cœur du produit : un fichier hosts (`0.0.0.0 youtube.com`) ne matche que le nom
    exact et laissait « www.youtube.com » — le site lui-même — parfaitement accessible."""
    add_sites("youtube.com")
    assert controller.generate_blocklist() == 1

    content = controller.blocklist_path.read_text(encoding="utf-8")
    assert "address=/youtube.com/0.0.0.0" in content
    assert "0.0.0.0 youtube.com" not in content


def test_blocklist_ignores_unblocked_sites(controller):
    add_sites("youtube.com")
    add_sites("wikipedia.org", blocked=False)

    assert controller.generate_blocklist() == 1
    assert "wikipedia.org" not in controller.blocklist_path.read_text(encoding="utf-8")


def test_blocklist_skips_invalid_domains(controller):
    """Défense en profondeur : cette blocklist est injectée dans la configuration d'un
    dnsmasq qui tourne en root, une ligne arbitraire n'a rien à y faire."""
    add_sites("youtube.com", "mauvais domaine\nlog-facility=/etc/passwd")

    assert controller.generate_blocklist() == 1
    content = controller.blocklist_path.read_text(encoding="utf-8")
    assert "log-facility=/etc/passwd" not in content
    assert "address=/youtube.com/0.0.0.0" in content


def test_apply_restarts_dnsmasq_only_when_content_changed(controller, monkeypatch):
    """Sans cette comparaison, le daemon redémarrait dnsmasq toutes les 30 s pour rien
    (cache DNS vidé à chaque fois)."""
    restarts = []
    monkeypatch.setattr(controller, "restart_dnsmasq", lambda: restarts.append(1) or True)

    add_sites("youtube.com")
    assert controller.apply() is True          # 1er passage : le fichier n'existait pas
    assert controller.apply() is False         # rien n'a changé
    assert len(restarts) == 1

    add_sites("tiktok.com")
    assert controller.apply() is True
    assert len(restarts) == 2


def test_blocklist_write_is_atomic(controller, monkeypatch):
    """dnsmasq peut lire le fichier pendant sa réécriture : une écriture directe l'exposait
    à une blocklist tronquée, donc à des sites débloqués."""
    add_sites("youtube.com")
    controller.generate_blocklist()
    original = controller.blocklist_path.read_text(encoding="utf-8")

    add_sites("tiktok.com")
    monkeypatch.setattr(
        "mintguard.backend.dns_controller.os.replace",
        lambda *a, **k: (_ for _ in ()).throw(OSError("disque plein")),
    )
    with pytest.raises(OSError):
        controller.generate_blocklist()

    # L'ancienne blocklist est intacte, et aucun fichier temporaire n'est laissé derrière.
    assert controller.blocklist_path.read_text(encoding="utf-8") == original
    assert not list(controller.blocklist_path.parent.glob(".blocklist-*"))
