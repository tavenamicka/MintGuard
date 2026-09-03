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

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from mintguard.config import get_config
from mintguard.db.models import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None

# (table, colonne, type SQL) a ajouter si absente d'une BD existante. `create_all()` ne cree
# que les tables manquantes, jamais une colonne manquante sur une table deja presente - une BD
# de production deja peuplee (BlockedApp, TimeRule...) ne recoit donc jamais les nouvelles
# colonnes sans cette migration explicite.
_COLUMN_MIGRATIONS = [
    ("time_rules", "daily_budget_minutes", "INTEGER"),
    ("blocked_apps", "child_id", "INTEGER REFERENCES children(id)"),
    ("blocked_apps", "daily_budget_minutes", "INTEGER"),
]


def _migrate_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        for table, column, sql_type in _COLUMN_MIGRATIONS:
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            if column not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"))

        # blocked_apps.child_id vient d'etre ajoutee : les lignes existantes sont NULL
        # ("s'applique a tous les enfants"). Avec un seul enfant en base (cas courant), on les
        # rattache explicitement pour qu'elles restent visibles/editables dans l'onglet
        # Applications, desormais filtre par enfant - une base multi-enfants est ambigue, on
        # n'y touche pas (la ligne reste globale).
        children = conn.execute(text("SELECT id FROM children")).fetchall()
        if len(children) == 1:
            conn.execute(
                text("UPDATE blocked_apps SET child_id = :child_id WHERE child_id IS NULL"),
                {"child_id": children[0][0]},
            )


def get_db_path() -> Path:
    return Path(get_config().get("database.path", "/var/lib/mintguard/mintguard.db"))


def has_data_dir_access() -> bool:
    """Vrai si l'utilisateur courant peut lire/écrire le dossier de la BD partagée.

    À vérifier *avant* toute connexion SQLite : sans ce garde-fou explicite, un parent
    pas encore dans le groupe mintguard-admin (ex. juste après l'installation du .deb,
    avant la reconnexion de session requise) voit l'appli planter sur un
    `sqlite3.OperationalError: unable to open database file` — trace Python illisible,
    et invisible de toute façon puisque l'appli est lancée depuis le menu, pas un
    terminal (trouvé en usage réel, voir SUIVI.md).
    """
    return os.access(get_db_path().parent, os.R_OK | os.W_OK | os.X_OK)


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
    _migrate_schema(_engine)
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
