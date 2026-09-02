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

from setuptools import setup, find_packages

setup(
    name="mintguard",
    version="0.1.0",
    description="Application de contrôle parental pour Linux Mint",
    author="Mickael Tavenart",
    license="GPL-3.0-or-later",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    ],
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    package_data={
        "mintguard.locales": ["*.json"],
        "mintguard.gui": ["assets/fonts/*", "assets/icons/*"],
    },
    install_requires=[
        "PyQt6>=6.5.0",
        "psutil>=5.10.0",
        "pydantic>=2.0.0",
        "SQLAlchemy>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mintguard=mintguard.main_gui:main",
            "mintguard-daemon=mintguard.daemon:main",
            "mintguard-child-tray=mintguard.child_tray:main",
            "mintguard-parent-tray=mintguard.parent_tray:main",
        ]
    },
    python_requires=">=3.10",
)
