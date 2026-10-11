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

import json
import logging
import os
import pwd
import re
import socket
import struct
import threading
from datetime import date, datetime, time, timedelta

from mintguard.backend.scheduler import Scheduler
from mintguard.db.database import get_session
from mintguard.db.models import ActivityLog, AppDailyUsage, BlockedApp, BlockedSite, Child, SiteDailyUsage, utcnow
from mintguard.utils.formatters import local_to_utc

logger = logging.getLogger("mintguard.backend.status_server")

_SO_PEERCRED_FMT = "3i"  # pid, uid, gid (struct ucred, Linux)
_RECENT_BLOCKS_WINDOW_SECONDS = 30
_CLIENT_TIMEOUT_SECONDS = 2.0
# Format des détails journalisés par ProcessMonitor ("Application bloquée : discord",
# "Quota atteint : steam (60 min/jour)") : phrase en français, on n'en garde que le nom.
_BLOCK_DETAILS_RE = re.compile(r"^(?:Application bloquée|Quota atteint) : (\S+)")


class StatusServer:
    """Socket Unix local, lecture seule : permet à un compte enfant (aucun accès à la BD
    partagée, voir database.py) de connaître son propre temps restant, sa période de grâce en
    cours le cas échéant (voir Scheduler._grace_deadlines) et ses applis bloquées récemment,
    sans exposer quoi que ce soit d'un autre compte.

    Pas de canal push : le client (mintguard-child-tray) interroge par polling. Une
    connexion = un échange (une ligne JSON en requête, une ligne JSON en réponse), pas de
    session persistante.
    """

    def __init__(self, scheduler: Scheduler, socket_path: str = "/run/mintguard/status.sock"):
        self.scheduler = scheduler
        self.socket_path = socket_path
        self._sock: socket.socket | None = None

    def start(self) -> None:
        """Crée le socket et démarre la boucle d'acceptation dans un thread daemon."""
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.bind(self.socket_path)
        # Un socket Unix nécessite la permission d'écriture sur le fichier spécial pour
        # qu'un autre utilisateur (l'enfant) puisse s'y connecter - la permission d'exécution
        # sur /run/mintguard (RuntimeDirectory=, voir etc/systemd/mintguard-daemon.service)
        # ne suffit pas à elle seule.
        os.chmod(self.socket_path, 0o666)
        self._sock.listen(5)
        threading.Thread(target=self._serve_forever, daemon=True).start()
        logger.info("StatusServer en écoute sur %s", self.socket_path)

    def _serve_forever(self) -> None:
        assert self._sock is not None
        while True:
            try:
                conn, _ = self._sock.accept()
            except OSError:
                return
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn: socket.socket) -> None:
        try:
            # Sans délai, un client qui se connecte sans jamais rien envoyer bloquait un thread
            # indéfiniment : n'importe quel compte (le socket est en 0666) pouvait en ouvrir des
            # milliers et épuiser les threads du daemon.
            conn.settimeout(_CLIENT_TIMEOUT_SECONDS)
            uid = self._peer_uid(conn)
            raw = conn.recv(4096)
            if not raw:
                return
            request = json.loads(raw.decode("utf-8", errors="replace").strip() or "{}")
            if request.get("cmd") != "status":
                conn.sendall((json.dumps({"error": "unknown_cmd"}) + "\n").encode("utf-8"))
                return
            response = self._build_status(uid)
            conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as e:
            logger.warning("Requête StatusServer invalide: %s", e)
        finally:
            conn.close()

    @staticmethod
    def _peer_uid(conn: socket.socket) -> int:
        creds = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize(_SO_PEERCRED_FMT))
        _pid, uid, _gid = struct.unpack(_SO_PEERCRED_FMT, creds)
        return uid

    def _build_status(self, uid: int) -> dict:
        try:
            username = pwd.getpwuid(uid).pw_name
        except KeyError:
            return {"is_child": False}

        db_session = get_session()
        try:
            child = db_session.query(Child).filter_by(username=username).first()
            if child is None:
                return {"is_child": False}

            # ActivityLog.timestamp est stocke en UTC naif (mintguard.db.models.utcnow) - il faut
            # comparer avec la meme reference, pas l'heure locale (datetime.now()).
            since = utcnow() - timedelta(seconds=_RECENT_BLOCKS_WINDOW_SECONDS)
            recent = (
                db_session.query(ActivityLog)
                .filter(
                    ActivityLog.child_id == child.id,
                    ActivityLog.action == "app_blocked",
                    ActivityLog.timestamp >= since,
                )
                .all()
            )
            recent_blocks = [self._app_name_from_details(log.details) for log in recent if log.details]
            rules = self._rules_for_child(db_session, child.id)
        finally:
            db_session.close()

        return {
            "is_child": True,
            "minutes_remaining": self.scheduler.get_minutes_remaining(child.id),
            "grace_seconds_remaining": self.scheduler.get_grace_seconds_remaining(child.id),
            "recent_blocks": recent_blocks,
            **rules,
        }

    @staticmethod
    def _app_name_from_details(details: str | None) -> str | None:
        if not details:
            return None
        match = _BLOCK_DETAILS_RE.match(details)
        return match.group(1) if match else details

    @staticmethod
    def _rules_for_child(db_session, child_id: int) -> dict:
        """Ce qui s'applique à cet enfant aujourd'hui, pour la fenêtre ouverte au clic sur son
        icône : applications et sites bloqués (avec le temps restant s'ils ont un quota) et
        dernière application fermée aujourd'hui. Avant, l'enfant ne voyait que les applis
        fermées dans les 30 dernières secondes - un clic plus tard ne montrait rien.

        Règle propre à l'enfant prioritaire sur une règle globale du même nom, comme côté
        ProcessMonitor/DNSController."""
        today = date.today().isoformat()

        def remaining(budget: int | None, used_seconds: int) -> int | None:
            return None if budget is None else max(0, budget * 60 - used_seconds) // 60

        apps: dict[str, BlockedApp] = {}
        for app in (
            db_session.query(BlockedApp)
            .filter(BlockedApp.enabled.is_(True))
            .filter((BlockedApp.child_id == child_id) | (BlockedApp.child_id.is_(None)))
            .all()
        ):
            if app.child_id is not None or app.app_name not in apps:
                apps[app.app_name] = app
        app_usage = {
            row.app_name: row.seconds_used
            for row in db_session.query(AppDailyUsage).filter_by(child_id=child_id, date=today).all()
        }

        sites: dict[str, BlockedSite] = {}
        for site in (
            db_session.query(BlockedSite)
            .filter(BlockedSite.blocked.is_(True))
            .filter((BlockedSite.child_id == child_id) | (BlockedSite.child_id.is_(None)))
            .all()
        ):
            if site.child_id is not None or site.domain not in sites:
                sites[site.domain] = site
        site_usage = {
            row.domain: row.seconds_used
            for row in db_session.query(SiteDailyUsage).filter_by(child_id=child_id, date=today).all()
        }

        # ActivityLog.timestamp est en UTC naïf : minuit local converti en UTC.
        midnight_utc = local_to_utc(datetime.combine(date.today(), time()))
        last = (
            db_session.query(ActivityLog)
            .filter(
                ActivityLog.child_id == child_id,
                ActivityLog.action == "app_blocked",
                ActivityLog.timestamp >= midnight_utc,
            )
            .order_by(ActivityLog.timestamp.desc())
            .first()
        )

        return {
            "blocked_apps": [
                {
                    "name": name,
                    "budget_minutes": app.daily_budget_minutes,
                    "remaining_minutes": remaining(app.daily_budget_minutes, app_usage.get(name, 0)),
                }
                for name, app in sorted(apps.items())
            ],
            "blocked_sites": [
                {
                    "name": domain,
                    "budget_minutes": site.daily_budget_minutes,
                    "remaining_minutes": remaining(site.daily_budget_minutes, site_usage.get(domain, 0)),
                }
                for domain, site in sorted(sites.items())
            ],
            "last_block_today": StatusServer._app_name_from_details(last.details) if last is not None else None,
        }
