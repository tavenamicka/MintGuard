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

import logging
import pwd
import re
import subprocess

from mintguard.db.database import get_session
from mintguard.db.models import Child
from mintguard.utils.validators import is_valid_username

logger = logging.getLogger("mintguard.backend.firewall")

# `iptables -S` affiche toujours l'UID numérique, même si la règle a été posée par nom.
_UID_OWNER_RE = re.compile(r"--uid-owner (\d+)")


class FirewallController:
    """Défense en profondeur : force chaque compte enfant à utiliser uniquement le
    résolveur DNS local (dnsmasq), pour empêcher un contournement du blocage DNS en
    configurant un résolveur externe (ex: 8.8.8.8) directement dans le système ou le
    navigateur. Le blocage DNS lui-même (DNSController) reste la protection primaire.

    Règles posées dans une chaîne dédiée ("MINTGUARD") plutôt que directement dans
    OUTPUT, pour ne jamais toucher aux règles iptables préexistantes de l'utilisateur
    et pouvoir tout retirer proprement (`remove()`).

    Règles posées en IPv4 *et* en IPv6 : Linux Mint active IPv6 par défaut et une seule
    ligne `nameserver 2001:4860:4860::8888` dans la configuration réseau suffisait à
    contourner l'intégralité du blocage tant que seul iptables (IPv4) était filtré.
    """

    CHAIN = "MINTGUARD"
    # Résolveur local, par famille d'adresses : dnsmasq écoute sur 127.0.0.1, donc une
    # requête DNS IPv6 n'a aucune destination légitime — mais ::1 est autorisé pour ne
    # pas casser un futur `listen-address=::1`.
    COMMANDS = {"iptables": "127.0.0.1", "ip6tables": "::1"}

    def _run(self, command: str, args: list[str]) -> bool:
        try:
            subprocess.run([command] + args, check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error("Commande %s échouée (%s): %s", command, args, e)
            return False

    def _chain_exists(self, command: str) -> bool:
        result = subprocess.run([command, "-nL", self.CHAIN], capture_output=True)
        return result.returncode == 0

    def _jump_exists(self, command: str) -> bool:
        result = subprocess.run([command, "-C", "OUTPUT", "-j", self.CHAIN], capture_output=True)
        return result.returncode == 0

    def _ensure_chain(self, command: str) -> bool:
        if not self._chain_exists(command) and not self._run(command, ["-N", self.CHAIN]):
            return False
        if not self._jump_exists(command) and not self._run(command, ["-I", "OUTPUT", "-j", self.CHAIN]):
            return False
        return True

    def _child_accounts(self) -> list[tuple[str, int]]:
        """(nom, UID) de chaque enfant dont le compte Linux existe réellement.

        Un enfant dont le compte a été supprimé du système (mais pas de MintGuard) est ignoré
        ici : `iptables --uid-owner` refuse un nom inconnu, et cet échec interrompait
        auparavant la reconstruction de la chaîne - laissant les enfants suivants sans
        aucun filtrage DNS.
        """
        session = get_session()
        try:
            usernames = [c.username for c in session.query(Child).all()]
        finally:
            session.close()

        accounts = []
        for username in usernames:
            if not is_valid_username(username):
                logger.warning("Nom d'utilisateur invalide ignoré (règles firewall): %r", username)
                continue
            try:
                accounts.append((username, pwd.getpwnam(username).pw_uid))
            except KeyError:
                logger.warning("Compte Linux introuvable, ignoré (règles firewall): %r", username)
        return accounts

    def _rules_for(self, username: str, local_resolver: str) -> list[list[str]]:
        return [
            [
                "-A", self.CHAIN,
                "-m", "owner", "--uid-owner", username,
                "-p", proto, "--dport", "53",
                "!", "-d", local_resolver,
                "-j", "REJECT",
            ]
            for proto in ("udp", "tcp")
        ]

    def _current_uids(self, command: str) -> list[int] | None:
        """UID ciblé par chaque règle actuellement dans la chaîne (trié), ou None si illisible."""
        result = subprocess.run([command, "-S", self.CHAIN], capture_output=True, text=True)
        if result.returncode != 0:
            return None
        return sorted(
            int(match.group(1))
            for line in (result.stdout or "").splitlines()
            if line.startswith("-A ") and (match := _UID_OWNER_RE.search(line))
        )

    def sync_child_dns_restriction(self) -> bool:
        """Régénère les règles depuis la BD (liste actuelle des enfants), en IPv4 et IPv6.

        Idempotent : peut être rappelée à chaque cycle du daemon. La chaîne n'est vidée et
        reconstruite que si les comptes ciblés ne correspondent plus à l'existant (comparaison
        par UID et non plus par simple nombre de règles : supprimer un enfant puis en ajouter
        un autre laissait la chaîne inchangée, le nouvel enfant n'étant jamais filtré) —
        un `-F` systématique toutes les 30 s rouvrait à chaque fois une fenêtre (courte mais
        récurrente) pendant laquelle l'enfant n'était plus filtré du tout.
        """
        ok = True
        for command, local_resolver in self.COMMANDS.items():
            if not self._sync_one(command, local_resolver):
                ok = False
        return ok

    def _sync_one(self, command: str, local_resolver: str) -> bool:
        if not self._ensure_chain(command):
            return False

        accounts = self._child_accounts()
        expected_uids = sorted(uid for _username, uid in accounts for _proto in ("udp", "tcp"))
        if self._current_uids(command) == expected_uids:
            return True

        if not self._run(command, ["-F", self.CHAIN]):
            return False
        ok = True
        for username, _uid in accounts:
            for rule in self._rules_for(username, local_resolver):
                # Un échec isolé ne doit pas priver les enfants suivants de leur filtrage.
                if not self._run(command, rule):
                    ok = False
        return ok

    def remove(self) -> bool:
        """Retire toutes les règles MintGuard (désinstallation), IPv4 et IPv6. Idempotent :
        ne pas échouer si la chaîne/le jump n'existent déjà plus.
        """
        ok = True
        for command in self.COMMANDS:
            self._run(command, ["-D", "OUTPUT", "-j", self.CHAIN])
            self._run(command, ["-F", self.CHAIN])
            if not self._run(command, ["-X", self.CHAIN]):
                ok = False
        return ok

    def test(self) -> bool:
        """Vérifie que iptables est accessible en lecture (--list), sans modifier l'état."""
        try:
            subprocess.run(["iptables", "-L", "-n"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("iptables indisponible (normal hors Linux/root): %s", e)
            return False
