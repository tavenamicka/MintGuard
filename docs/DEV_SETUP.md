# Setup développeur — MintGuard

Guide pour une nouvelle personne qui rejoint le projet. Objectif : environnement fonctionnel et `pytest tests/ -v` au vert en moins de 5 minutes.

## 1. Cloner et installer

```bash
git clone <url-du-depot>   # dépôt local pour l'instant, pas encore de remote public
cd MintGuard

python -m venv .venv
source .venv/bin/activate    # Windows : .venv\Scripts\activate

pip install -e .
pip install -r requirements.txt
```

## 2. Vérifier que tout fonctionne

```bash
pytest tests/ -v
```

45 tests doivent passer. Sur une machine non-Linux (Windows/Mac), les tests des contrôleurs `FirewallController`, `SessionManager` et `AppArmorController` passent quand même : leur méthode `test()` détecte l'absence d'`iptables`/`loginctl`/`apparmor_parser` et retourne `False` proprement (assertion `isinstance(..., bool)`, pas d'exception).

## 3. Où travailler selon la tâche

| Je veux... | Fichier(s) |
|---|---|
| Ajouter/modifier un écran GUI | `mintguard/gui/` (Phase 2), `mintguard/main_gui.py` |
| Changer la logique de blocage DNS | `mintguard/backend/dns_controller.py` |
| Changer la logique de limitation de temps | `mintguard/backend/scheduler.py`, `mintguard/backend/session_manager.py` |
| Ajouter une table/colonne en BD | `mintguard/db/models.py` (puis `pytest tests/test_db.py`) |
| Ajouter un texte affiché à l'utilisateur | `mintguard/locales/*.json` (les 4 langues), jamais de texte en dur dans le code |
| Changer une valeur de config par défaut | `mintguard/config.py` (`DEFAULT_CONFIG`) + `etc/config.json.example` |

## 4. Règles de code (voir aussi CONTRIBUTING.md)

- **i18n obligatoire** : `from mintguard.locales.loader import get_i18n` puis `get_i18n()("dashboard.title")`. Jamais de string affichable en dur.
- **Header GPL** : tout nouveau fichier `.py` doit commencer par le header de copyright (copier celui d'un fichier existant dans `mintguard/`).
- **Tests obligatoires** : tout changement de comportement s'accompagne d'un test dans `tests/`.
- **BD** : ne jamais taper du SQL brut, passer par les modèles SQLAlchemy (`mintguard/db/models.py`) et `get_session()`.

## 5. Config en dev (sans /etc)

Par défaut MintGuard lit `/etc/mintguard/config.json`, absent en dev. Pas besoin de le créer : `mintguard/config.py` retombe sur `DEFAULT_CONFIG` si le fichier n'existe pas. Pour tester avec une config custom :

```bash
export MINTGUARD_CONFIG_PATH=/tmp/mintguard-config.json   # Windows: $env:MINTGUARD_CONFIG_PATH
```

## 6. IDE

- **PyQt6 + autocomplétion** : les stubs `PyQt6-stubs` ne sont pas installés par défaut ; l'autocomplétion peut être limitée selon l'IDE, ce n'est pas bloquant.
- **VS Code** : sélectionner l'interpréteur `.venv` (Ctrl+Shift+P → Python: Select Interpreter).
- Les tests GUI (`tests/test_gui.py`) forcent `QT_QPA_PLATFORM=offscreen` pour tourner sans display — pas besoin d'un environnement graphique pour `pytest`.

## 7. Étapes suivantes

Voir [SUIVI.md](../SUIVI.md) pour l'état d'avancement courant et [PROJECT_BRIEF.md](../PROJECT_BRIEF.md) pour le plan de phases complet.
