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

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from mintguard.config import get_config
from mintguard.db.models import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_db_path() -> Path:
    return Path(get_config().get("database.path", "/var/lib/mintguard/mintguard.db"))


def init_db(db_path: Path | None = None) -> Engine:
    """Initialise la base de données (crée les tables si absentes)."""
    global _engine, _SessionLocal
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Le daemon (root, écrit toutes les 5 s via UsageTracker) et la GUI (relit toutes les
    # 5 s, écrit à chaque réglage) partagent ce fichier SQLite. Par défaut, un écrivain qui
    # trouve la BD verrouillée échoue immédiatement sur "database is locked" — remonté en
    # exception non rattrapée jusque dans un slot Qt côté GUI, ou en perte du cumul de temps
    # côté daemon. `timeout` fait patienter l'écrivain, WAL permet aux lecteurs de continuer
    # pendant une écriture (les deux sont nécessaires : WAL seul ne sérialise pas deux
    # écrivains).
    _engine = create_engine(f"sqlite:///{path}", connect_args={"timeout": 15.0})

    @event.listens_for(_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _record):  # pragma: no cover - dépend du driver
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

    Base.metadata.create_all(_engine)
    _SessionLocal = sessionmaker(bind=_engine)

    # Le daemon (root) et la GUI (utilisateur normal, groupe mintguard-admin)
    # partagent ce fichier. Selon lequel le crée en premier, l'umask peut
    # retirer le droit d'écriture du groupe (ex: 644 au lieu de 660) — on
    # le force explicitement. Le dossier parent (setgid, cf. install.sh)
    # gère déjà l'héritage du groupe ; sans effet réel hors POSIX (dev Windows).
    try:
        path.chmod(0o660)
    except OSError:
        pass

    return _engine


def get_session() -> Session:
    """Crée une session de BD, en initialisant la BD si nécessaire."""
    if _SessionLocal is None:
        init_db()
    return _SessionLocal()


@contextmanager
def session_scope() -> Iterator[Session]:
    """`get_session()` avec fermeture garantie et rollback en cas d'erreur.

    Le motif `session = get_session(); try: ... finally: session.close()` est répété une
    trentaine de fois dans le projet ; il ferme bien la session mais laisse une transaction
    partiellement appliquée si `commit()` lève. À privilégier pour tout nouveau code, et à
    substituer progressivement à l'existant.
    """
    session = get_session()
    try:
        yield session
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
