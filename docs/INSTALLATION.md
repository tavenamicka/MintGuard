# Installation — MintGuard

## Environnement de développement (toute plateforme)

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e .
pip install -r requirements.txt
pytest tests/ -v
```

Les contrôleurs backend qui dépendent d'outils Linux (`iptables`, `loginctl`, `apparmor_parser`) échouent proprement hors Linux — c'est attendu en dev (voir `mintguard/backend/*.py`, méthode `test()`).

## Installation cible (Linux Mint, Phase 3+)

Nécessite les privilèges root pour :
- Installer le service systemd (`etc/systemd/mintguard-daemon.service`)
- Configurer dnsmasq (`etc/dnsmasq.d/mintguard.conf`)
- Charger le profil AppArmor (`etc/apparmor/mintguard-restrict-child`)
- Installer les règles sudoers (`etc/sudoers.d/mintguard`)

Ces étapes seront scriptées dans `scripts/install.sh` (Phase 3).

## Variables d'environnement utiles (dev)

| Variable | Effet |
|---|---|
| `MINTGUARD_CONFIG_PATH` | Chemin alternatif vers `config.json` (par défaut `/etc/mintguard/config.json`) |
| `LANG` | Langue auto-détectée si `app.language` = `"auto"` dans la config |
