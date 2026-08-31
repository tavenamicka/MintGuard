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

from pathlib import Path

from sqlalchemy import Engine, create_engine
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

    _engine = create_engine(f"sqlite:///{path}")
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
