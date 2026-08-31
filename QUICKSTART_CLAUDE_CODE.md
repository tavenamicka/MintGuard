# 🚀 QuickStart - MintGuard pour Claude Code

## Avant de Commencer

**Lire dans cet ordre:**
1. `PROJECT_BRIEF.md` (vue d'ensemble complète)
2. `ANALYSE_FAISABILITE_TECHNIQUE.html` (détails techniques)
3. `STRATEGIE_UX_UI.html` (design & UX)
4. Ce fichier (instructions de démarrage)

---

## 📁 Initialisation du Projet

### Étape 1: Créer la structure de répertoires

```bash
cd /home/mintguard-project  # ou votre dossier préféré

# Structure complète
mkdir -p mintguard/{mintguard,tests,docs,scripts,etc/{systemd,dnsmasq.d,apparmor,sudoers.d},assets/{icons,images,screenshots}}

cd mintguard/

# Créer les sous-dossiers Python
mkdir -p mintguard/{gui,backend,db,locales,utils}

# Fichiers racine
touch README.md CONTRIBUTING.md setup.py requirements.txt
touch LICENSE  # MIT ou GPL

# Python init files
touch mintguard/__init__.py
touch mintguard/gui/__init__.py
touch mintguard/backend/__init__.py
touch mintguard/db/__init__.py
touch mintguard/locales/__init__.py
touch mintguard/utils/__init__.py
```

### Étape 2: Fichiers de Configuration Initiaux

**requirements.txt:**
```
PyQt6>=6.5.0
PyQt6-sip>=13.5.0
psutil>=5.10.0
pydantic>=2.0.0
SQLAlchemy>=2.0.0
dbus-python>=1.3.0
```

**setup.py (minimal):**
```python
from setuptools import setup, find_packages

setup(
    name="mintguard",
    version="0.1.0",
    description="Parental Control Application for Linux Mint",
    author="Your Name",
    packages=find_packages(),
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
        ]
    },
    python_requires=">=3.10",
)
```

---

## 🌍 Fichiers i18n (Multilingue) - Prêts à Utiliser

**Fichier:** `mintguard/locales/fr.json`

```json
{
  "app": {
    "name": "MintGuard",
    "tagline": "Pour que vos enfants explorent Internet en toute sécurité",
    "version": "0.1.0"
  },
  "common": {
    "ok": "OK",
    "cancel": "Annuler",
    "save": "Sauvegarder",
    "delete": "Supprimer",
    "edit": "Modifier",
    "help": "Aide",
    "close": "Fermer",
    "settings": "Paramètres",
    "dashboard": "Tableau de Bord",
    "reports": "Rapports"
  },
  "dashboard": {
    "title": "Tableau de Bord",
    "protection_active": "Protection: ACTIVE ✓",
    "protection_inactive": "Protection: INACTIVE",
    "child_select": "Enfant",
    "time_today": "Temps aujourd'hui",
    "time_limit": "maximum",
    "last_restriction": "Dernière restriction",
    "no_restrictions": "Aucune restriction ce jour"
  },
  "settings": {
    "title": "Paramètres",
    "time_limits": "Limite de Temps",
    "blocked_sites": "Sites à Bloquer",
    "blocked_apps": "Applications à Bloquer",
    "security": "Sécurité",
    "language": "Langue"
  },
  "time": {
    "monday": "Lundi",
    "tuesday": "Mardi",
    "wednesday": "Mercredi",
    "thursday": "Jeudi",
    "friday": "Vendredi",
    "saturday": "Samedi",
    "sunday": "Dimanche",
    "enabled": "Activé",
    "disabled": "Désactivé",
    "access_all_day": "Accès toute la journée"
  },
  "help": {
    "what_is_blocking": "Qu'est-ce que 'bloquer'?",
    "blocking_explanation": "Si vous bloquez un site, votre enfant ne peut pas le visiter. Il verra un message: 'Cette page est bloquée'.",
    "how_it_works": "Comment ça marche?",
    "how_it_works_explanation": "L'application MintGuard voit quels sites et applications votre enfant utilise, puis applique les restrictions que vous avez configurées.",
    "what_is_category": "Qu'est-ce qu'une catégorie?",
    "category_explanation": "Une catégorie regroupe plusieurs sites similaires. Par exemple, 'Réseaux sociaux' inclut Facebook, Instagram, TikTok, etc."
  },
  "messages": {
    "protection_enabled": "Protection activée ✓",
    "site_blocked": "Ce site est bloqué",
    "app_blocked": "Cette application ne peut pas être utilisée",
    "time_limit_exceeded": "Limite de temps dépassée",
    "settings_saved": "Paramètres sauvegardés ✓",
    "error": "Erreur",
    "warning": "Attention"
  }
}
```

**Fichier:** `mintguard/locales/en.json`

```json
{
  "app": {
    "name": "MintGuard",
    "tagline": "Help your children explore the internet safely",
    "version": "0.1.0"
  },
  "common": {
    "ok": "OK",
    "cancel": "Cancel",
    "save": "Save",
    "delete": "Delete",
    "edit": "Edit",
    "help": "Help",
    "close": "Close",
    "settings": "Settings",
    "dashboard": "Dashboard",
    "reports": "Reports"
  },
  "dashboard": {
    "title": "Dashboard",
    "protection_active": "Protection: ACTIVE ✓",
    "protection_inactive": "Protection: INACTIVE",
    "child_select": "Child",
    "time_today": "Time today",
    "time_limit": "maximum",
    "last_restriction": "Last restriction",
    "no_restrictions": "No restrictions today"
  },
  "settings": {
    "title": "Settings",
    "time_limits": "Time Limits",
    "blocked_sites": "Blocked Sites",
    "blocked_apps": "Blocked Apps",
    "security": "Security",
    "language": "Language"
  },
  "time": {
    "monday": "Monday",
    "tuesday": "Tuesday",
    "wednesday": "Wednesday",
    "thursday": "Thursday",
    "friday": "Friday",
    "saturday": "Saturday",
    "sunday": "Sunday",
    "enabled": "Enabled",
    "disabled": "Disabled",
    "access_all_day": "Access all day"
  },
  "help": {
    "what_is_blocking": "What is 'blocking'?",
    "blocking_explanation": "If you block a site, your child cannot access it. They will see a message: 'This page is blocked'.",
    "how_it_works": "How does it work?",
    "how_it_works_explanation": "MintGuard monitors which websites and applications your child uses, then applies the restrictions you configured.",
    "what_is_category": "What is a category?",
    "category_explanation": "A category groups similar websites together. For example, 'Social Media' includes Facebook, Instagram, TikTok, etc."
  },
  "messages": {
    "protection_enabled": "Protection enabled ✓",
    "site_blocked": "This site is blocked",
    "app_blocked": "This application cannot be used",
    "time_limit_exceeded": "Time limit exceeded",
    "settings_saved": "Settings saved ✓",
    "error": "Error",
    "warning": "Warning"
  }
}
```

**Créer aussi:** `mintguard/locales/de.json` et `mintguard/locales/es.json` (mêmes clés, traductions différentes)

**Fichier:** `mintguard/locales/loader.py`

```python
import json
import os
from pathlib import Path
from typing import Dict, Any

class I18nLoader:
    """Charge les traductions multilingues"""
    
    def __init__(self, lang: str = "en"):
        self.lang = lang
        self.translations: Dict[str, Any] = {}
        self.load_language(lang)
    
    def load_language(self, lang: str) -> bool:
        """Charge un fichier de langue"""
        locale_path = Path(__file__).parent / f"{lang}.json"
        
        if not locale_path.exists():
            print(f"⚠️  Language file not found: {lang}.json, falling back to English")
            locale_path = Path(__file__).parent / "en.json"
        
        try:
            with open(locale_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            self.lang = lang
            return True
        except Exception as e:
            print(f"Error loading language file: {e}")
            return False
    
    def get(self, key: str, fallback: str = "") -> str:
        """Récupère une traduction par clé (ex: 'dashboard.title')"""
        keys = key.split('.')
        value = self.translations
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return fallback
        
        return str(value) if value else fallback
    
    def __call__(self, key: str) -> str:
        """Raccourci: i18n("dashboard.title") au lieu de i18n.get()"""
        return self.get(key)

# Singleton global pour utiliser dans l'app
_i18n_instance = None

def get_i18n(lang: str = None) -> I18nLoader:
    """Obtient l'instance i18n globale"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18nLoader(lang or "en")
    return _i18n_instance

# Alias pour facilité d'utilisation
_ = get_i18n

# Usage dans l'app:
# from mintguard.locales.loader import _
# label = _("dashboard.title")  # Retourne la valeur traduite
```

---

## 🗄️ Base de Données SQLite

**Fichier:** `mintguard/db/models.py`

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Child(Base):
    __tablename__ = 'children'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    username = Column(String(100), unique=True)
    age = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    time_rules = relationship("TimeRule", back_populates="child")
    activity_logs = relationship("ActivityLog", back_populates="child")

class TimeRule(Base):
    __tablename__ = 'time_rules'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'))
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    start_hour = Column(Time)
    end_hour = Column(Time)
    enabled = Column(Boolean, default=True)
    
    child = relationship("Child", back_populates="time_rules")

class BlockedSite(Base):
    __tablename__ = 'blocked_sites'
    
    id = Column(Integer, primary_key=True)
    domain = Column(String(255), unique=True)
    category = Column(String(50))  # social, adult, entertainment
    blocked = Column(Boolean, default=True)

class BlockedApp(Base):
    __tablename__ = 'blocked_apps'
    
    id = Column(Integer, primary_key=True)
    app_name = Column(String(255))
    binary_path = Column(String(500))
    enabled = Column(Boolean, default=True)

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String(50))  # site_blocked, app_blocked, time_limit_hit
    details = Column(String(500))
    
    child = relationship("Child", back_populates="activity_logs")

class ParentConfig(Base):
    __tablename__ = 'parent_config'
    
    key = Column(String(100), primary_key=True)
    value = Column(String(500))
    updated_at = Column(DateTime, default=datetime.utcnow)
```

**Fichier:** `mintguard/db/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from .models import Base

DB_PATH = Path("/var/lib/mintguard/mintguard.db")

def init_db():
    """Initialise la base de données"""
    engine = create_engine(f'sqlite:///{DB_PATH}')
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Crée une session de BD"""
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session()
```

---

## 🎯 Structure Minimale pour Démarrage

**Fichier:** `mintguard/main_gui.py` (skeleton)

```python
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from mintguard.locales.loader import get_i18n

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.i18n = get_i18n("en")  # TODO: Charger depuis config
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(self.i18n("app.name"))
        self.setGeometry(100, 100, 800, 600)
        
        # Placeholder pour test
        label = QLabel(self.i18n("dashboard.title"))
        layout = QVBoxLayout()
        layout.addWidget(label)
        
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

**Fichier:** `mintguard/daemon.py` (skeleton)

```python
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mintguard-daemon")

def main():
    logger.info("MintGuard Daemon Started")
    
    try:
        while True:
            # TODO: Monitoring logic here
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("MintGuard Daemon Stopped")

if __name__ == "__main__":
    main()
```

---

## 📝 Instructions pour Claude Code

### Phase 1: Fondations (Semaine 1)

**Tâches prioritaires:**
1. ✅ Créer structure projet (répertoires, fichiers init)
2. ✅ Setup i18n multilingue complet (FR, EN, DE, ES)
3. ✅ Initialiser BD SQLite avec schéma
4. ✅ Implémenter config.py (charger fichiers config)
5. ✅ Créer daemon.py skeleton + systemd service
6. ✅ Tests unitaires infrastructure

**Checklist:**
- [ ] `python setup.py install` fonctionne
- [ ] `mintguard` lance l'app (GUI vide)
- [ ] `mintguard-daemon` lance le daemon
- [ ] Tous les fichiers i18n chargent sans erreur
- [ ] BD SQLite crée sans erreur
- [ ] Tests unitaires passent (pytest)

### Phase 2: Commencer Interface GUI

**Ne pas faire avant Phase 1 complétée!**

- Créer screens PyQt6 dans `mintguard/gui/`
- Suivre le design dans `STRATEGIE_UX_UI.html`
- Utiliser i18n pour tous les textes
- Tests GUI au fur et à mesure

---

## 🔗 Ressources de Référence

**Documents à Consulter:**
- `PROJECT_BRIEF.md` - Spécifications complètes
- `ANALYSE_FAISABILITE_TECHNIQUE.html` - Détails techniques
- `STRATEGIE_UX_UI.html` - Design & UX

**Dépôt GitHub (futur):**
- Issues pour tracker tasks
- Pull requests pour code review
- Wiki pour documentation

---

## ⚡ Commandes Utiles Claude Code

```bash
# Test que tout fonctionne
python -m pytest tests/ -v

# Installation développement
pip install -e .

# Lancer l'app GUI
mintguard

# Lancer le daemon (nécessite root)
sudo mintguard-daemon

# Lancer tests avec couverture
pytest tests/ --cov=mintguard

# Générer la structure (initial setup)
python scripts/init_project.py
```

---

## 🎯 Prochaines Étapes

**Après initialisation du projet:**
1. Vérifier que la structure est OK
2. Tester chargement i18n
3. Tester création/connexion BD
4. Commencer Phase 1 GUI
5. Intégrer avec tests utilisateur parents

---

**Questions fréquentes pour Claude Code:**

Q: "Dois-je installer vraiment dnsmasq/AppArmor pour tester?"  
A: Non, d'abord, développer la GUI. Les contrôleurs backend peuvent être mockés pour tests.

Q: "Quelle langue par défaut?"  
A: Auto-détect depuis `$LANG` env var. Fallback à anglais.

Q: "La BD doit être en root?"  
A: Oui, `/var/lib/mintguard/` avec permissions restrictives (400).

Q: "Comment tester sans être root?"  
A: Pendant dev, utiliser `/tmp/mintguard-test.db` pour tests.

---

**Bonne chance ! 🚀**
