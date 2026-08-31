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
from mintguard.backend.process_monitor import ProcessMonitor
from mintguard.backend.scheduler import Scheduler
from mintguard.config import get_config
from mintguard.db.database import init_db
from mintguard.logger import setup_logging

logger = setup_logging("mintguard-daemon")


def run_cycle(
    process_monitor: ProcessMonitor,
    scheduler: Scheduler,
    dns_controller: DNSController,
    state: dict,
    now: float,
    session_interval: float,
    dns_refresh_interval: float,
) -> None:
    """Un tour de boucle du daemon. Isolé de `main()` pour être testable sans horloge réelle.

    Pas de bus D-Bus/IPC pour propager les changements Réglages -> daemon (voir SUIVI.md pour la
    justification) : le daemon relit périodiquement la BD partagée, comme ProcessMonitor et
    Scheduler le font déjà à chaque cycle. `dns_refresh_interval` évite de relancer
    `systemctl reload dnsmasq` à chaque cycle process (par défaut 5s) alors que rien n'a changé.
    """
    process_monitor.check_and_kill()

    if now - state["last_session_check"] >= session_interval:
        scheduler.check_all_children()
        state["last_session_check"] = now

    if now - state["last_dns_refresh"] >= dns_refresh_interval:
        dns_controller.generate_blocklist()
        dns_controller.reload_dnsmasq()
        state["last_dns_refresh"] = now


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

    dns_controller.generate_blocklist()
    state = {"last_session_check": 0.0, "last_dns_refresh": time.monotonic()}

    try:
        while True:
            run_cycle(
                process_monitor,
                scheduler,
                dns_controller,
                state,
                time.monotonic(),
                session_interval,
                dns_refresh_interval,
            )
            time.sleep(process_interval)
    except KeyboardInterrupt:
        logger.info("MintGuard Daemon arrêté")


if __name__ == "__main__":
    main()
