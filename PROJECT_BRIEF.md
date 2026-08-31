# 📋 MintGuard - Project Brief Complet pour Claude Code

**Dernier mise à jour:** 31 Août 2024  
**Statut:** Prêt pour implémentation  
**Stack:** Python 3.10+ / PyQt6 / systemd / dnsmasq / AppArmor

---

## 🎯 Objectif Global

Créer une application de contrôle parental pour Linux Mint, **simple et accessible pour parents novices**, qui limite l'heure d'utilisation, bloque les sites et applications, avec explications visuelles et support multilingue.

**Non-Tech Target:** Parents 40-60 ans, aucune formation informatique, anxieux face à la tech.

---

## 📦 Spécifications Techniques Globales

### 1. Architecture Système

```
┌─────────────────────────────────────────────────┐
│      Interface Graphique PyQt6 (Parent)          │
│   - Dashboard (Tableau de bord)                  │
│   - Settings (Paramètres)                        │
│   - Reports (Rapports)                           │
│   - Help System (Système d'aide)                 │
└────────────────┬────────────────────────────────┘
                 │ (Communication via D-Bus/IPC)
┌────────────────▼────────────────────────────────┐
│   Backend Daemon (Python systemd service)        │
│   - Gestion règles                               │
│   - Enforcement (DNS, AppArmor, Process Monitor) │
│   - Logging (SQLite)                             │
│   - Notifications                                │
└────┬──────────┬──────────┬───────────┬──────────┘
     │          │          │           │
┌────▼──┐  ┌───▼──┐  ┌────▼──┐  ┌────▼──────┐
│dnsmasq│  │Fire- │  │Process │  │Session    │
│(DNS)  │  │wall  │  │Monitor │  │Manager    │
└───────┘  │(iptls)  │        │  │(systemd)  │
           └──────┘  └───────┘  └───────────┘
```

### 2. Stack Technique

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| **GUI** | PyQt6 | Native Linux, bon support i18n, performance |
| **Backend** | Python 3.10+ | Flexibilité, libs disponibles |
| **Service** | systemd | Auto-start, logging intégré |
| **Filtrage DNS** | dnsmasq | Léger, standard Linux, config simple |
| **Confinement** | AppArmor | Native Linux Mint |
| **BD Logs** | SQLite3 | Zéro config, stockage local sécurisé |
| **IPC** | D-Bus / Socket | Communication GUI ↔ Daemon |
| **i18n** | JSON files | Simple, pas gettext complexe |

### 3. Structure de Répertoires

```
mintguard/
├── README.md                    # Documentation projet
├── CONTRIBUTING.md              # Guide contribution
├── setup.py                     # Installation package
├── mintguard/
│   ├── __init__.py
│   ├── main_gui.py              # Point d'entrée GUI (PyQt6)
│   ├── daemon.py                # Service systemd
│   ├── config.py                # Gestion config
│   ├── logger.py                # Logging système
│   │
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py       # Fenêtre principale
│   │   ├── dashboard.py         # Écran 1: Dashboard
│   │   ├── settings.py          # Écran 2: Paramètres
│   │   ├── reports.py           # Écran 3: Rapports
│   │   ├── onboarding.py        # Écran 4: Onboarding
│   │   ├── help_system.py       # Système d'aide (?)
│   │   ├── styles.py            # Thème/CSS PyQt
│   │   └── dialogs.py           # Popups/dialogs
│   │
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── dns_controller.py    # Gestion dnsmasq
│   │   ├── firewall_controller.py # Gestion iptables
│   │   ├── process_monitor.py   # Monitoring apps
│   │   ├── session_manager.py   # Gestion sessions
│   │   ├── scheduler.py         # Timing/crons
│   │   └── apparmor_controller.py # Gestion AppArmor
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py            # Modèles SQLAlchemy
│   │   ├── database.py          # Connexion BD
│   │   └── migrations.py        # Migrations
│   │
│   ├── locales/
│   │   ├── fr.json              # Français
│   │   ├── en.json              # Anglais
│   │   ├── de.json              # Allemand
│   │   ├── es.json              # Espagnol
│   │   ├── it.json              # Italien (future)
│   │   └── loader.py            # Chargeur i18n
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validators.py        # Validation données
│       ├── formatters.py        # Formatage affichage
│       └── security.py          # Fonctions sécurité
│
├── etc/
│   ├── systemd/
│   │   └── mintguard-daemon.service
│   ├── dnsmasq.d/
│   │   └── mintguard.conf
│   ├── apparmor/
│   │   └── mintguard-restrict-child
│   └── sudoers.d/
│       └── mintguard
│
├── tests/
│   ├── test_gui.py
│   ├── test_backend.py
│   ├── test_dns_controller.py
│   ├── test_security.py
│   └── fixtures/
│
├── docs/
│   ├── INSTALLATION.md           # Guide d'installation
│   ├── USER_MANUAL_*.md          # Manuels utilisateur multilingues
│   ├── TECHNICAL.md              # Docs techniques
│   ├── API.md                    # API interne
│   └── SECURITY.md               # Guide sécurité
│
├── assets/
│   ├── icons/                   # Icones 16x16, 32x32, 64x64
│   ├── images/                  # Images aide/tutoriels
│   └── screenshots/             # Screenshots exemples
│
└── scripts/
    ├── install.sh               # Script installation
    ├── uninstall.sh             # Script désinstallation
    └── setup-apparmor.sh        # Setup AppArmor profiles
```

---

## 🎨 Spécifications UX/UI

### Écrans Principaux

#### Écran 1: Dashboard (Vue par défaut)
**Objectif:** Vue d'ensemble instantanée du statut
```
┌─────────────────────────────────┐
│  MintGuard - Tableau de Bord      │
├─────────────────────────────────┤
│ 👤 Enfant: [Sélecteur dropdown] │
│                                  │
│ ✓ Protection: ACTIVE            │
│                                  │
│ ⏰ TEMPS AUJOURD'HUI             │
│    1h 45min / 3h max            │
│    [████████░░]  58%            │
│                                  │
│ 🚫 DERNIÈRE RESTRICTION         │
│    YouTube bloqué à 18:32       │
│    Raison: Site réseaux sociaux │
│                                  │
│ [⚙️ Réglages] [📊 Rapports]     │
└─────────────────────────────────┘
```

**Éléments interactifs:**
- Sélecteur enfant (dropdown)
- Bouton Réglages
- Bouton Rapports
- "?" Aide contexte
- Menu principal (⋮)

#### Écran 2: Paramètres
Trois onglets: **Temps**, **Sites**, **Applications**

**Tab 1: Limitation du Temps**
```
╔════════════════════════════════╗
║ LIMITE DE TEMPS PAR JOUR       ║
╚════════════════════════════════╝

☐ Lundi
   16:00 - 20:00 (4h)  [Modifier]

☑ Mardi  
   16:00 - 20:00 (4h)  [Modifier]

☑ Mercredi
   16:30 - 20:00 (3.5h) [Modifier]

...

☑ Dimanche
   ACCÈS LIBRE (24/24)  [Modifier]

[💾 Sauvegarder] [✕ Annuler]
```

**Tab 2: Blocage des Sites**
```
╔════════════════════════════════╗
║ SITES À BLOQUER                ║
╚════════════════════════════════╝

CATÉGORIES (✓ = Bloquée)
☑ Réseaux sociaux
☑ Divertissement (YouTube, etc)
☐ Jeux en ligne
☑ Contenu adulte
☐ Streaming vidéo

SITES PERSONNALISÉS
✕ tiktok.com
✕ instagram.com
[+ Ajouter un site]

[? Qu'est-ce que "bloquer"?]
[💾 Sauvegarder]
```

**Tab 3: Blocage des Applications**
```
╔════════════════════════════════╗
║ APPLICATIONS À BLOQUER         ║
╚════════════════════════════════╝

☑ Firefox
☑ Chrome / Google Chrome
☑ Discord
☑ Steam
☐ LibreOffice
☐ GIMP

[? Comment bloquer une app?]
[+ Ajouter application]

[💾 Sauvegarder]
```

#### Écran 3: Rapports
```
╔════════════════════════════════╗
║ RAPPORT HEBDOMADAIRE           ║
║ Semaine du 25-31 Août 2024     ║
╚════════════════════════════════╝

📊 TEMPS
  Utilisé: 15h 23min
  Limite:  21h
  Status:  ✓ Respecte limites

🚫 BLOCAGES
  TikTok:     5 fois
  YouTube:    3 fois
  Instagram:  2 fois

✅ BON COMPORTEMENT
  Aucune tentative de contourner

[Voir détail jour par jour]
[Exporter PDF]
```

#### Écran 4: Onboarding (Premier lancement)
**6 étapes, 2 min max total**

1. Bienvenue + Image friendly
2. Sélectionner/créer compte enfant
3. Configuration rapide par âge
4. Créer code de sécurité (PIN)
5. Explications visuelles ("Comment ça marche?")
6. Résumé + "Commencer"

### Éléments de Design Global

**Palette Couleurs:**
- Bleu primaire: #0EA5E9 (actions, éléments principaux)
- Vert: #10B981 (succès, "ok", protection active)
- Orange: #F59E0B (avertissement, attention)
- Rouge: #EF4444 (danger, blocages actifs)
- Gris fond: #F9FAFB (light), #1F2937 (dark)

**Typographie:**
- Police: Inter, Roboto, system-ui
- H1: 28px bold
- H2: 22px bold
- Texte corps: 16px regular
- Labels: 14px regular

**Iconographie:**
- Style: Monolines simples
- 👤, ⏰, 🚫, 📊, ⚙️, 🔒, 📱, 🌍, ❓, 💾, ✅, ⚠️, 🔔

---

## 🌍 Spécifications Multilingues (i18n)

### Structure JSON (locales/fr.json, en.json, etc.)

```json
{
  "app": {
    "name": "MintGuard",
    "tagline": "Pour que vos enfants explorent Internet en toute sécurité"
  },
  "screens": {
    "dashboard": {
      "title": "Tableau de Bord",
      "protection_active": "Protection: ACTIVE",
      "time_today": "Temps aujourd'hui",
      "last_restriction": "Dernière restriction"
    },
    "settings": {
      "title": "Paramètres",
      "time_limit": "Limite de Temps",
      "blocked_sites": "Sites à Bloquer",
      "blocked_apps": "Applications à Bloquer"
    }
  },
  "help": {
    "what_is_blocking": "Qu'est-ce que 'bloquer'? Si vous bloquez un site, votre enfant ne peut pas le visiter...",
    "how_it_works": "Comment ça marche? L'app voit quels sites/apps sont utilisés..."
  },
  "messages": {
    "protection_enabled": "Protection activée ✓",
    "site_blocked": "Ce site est bloqué",
    "quota_exceeded": "Limite de temps dépassée"
  }
}
```

**Langues Phase 1:** FR, EN, DE, ES  
**Langues Phase 2:** IT, PL, NL  
**Auto-détection:** Détecte locale système (LANG env var)

---

## 🔧 Spécifications Backend

### 1. Service systemd (mintguard-daemon)

**Fichier:** `etc/systemd/system/mintguard-daemon.service`

```ini
[Unit]
Description=MintGuard Parental Control Daemon
After=network.target
Requires=dnsmasq.service

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /usr/local/lib/mintguard/daemon.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Responsabilités:**
- Démarrer au boot
- Charger règles depuis BD SQLite
- Appliquer restrictions DNS/AppArmor/firewall
- Monitoring processus enfants
- Générer logs

### 2. Contrôle DNS (dnsmasq)

**Fichier:** `etc/dnsmasq.d/mintguard.conf`

```
# Écouter sur localhost:5353
listen-address=127.0.0.1
port=5353

# Charger blocklists dynamiques
addn-hosts=/var/lib/mintguard/blocklist.hosts

# Log queries
log-queries
log-facility=/var/log/mintguard/dns.log
```

**Python Controller** (`mintguard/backend/dns_controller.py`):
- Générer `/var/lib/mintguard/blocklist.hosts` depuis BD
- Recharger dnsmasq après changements
- Signaler au parent si DNS faile

### 3. Monitoring Processus

**Fichier:** `mintguard/backend/process_monitor.py`

```python
# Pseudocode
while True:
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        if is_blocked_app(proc.name):
            # Terminé avec log
            proc.kill()
            log_action(f"Killed blocked app: {proc.name}")
    
    # Vérifier quota temps d'utilisation
    if time_quota_exceeded():
        loginctl.terminate_user("child_user")
        
    time.sleep(5)
```

### 4. Gestion Sessions (systemd)

```python
# Logout automatique aux heures limite
def check_session_limits():
    now = datetime.now().time()
    day = now.strftime("%A").lower()
    
    allowed_hours = config.get_allowed_hours(day)
    if not allowed_hours:
        return  # Jour inactif
    
    start, end = allowed_hours
    if not (time.fromisoformat(start) <= now <= time.fromisoformat(end)):
        # Hors heures autorisées
        subprocess.run(["loginctl", "terminate-user", "child"])
        log_action("Auto-logout: Outside allowed hours")
```

### 5. Schéma BD SQLite

```sql
-- Utilisateurs enfants
CREATE TABLE children (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    username TEXT UNIQUE,
    age INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Restrictions horaires
CREATE TABLE time_rules (
    id INTEGER PRIMARY KEY,
    child_id INTEGER FOREIGN KEY,
    day_of_week INTEGER (0=Mon, 6=Sun),
    start_hour TEXT,  -- "16:00"
    end_hour TEXT,    -- "20:00"
    enabled BOOLEAN DEFAULT 1,
    FOREIGN KEY (child_id) REFERENCES children(id)
);

-- Sites bloqués
CREATE TABLE blocked_sites (
    id INTEGER PRIMARY KEY,
    domain TEXT UNIQUE,
    category TEXT,  -- "social", "entertainment", "adult"
    blocked BOOLEAN DEFAULT 1
);

-- Applications bloquées
CREATE TABLE blocked_apps (
    id INTEGER PRIMARY KEY,
    app_name TEXT,
    binary_path TEXT,
    enabled BOOLEAN DEFAULT 1
);

-- Logs d'activité
CREATE TABLE activity_logs (
    id INTEGER PRIMARY KEY,
    child_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT,  -- "site_blocked", "app_blocked", "time_limit_hit"
    details TEXT,  -- domaine, nom app, etc
    FOREIGN KEY (child_id) REFERENCES children(id)
);

-- Configuration parent
CREATE TABLE parent_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP
);
```

---

## 🚀 Plan d'Implémentation (Détaillé)

### Phase 1: Fondations (Semaines 1-2)

**Week 1:**
- [ ] Setup projet Python structure
- [ ] Créer fichiers i18n de base (FR, EN, DE, ES)
- [ ] Initialiser BD SQLite + migrations
- [ ] Créer daemon.py skeleton
- [ ] Tests unitaires infrastructure

**Week 2:**
- [ ] Implémenter config.py + config file loading
- [ ] Créer DNS controller (dnsmasq intégration)
- [ ] Implémenter process monitor
- [ ] Session manager (loginctl)
- [ ] Tests backend

### Phase 2: Interface GUI (Semaines 3-5)

**Week 3:**
- [ ] Setup PyQt6 structure
- [ ] Créer main_window.py
- [ ] Onboarding screens (6 étapes)
- [ ] Thème/styles globaux

**Week 4:**
- [ ] Dashboard screen (complet)
- [ ] Settings screen - Tab Time
- [ ] Settings screen - Tab Sites
- [ ] Help system (? buttons)

**Week 5:**
- [ ] Settings screen - Tab Apps
- [ ] Reports screen
- [ ] Intégration GUI ↔ Backend (D-Bus/IPC)
- [ ] Tests GUI

### Phase 3: Sécurité & Intégration (Semaines 6-7)

**Week 6:**
- [ ] AppArmor profile setup
- [ ] Firewall controller (iptables)
- [ ] Permission/sudo configuration
- [ ] Security audit

**Week 7:**
- [ ] Systemd service setup
- [ ] Installation script
- [ ] Tests sécurité complets
- [ ] Documentation installation

### Phase 4: Testing & Polish (Semaine 8)

- [ ] User testing parents novices
- [ ] Fixes UI/UX
- [ ] Performance optimization
- [ ] Accessibility audit (WCAG 2.1)

---

## 📝 Points de Configuration Importants

### 1. Sudoers Configuration

**Fichier:** `etc/sudoers.d/mintguard`
```
# Permettre à application de faire actions root sans pwd
%mintguard-admin ALL=(ALL) NOPASSWD: /usr/local/bin/mintguard-apply-rules.sh
%mintguard-admin ALL=(ALL) NOPASSWD: /usr/sbin/iptables
%mintguard-admin ALL=(ALL) NOPASSWD: /usr/sbin/dnsmasq
%mintguard-admin ALL=(ALL) NOPASSWD: /bin/loginctl
```

### 2. AppArmor Profile

**Fichier:** `etc/apparmor.d/mintguard-restrict-child`
```
profile mintguard-restrict-child flags=(attach_disconnected) {
  include <abstractions/base>

  # Bloquer Firefox
  deny /usr/bin/firefox rx,
  deny /usr/lib/firefox/** rx,

  # Bloquer Chrome
  deny /usr/bin/google-chrome rx,
  deny /opt/google/** rx,

  # Bloquer Discord
  deny ~/.discord/** rwx,
  deny ~/.config/discord/** rwx,

  # Applications essentielles autorisées
  allow /bin/** rx,
  allow /usr/bin/bash rx,
  allow /usr/bin/python3 rx,
}
```

### 3. Configuration Fichier

**Fichier:** `/etc/mintguard/config.json`
```json
{
  "app": {
    "language": "auto",
    "locale_fallback": "en",
    "theme": "auto"
  },
  "database": {
    "path": "/var/lib/mintguard/mintguard.db"
  },
  "dns": {
    "enabled": true,
    "listen_port": 5353,
    "blocklist_path": "/var/lib/mintguard/blocklist.hosts"
  },
  "monitoring": {
    "process_check_interval": 5,
    "session_check_interval": 60
  },
  "logging": {
    "level": "INFO",
    "path": "/var/log/mintguard/"
  }
}
```

---

## 🧪 Stratégie Testing

### Tests Unitaires
- Backend logic (DNS, monitoring, timers)
- Database migrations
- Config loading
- Validators

### Tests Intégration
- GUI ↔ Backend communication
- Real DNS blocking
- Real AppArmor enforcement
- Real session termination

### Tests Utilisateur
- Parents novices (6-8 personnes)
- Feedback UI/UX
- Temps d'onboarding
- Clarté explications

### Tests Sécurité
- Contournement DNS (VPN test)
- Contournement AppArmor
- Contournement session lock
- Escalade privilèges

---

## 📚 Fichiers de Référence à Créer

1. **TECHNICAL_SPEC.md** - Spécifications techniques détaillées
2. **SECURITY_GUIDE.md** - Guide sécurité & contournements
3. **DEVELOPER_GUIDE.md** - Pour contributeurs
4. **USER_MANUAL_FR.md** - Manuel utilisateur français (avec screenshots)
5. **USER_MANUAL_EN.md** - Manuel utilisateur anglais
6. **API_INTERNAL.md** - API communication GUI/Daemon

---

## 🎯 Critères de Succès MVP

- [ ] Dashboard affiche statut enfant correctement
- [ ] Limitation de temps fonctionne (logout auto)
- [ ] Blocage sites DNS fonctionne
- [ ] Onboarding complété en < 2 min
- [ ] Interface 100% en français + anglais
- [ ] Aide contextuelle sur tous les paramètres
- [ ] Rapports générés correctement
- [ ] Accessible WCAG 2.1 AA (testé)
- [ ] Pas d'erreurs critiques après 1h utilisation
- [ ] Parents novices peuvent tout faire sans terminal

---

## 🔗 Dépendances (Requirements)

```
PyQt6>=6.5.0
PyQt6-sip>=13.5.0
psutil>=5.10.0
pydantic>=2.0.0
SQLAlchemy>=2.0.0
dbus-python>=1.3.0
dnsmasq  # Package système
apparmor # Package système
```

---

## 📞 Notes Additionnelles

- **Pas de données cloud:** Tout reste local, SQLite côté machine
- **Pas de analytics:** Aucun tracking utilisateur
- **Open source:** Sera publié sur GitHub avec licence GPL/MIT
- **Support:** Communauté GitHub + futur live chat
- **Maintenance:** Updates régulières pour correctifs sécurité

---

**Questions/Clarifications pour Claude Code:**
- OK pour démarrer Phase 1 (Fondations) ?
- Préférence entre D-Bus et simple Socket pour GUI ↔ Daemon ?
- Faut-il tester sur vraie machine Linux Mint ou VM ?
- Priorité: tester avec parents réels pendant développement ?
