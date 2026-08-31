# Contribuer à MintGuard

## Licence

MintGuard est sous licence [GPL-3.0-or-later](LICENSE). En contribuant, vous acceptez que vos contributions soient distribuées sous cette même licence. Ajoutez-vous à [AUTHORS.md](AUTHORS.md) dans votre première pull request. Tout nouveau fichier source doit inclure le header de copyright GPL (voir un fichier existant dans `mintguard/` pour le modèle exact).

## Workflow

1. Lire [PROJECT_BRIEF.md](PROJECT_BRIEF.md) et [CLAUDE_CODE_BRIEFING.md](CLAUDE_CODE_BRIEFING.md) pour l'architecture et les phases.
2. Respecter l'i18n : aucun texte en dur, toujours passer par `get_i18n()` / `_("clé.imbriquée")`.
3. Ajouter/mettre à jour les tests dans `tests/` pour tout changement de comportement.
4. `pytest tests/ -v` doit passer avant tout commit.
5. Commits réguliers, messages clairs (voir historique du dépôt pour le style).

## Ajouter une langue

1. Dupliquer `mintguard/locales/en.json`, traduire toutes les valeurs (garder les clés identiques).
2. Ajouter le code langue à `SUPPORTED_LANGUAGES` dans `mintguard/locales/loader.py`.
3. `pytest tests/test_i18n.py` vérifie que toutes les langues ont le même jeu de clés.

## Tester les contrôleurs backend

Les contrôleurs dans `mintguard/backend/` dépendent d'outils Linux (`iptables`, `loginctl`, `apparmor_parser`, `dnsmasq`). Chacun expose une méthode `test()` qui vérifie que l'outil est accessible sans modifier l'état système — utilisée par `tests/test_backend.py`.
