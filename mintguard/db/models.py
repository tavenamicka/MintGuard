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

from datetime import datetime, time as dt_time, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Child(Base):
    __tablename__ = "children"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    time_rules: Mapped[list["TimeRule"]] = relationship(back_populates="child", cascade="all, delete-orphan")
    activity_logs: Mapped[list["ActivityLog"]] = relationship(back_populates="child", cascade="all, delete-orphan")


class TimeRule(Base):
    __tablename__ = "time_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id"))
    day_of_week: Mapped[int] = mapped_column(Integer)  # 0=Lundi, 6=Dimanche
    start_hour: Mapped[dt_time] = mapped_column(Time)
    end_hour: Mapped[dt_time] = mapped_column(Time)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    child: Mapped["Child"] = relationship(back_populates="time_rules")


class BlockedSite(Base):
    __tablename__ = "blocked_sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain: Mapped[str] = mapped_column(String(255), unique=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)  # social, entertainment, adult...
    blocked: Mapped[bool] = mapped_column(Boolean, default=True)


class BlockedApp(Base):
    __tablename__ = "blocked_apps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_name: Mapped[str] = mapped_column(String(255))
    binary_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    child_id: Mapped[int | None] = mapped_column(ForeignKey("children.id"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    action: Mapped[str] = mapped_column(String(50))  # site_blocked, app_blocked, time_limit_hit...
    details: Mapped[str | None] = mapped_column(String(500), nullable=True)

    child: Mapped["Child"] = relationship(back_populates="activity_logs")


class ParentConfig(Base):
    __tablename__ = "parent_config"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
