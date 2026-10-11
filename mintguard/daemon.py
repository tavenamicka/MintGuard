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

import time

from mintguard.backend.dns_controller import DNSController
from mintguard.backend.dns_health import system_resolver_uses_mintguard
from mintguard.backend.firewall_controller import FirewallController
from mintguard.backend.process_monitor import ProcessMonitor
from mintguard.backend.scheduler import Scheduler
from mintguard.backend.site_usage_tracker import SiteUsageTracker, logged_in_child_ids, resolve_active_child_id
from mintguard.backend.status_server import StatusServer
from mintguard.backend.usage_tracker import UsageTracker
from mintguard.config import get_config
from mintguard.db.database import init_db
from mintguard.logger import setup_logging

logger = setup_logging("mintguard-daemon")


def run_cycle(
    process_monitor: ProcessMonitor,
    scheduler: Scheduler,
    dns_controller: DNSController,
    firewall_controller: FirewallController,
    usage_tracker: UsageTracker,
    site_usage_tracker: SiteUsageTracker,
    state: dict,
    now: float,
    session_interval: float,
    dns_refresh_interval: float,
    process_interval: float,
) -> None:
    """Un tour de boucle du daemon. Isolé de `main()` pour être testable sans horloge réelle.

    Pas de bus D-Bus/IPC pour propager les changements Réglages -> daemon (choix
    d'architecture assumé) : le daemon relit périodiquement la BD partagée, comme ProcessMonitor et
    Scheduler le font déjà à chaque cycle. `dns_refresh_interval` évite de relancer
    `systemctl reload dnsmasq` à chaque cycle process (par défaut 5s) alors que rien n'a changé.
    Les règles firewall (défense en profondeur, voir FirewallController) sont resynchronisées
    au même rythme que la blocklist DNS : même but (empêcher un contournement du blocage DNS),
    et la liste des enfants change rarement.
    """
    # Chaque étape est isolée (`_step`) : une étape qui échoue à chaque cycle (BD verrouillée,
    # commande système en erreur...) ne doit jamais empêcher les suivantes de tourner - en
    # particulier le Scheduler, sans quoi plus aucune session ne serait coupée.

    # `elapsed_seconds` sert aussi à ProcessMonitor pour accumuler le temps des applications à
    # quota (AppDailyUsage), même principe que DailyUsage ci-dessous.
    _step("contrôle des processus", process_monitor.check_and_kill, process_interval)

    # Comptes connectés calculés une seule fois par cycle (psutil + un appel `loginctl`), puis
    # partagés entre le cumul du temps d'écran et la résolution de l'enfant actif - chacun
    # relançait auparavant sa propre requête loginctl, soit deux sous-processus toutes les 5 s.
    active_usernames = _step("comptes connectés", usage_tracker.get_active_usernames)
    child_ids: list[int] | None = None
    if active_usernames is not None:
        # Même cadence que check_and_kill() (un tick = process_interval secondes) : c'est cette
        # écriture périodique dans DailyUsage, relue par le Dashboard, qui tient lieu d'"IPC
        # temps réel" GUI<->daemon pour la barre de progression.
        _step("temps d'écran", usage_tracker.record_tick, process_interval, active_usernames)
        child_ids = _step("enfants connectés", logged_in_child_ids, active_usernames)

    # Comptes connectés inconnus (étape en échec) : traité comme ambigu, donc restrictif.
    if child_ids is None:
        active_child_id, parent_only = None, False
    else:
        # Réutilisé à la fois par le suivi de temps par site (chaque cycle) et par la
        # régénération DNS ci-dessous (seulement quand dns_refresh_interval le déclenche).
        active_child_id = resolve_active_child_id(active_usernames, child_ids)
        # Des comptes sont connectés mais aucun n'est un enfant (le parent seul) : seules les
        # règles globales s'appliquent. Personne de connecté (écran de connexion) reste traité
        # comme ambigu, donc restrictif - le prochain à se connecter peut être un enfant.
        parent_only = bool(active_usernames) and not child_ids
    _step("temps par site", site_usage_tracker.poll, process_interval, active_child_id)

    if now - state["last_session_check"] >= session_interval:
        _step("plages horaires", scheduler.check_all_children)
        state["last_session_check"] = now

    # Changement de compte connecté (parent -> enfant, enfant A -> enfant B) : la blocklist
    # dépend de qui est connecté, elle est régénérée tout de suite plutôt qu'au prochain
    # rafraîchissement périodique (jusqu'à 30 s pendant lesquelles un enfant qui vient de se
    # connecter aurait profité des règles du parent).
    users_changed = active_usernames != state.get("active_usernames")
    state["active_usernames"] = active_usernames
    if users_changed or now - state["last_dns_refresh"] >= dns_refresh_interval:
        # `apply()` ne redémarre dnsmasq que si la blocklist a réellement changé, et
        # `sync_child_dns_restriction()` ne reconstruit la chaîne iptables que si elle ne
        # correspond plus à la BD : un cycle sans changement (le cas courant) ne touche
        # plus au système du tout.
        _step("blocklist DNS", dns_controller.apply, active_child_id, parent_only)
        _step("pare-feu", firewall_controller.sync_child_dns_restriction)
        _step("vérification du résolveur", _log_resolver_change, state)
        state["last_dns_refresh"] = now


def _step(name: str, func, *args):
    """Exécute une étape du cycle ; en cas d'erreur, la journalise et renvoie None."""
    try:
        return func(*args)
    except Exception:
        logger.exception("Étape « %s » en échec, les autres étapes du cycle continuent", name)
        return None


def _log_resolver_change(state: dict) -> None:
    """Journalise (une fois par changement, pas à chaque cycle) quand le système cesse ou
    recommence d'interroger dnsmasq - sans ce signal, un blocage inopérant passait inaperçu."""
    resolver_ok = system_resolver_uses_mintguard()
    if resolver_ok is None or resolver_ok == state.get("resolver_ok"):
        return
    if resolver_ok:
        logger.info("/etc/resolv.conf désigne dnsmasq : blocage des sites actif")
    else:
        logger.warning(
            "/etc/resolv.conf ne désigne pas dnsmasq (127.0.0.1) : AUCUN site n'est bloqué. "
            "Réparer depuis le Tableau de bord, ou /usr/lib/mintguard/switch-dns.sh"
        )
    state["resolver_ok"] = resolver_ok


def main() -> None:
    logger.info("MintGuard Daemon démarré")
    init_db()

    config = get_config()
    process_interval = config.get("monitoring.process_check_interval", 5)
    session_interval = config.get("monitoring.session_check_interval", 60)
    dns_refresh_interval = config.get("dns.refresh_interval", 30)

    process_monitor = ProcessMonitor()
    scheduler = Scheduler()
    dns_controller = DNSController()
    firewall_controller = FirewallController()
    usage_tracker = UsageTracker()
    site_usage_tracker = SiteUsageTracker()

    # Écrit la blocklist ET redémarre dnsmasq inconditionnellement (pas `apply()`, qui ne
    # redémarre que si le contenu diffère de celui déjà sur disque) : constaté en usage réel
    # qu'un dnsmasq déjà démarré (avant ce cycle, ex: resté actif d'un
    # précédent lancement du daemon) tournait avec une configuration chargée en mémoire
    # potentiellement plus ancienne que ce qui vient d'être (ré)écrit sur disque - le premier
    # `apply()` du cycle ne voyait ensuite aucun changement (le fichier venait d'être écrit
    # avec exactement ce contenu) et ne redémarrait donc jamais dnsmasq, qui restait bloqué
    # sur son ancienne configuration indéfiniment.
    dns_controller.generate_blocklist()
    dns_controller.restart_dnsmasq()
    firewall_controller.sync_child_dns_restriction()
    StatusServer(scheduler).start()
    state = {"last_session_check": 0.0, "last_dns_refresh": time.monotonic()}

    try:
        while True:
            # Une erreur ponctuelle (BD verrouillée plus longtemps que le timeout SQLite, commande
            # système qui échoue de façon inattendue...) ne doit pas tuer le daemon : systemd le
            # relancerait, mais en perdant les périodes de grâce en cours (gardées en mémoire,
            # voir Scheduler) - des erreurs répétées repousseraient alors indéfiniment la
            # coupure de session. On journalise et on retente au cycle suivant.
            try:
                run_cycle(
                    process_monitor,
                    scheduler,
                    dns_controller,
                    firewall_controller,
                    usage_tracker,
                    site_usage_tracker,
                    state,
                    time.monotonic(),
                    session_interval,
                    dns_refresh_interval,
                    process_interval,
                )
            except Exception:
                logger.exception("Erreur pendant un cycle du daemon, nouvel essai au cycle suivant")
            time.sleep(process_interval)
    except KeyboardInterrupt:
        logger.info("MintGuard Daemon arrêté")


if __name__ == "__main__":
    main()
