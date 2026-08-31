# Conformité licence — MintGuard (GPL-3.0-or-later)

## Dépendances et compatibilité GPL v3

| Dépendance | Licence | Compatible GPLv3 ? | Note |
|---|---|---|---|
| PyQt6 | GPL v3 (ou commerciale, Riverbank) | ✅ Oui | Utiliser la distribution PyPI standard (édition GPL). Ne pas utiliser une licence commerciale Riverbank sans revoir ce tableau. |
| PyQt6-sip | BSD | ✅ Oui | Permissive, compatible. |
| psutil | BSD-3-Clause | ✅ Oui | Permissive, compatible. |
| pydantic | MIT | ✅ Oui | Permissive, compatible. |
| SQLAlchemy | MIT | ✅ Oui | Permissive, compatible. |
| dbus-python | LGPL-2.1-or-later | ✅ Oui | LGPL est compatible avec une utilisation dans un projet GPL v3. |
| pytest / pytest-cov | MIT | — | Dépendances de dev/test uniquement, non distribuées avec l'application. |
| dnsmasq, AppArmor, systemd, iptables/loginctl | GPL v2 / GPL v2-or-later (paquets système) | ✅ Oui | Invoqués comme outils externes via `subprocess` (pas de liaison de code) — pas de contrainte de compatibilité de licence sur MintGuard. |

**Conclusion :** aucune dépendance directe n'est incompatible avec la GPL v3. Point de vigilance unique : PyQt6 doit rester en édition GPL (c'est le cas par défaut via `pip install PyQt6`).

## À revérifier

- À chaque ajout de dépendance dans `requirements.txt` / `setup.py`, mettre à jour ce tableau avant de merger.
- Si PyQt6 est un jour remplacé par une lib sous licence incompatible (ex: propriétaire sans exception), la distribution GPL de MintGuard ne serait plus possible sans changer de toolkit GUI.
