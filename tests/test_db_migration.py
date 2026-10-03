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

"""`init_db()` n'a pas de système de migration (pas d'Alembic, juste `create_all`, qui ne crée
que les tables manquantes) : les nouvelles colonnes (`TimeRule.daily_budget_minutes`,
`BlockedApp.child_id`/`daily_budget_minutes`) doivent être ajoutées manuellement à une BD
existante par `_migrate_schema()`. Ces tests simulent une BD "ancienne" (créée avant l'ajout
de ces colonnes) pour vérifier que la migration s'applique et reste idempotente."""

import sqlite3

from sqlalchemy import create_engine

from mintguard.db.database import _migrate_schema


def make_legacy_db(path) -> None:
    """Crée une BD avec le schéma tel qu'il existait avant ce changement (colonnes manquantes),
    directement en SQL brut - `_migrate_schema` doit fonctionner sur une vraie BD de production
    déjà peuplée avec l'ancien schéma, pas sur une BD dérivée du schéma actuel."""
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE children (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                username VARCHAR(100) UNIQUE,
                age INTEGER,
                created_at DATETIME
            );
            CREATE TABLE time_rules (
                id INTEGER PRIMARY KEY,
                child_id INTEGER REFERENCES children(id),
                day_of_week INTEGER,
                start_hour TIME,
                end_hour TIME,
                enabled BOOLEAN
            );
            CREATE TABLE blocked_apps (
                id INTEGER PRIMARY KEY,
                app_name VARCHAR(255),
                binary_path VARCHAR(500),
                enabled BOOLEAN
            );
            CREATE TABLE blocked_sites (
                id INTEGER PRIMARY KEY,
                domain VARCHAR(255) UNIQUE,
                category VARCHAR(50),
                blocked BOOLEAN
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def columns_of(path, table) -> set[str]:
    conn = sqlite3.connect(path)
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


def test_migration_adds_missing_columns(tmp_path):
    db_path = tmp_path / "legacy.db"
    make_legacy_db(db_path)
    assert "daily_budget_minutes" not in columns_of(db_path, "time_rules")

    engine = create_engine(f"sqlite:///{db_path}")
    _migrate_schema(engine)
    engine.dispose()

    assert "daily_budget_minutes" in columns_of(db_path, "time_rules")
    assert "child_id" in columns_of(db_path, "blocked_apps")
    assert "daily_budget_minutes" in columns_of(db_path, "blocked_apps")
    assert "child_id" in columns_of(db_path, "blocked_sites")
    assert "daily_budget_minutes" in columns_of(db_path, "blocked_sites")


def test_migration_is_idempotent(tmp_path):
    db_path = tmp_path / "legacy.db"
    make_legacy_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO blocked_sites (domain, category, blocked) VALUES ('tiktok.com', 'social', 1)")
    conn.commit()
    conn.close()

    engine = create_engine(f"sqlite:///{db_path}")
    _migrate_schema(engine)
    _migrate_schema(engine)  # ne doit pas lever (colonnes deja presentes, contrainte deja retiree)
    engine.dispose()

    assert "daily_budget_minutes" in columns_of(db_path, "time_rules")


def test_migration_drops_blocked_sites_domain_unique_constraint(tmp_path):
    """blocked_sites.domain etait UNIQUE au niveau table avant le scoping par enfant -
    ALTER TABLE ADD COLUMN ne peut pas retirer cette contrainte SQLite ; sans le rebuild de
    table dedie, deux enfants partageant un domaine bloque leveraient IntegrityError."""
    db_path = tmp_path / "legacy.db"
    make_legacy_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO blocked_sites (domain, category, blocked) VALUES ('tiktok.com', 'social', 1)")
    conn.commit()
    conn.close()

    engine = create_engine(f"sqlite:///{db_path}")
    _migrate_schema(engine)
    engine.dispose()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO blocked_sites (domain, category, blocked, child_id) VALUES ('tiktok.com', 'social', 1, 2)"
        )
        conn.commit()
        rows = conn.execute("SELECT child_id FROM blocked_sites WHERE domain='tiktok.com'").fetchall()
    finally:
        conn.close()
    assert len(rows) == 2


def test_migration_reassigns_blocked_apps_to_sole_child(tmp_path):
    db_path = tmp_path / "legacy.db"
    make_legacy_db(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO children (name, username) VALUES ('Elisa', 'mintguard-test-child')")
    conn.execute("INSERT INTO blocked_apps (app_name, enabled) VALUES ('flatpak', 1)")
    conn.commit()
    conn.close()

    engine = create_engine(f"sqlite:///{db_path}")
    _migrate_schema(engine)
    engine.dispose()

    conn = sqlite3.connect(db_path)
    try:
        child_id = conn.execute("SELECT id FROM children WHERE username='mintguard-test-child'").fetchone()[0]
        row_child_id = conn.execute("SELECT child_id FROM blocked_apps WHERE app_name='flatpak'").fetchone()[0]
    finally:
        conn.close()
    assert row_child_id == child_id


def test_migration_leaves_blocked_apps_global_with_multiple_children(tmp_path):
    db_path = tmp_path / "legacy.db"
    make_legacy_db(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO children (name, username) VALUES ('Elisa', 'child-one')")
    conn.execute("INSERT INTO children (name, username) VALUES ('Tom', 'child-two')")
    conn.execute("INSERT INTO blocked_apps (app_name, enabled) VALUES ('flatpak', 1)")
    conn.commit()
    conn.close()

    engine = create_engine(f"sqlite:///{db_path}")
    _migrate_schema(engine)
    engine.dispose()

    conn = sqlite3.connect(db_path)
    try:
        row_child_id = conn.execute("SELECT child_id FROM blocked_apps WHERE app_name='flatpak'").fetchone()[0]
    finally:
        conn.close()
    assert row_child_id is None  # ambigu avec plusieurs enfants : reste une règle globale


def test_migration_reassigns_blocked_sites_to_sole_child(tmp_path):
    db_path = tmp_path / "legacy.db"
    make_legacy_db(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO children (name, username) VALUES ('Elisa', 'mintguard-test-child')")
    conn.execute("INSERT INTO blocked_sites (domain, category, blocked) VALUES ('tiktok.com', 'social', 1)")
    conn.commit()
    conn.close()

    engine = create_engine(f"sqlite:///{db_path}")
    _migrate_schema(engine)
    engine.dispose()

    conn = sqlite3.connect(db_path)
    try:
        child_id = conn.execute("SELECT id FROM children WHERE username='mintguard-test-child'").fetchone()[0]
        row_child_id = conn.execute("SELECT child_id FROM blocked_sites WHERE domain='tiktok.com'").fetchone()[0]
    finally:
        conn.close()
    assert row_child_id == child_id


def test_migration_leaves_blocked_sites_global_with_multiple_children(tmp_path):
    db_path = tmp_path / "legacy.db"
    make_legacy_db(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO children (name, username) VALUES ('Elisa', 'child-one')")
    conn.execute("INSERT INTO children (name, username) VALUES ('Tom', 'child-two')")
    conn.execute("INSERT INTO blocked_sites (domain, category, blocked) VALUES ('tiktok.com', 'social', 1)")
    conn.commit()
    conn.close()

    engine = create_engine(f"sqlite:///{db_path}")
    _migrate_schema(engine)
    engine.dispose()

    conn = sqlite3.connect(db_path)
    try:
        row_child_id = conn.execute("SELECT child_id FROM blocked_sites WHERE domain='tiktok.com'").fetchone()[0]
    finally:
        conn.close()
    assert row_child_id is None  # ambigu avec plusieurs enfants : reste une règle globale
