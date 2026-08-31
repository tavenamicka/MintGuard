# 📌 CLAUDE CODE - BRIEFING COMPLET

**Date:** 31 Août 2024  
**Projet:** MintGuard - Application Contrôle Parental Linux Mint  
**Status:** ✅ Prêt pour implémentation  
**Responsable:** Claude Code (Agent IA)

---

## 🎯 Mission Principale

**Développer une application de contrôle parental pour Linux Mint qui:**
- ✅ Limite l'heure d'utilisation de l'ordinateur
- ✅ Bloque des sites web (par catégories + custom)
- ✅ Bloque des applications spécifiques
- ✅ **Multilingue** (FR, EN, DE, ES) avec auto-détection
- ✅ **Ultra-accessible** pour parents NON-TECH (60+ ans, aucune formation informatique)
- ✅ Interface graphique PyQt6 conviviale
- ✅ Explications visuelles et aide contextuelle partout
- ✅ Sécurisée multi-couches (DNS + AppArmor + Process Monitor)

**Slogan:** *"Pour que vos enfants explorent Internet en toute sécurité"*

---

## 📚 Documents de Référence à Lire (DANS CET ORDRE)

### 1. **PROJECT_BRIEF.md** (42 KB - 30 min de lecture)
   - Spécifications techniques complètes
   - Architecture système en détail
   - Schéma BD SQLite
   - Plan d'implémentation par phase (8 semaines)
   - Critères de succès MVP
   - **ACTION:** Comprendre la vision globale + architecture

### 2. **ANALYSE_FAISABILITE_TECHNIQUE.html** (Artifact)
   - Analyse détaillée des technologies
   - Comparaison DNS vs Proxy vs Firewall
   - Prérequis sécurité
   - Contournements possibles & mitigations
   - **ACTION:** Comprendre les choix tech & limitations

### 3. **STRATEGIE_UX_UI.html** (Artifact)
   - Design pour utilisateurs novices (5 principes)
   - Écrans wireframes (Dashboard, Settings, Reports)
   - Onboarding 6 étapes (2 min)
   - Système d'aide contextuelle
   - Accessibilité WCAG 2.1 AA
   - **ACTION:** Comprendre ce que l'utilisateur verra

### 4. **QUICKSTART_CLAUDE_CODE.md** (Ce fichier = instructions de démarrage)
   - Structure projet initiale
   - Fichiers i18n de base
   - Schéma BD SQLite
   - Commandes utiles
   - **ACTION:** Savoir comment initialiser et démarrer

### 5. **CLAUDE_CODE_BRIEFING.md** (Vous êtes ici)
   - Résumé du briefing
   - Points critiques
   - Dépendances entre tasks
   - Questions fréquentes
   - **ACTION:** Vérifier que tout est clair

---

## 🚀 Phase 1: Fondations (Semaines 1-2) - PRIORITÉ ABSOLUE

**But:** Avoir une base solide pour continuer avec GUI.

### Tâches Critiques (Week 1)

```
1. Initialiser structure Python
   - [ ] Créer dossiers (mintguard/, tests/, docs/, etc/)
   - [ ] Fichiers __init__.py
   - [ ] setup.py + requirements.txt
   - Validación: python setup.py install réussit

2. Multilingue i18n (FONDAMENTAL!)
   - [ ] Créer mintguard/locales/loader.py
   - [ ] Fichiers fr.json, en.json, de.json, es.json
   - [ ] Auto-détection langue depuis $LANG
   - Validation: _("dashboard.title") retourne traduction correcte

3. Base de Données SQLite
   - [ ] models.py (SQLAlchemy - Child, TimeRule, BlockedSite, etc.)
   - [ ] database.py (init_db, get_session)
   - [ ] Migrations (Alembic ou simples scripts)
   - Validation: Créer une BD test, insérer données, interroger

4. Configuration Globale
   - [ ] config.py (charger /etc/mintguard/config.json)
   - [ ] Fichier config.json d'exemple
   - [ ] Paths constants (DB, logs, etc.)
   - Validation: config.get("app.language") fonctionne

5. Daemon Skeleton
   - [ ] mintguard/daemon.py (main loop simple)
   - [ ] etc/systemd/mintguard-daemon.service
   - [ ] Logging vers /var/log/mintguard/
   - Validation: systemctl start mintguard-daemon fonctionne
```

### Tâches Importante (Week 2)

```
6. Backend Controllers (Stubs)
   - [ ] DNS Controller (dnsmasq integration)
   - [ ] Process Monitor (kill blocked apps)
   - [ ] Session Manager (loginctl)
   - [ ] Scheduler (check time limits)
   - Validation: Chacun a une méthode test() qui passe

7. Tests Unitaires Infrastructure
   - [ ] Test i18n loader
   - [ ] Test config loading
   - [ ] Test BD operations
   - [ ] Test backend stubs
   - Validation: pytest tests/ réussit 100%

8. Documentation Basique
   - [ ] README.md (installation + usage)
   - [ ] INSTALL.md (étapes installation détaillées)
   - [ ] DEV_SETUP.md (pour contributeurs)
   - Validation: Nouvelles personne peut installer en 5 min
```

---

## 🎨 Phase 2: Interface GUI (Semaines 3-5) - APRÈS Phase 1 COMPLÉTÉE

**But:** Interface parent fonctionnelle et testable.

### Architecture PyQt6

```
mintguard/gui/
├── main_window.py          # Fenêtre principale + menu
├── dashboard.py            # Écran 1: Dashboard
├── settings.py             # Écran 2: Settings (3 tabs)
├── reports.py              # Écran 3: Rapports
├── onboarding.py           # Écran 4: Setup initial 6 étapes
├── help_system.py          # Système aide (?)
├── dialogs.py              # Popups/dialogs réutilisables
├── styles.py               # CSS PyQt (thème global)
└── widgets.py              # Widgets réutilisables
```

### Semaine 3: Onboarding + Structure

```
- [ ] PyQt6 basic app template
- [ ] Onboarding screens (6 étapes)
- [ ] Système de navigation entre écrans
- [ ] Thème/styles global (couleurs, fonts)
- [ ] Test: Onboarding se complète en 2 min
```

### Semaine 4: Dashboard + Settings

```
- [ ] Dashboard complet (affiche enfant, temps, restrictions)
- [ ] Settings - Time Limits tab
- [ ] Settings - Blocked Sites tab
- [ ] Settings - Blocked Apps tab
- [ ] Communication GUI ↔ Backend (D-Bus ou Socket)
- [ ] Test: Toutes les actions sauvegardent correctement
```

### Semaine 5: Reports + Polish

```
- [ ] Écran Rapports (graphiques, stats)
- [ ] Système d'aide contextuelle (? buttons partout)
- [ ] Menu principal (⋮ dropdown)
- [ ] Notifications simples (toast messages)
- [ ] Test: Interface 100% fonctionnelle
```

---

## 🔐 Phase 3: Sécurité & Intégration (Semaines 6-7)

**ATTENTION:** Nécessite ROOT pour tester réellement

```
- [ ] AppArmor profile pour confiner enfant
- [ ] Firewall rules (iptables)
- [ ] Sudo configuration (actions sans password)
- [ ] Permission fichiers (DB read-only pour enfant)
- [ ] Tests sécurité (essayer contourner, trouver failles)
```

---

## 🧪 Phase 4: Testing & Release (Semaine 8)

```
- [ ] User Testing (parents réels, feedback UX)
- [ ] Performance tests (lancement, responsive)
- [ ] Accessibility tests (WCAG 2.1 AA)
- [ ] Security audit
- [ ] Bug fixes
- [ ] Documentation finalization
- [ ] Release v0.1.0
```

---

## 🔴 Points CRITIQUES (Ne pas oublier!)

### 1. **i18n DOIT être implémenté dans Phase 1**
   - Pas de textes en dur dans le code ("if lang == 'fr':")
   - **Utiliser:** `_("dashboard.title")` partout
   - TOUS les écrans doivent supporter FR, EN, DE, ES

### 2. **Accessibilité pour parents âgés**
   - Police minimum 14px
   - Contraste WCAG AA (4.5:1)
   - Raccourcis clavier
   - Support lecteur écran (NVDA)
   - Pas de couleur seule (utiliser icons aussi)

### 3. **Sécurité - Permissions Strictes**
   - DB en `/var/lib/mintguard/` avec 400 perms
   - Config en `/etc/mintguard/` avec root:root ownership
   - Daemon en root, GUI peut être utilisateur
   - Pas de mot de passe parent stocké en clair

### 4. **Tests AVANT chaque étape**
   - Phase 1 = 100% tests infrastructure
   - Phase 2 = Tests GUI au fur et à mesure
   - Phase 3 = Tests sécurité réels
   - Ne pas attendre fin pour tester!

### 5. **Documentation = Livrables**
   - README.md (pour GitHub)
   - USER_MANUAL_FR/EN/DE/ES.md
   - INSTALL.md (step-by-step)
   - TECHNICAL.md (pour devs)
   - SECURITY.md (pour admins)

---

## 📊 Dépendances entre Tasks

```
Phase 1 (Fondations)
  ├→ i18n loader ✓ (tous les autres dépendent de ça)
  ├→ BD SQLite ✓
  ├→ config.py ✓
  └→ daemon.py + backend stubs ✓
       ↓
Phase 2 (GUI) - DÉPEND DE Phase 1 100%
  ├→ PyQt6 basic app
  ├→ Dashboard screen
  ├→ Settings screens
  ├→ Reports screen
  └→ Communication GUI ↔ Backend
       ↓
Phase 3 (Sécurité) - PEUT COMMENCER en parallèle avec Phase 2 Week 4
  ├→ AppArmor implementation
  ├→ Firewall rules
  └→ Sudo configuration
       ↓
Phase 4 (Testing & Release) - APRÈS Phase 2 + 3 complétées
```

---

## 🎓 Ce que CLAUDE CODE doit faire

### ✅ À FAIRE
1. **Lire TOUS les documents** (sérieusement, c'est important)
2. **Respecter l'architecture** décrite dans PROJECT_BRIEF
3. **Utiliser i18n** pour tous les textes
4. **Tester à chaque étape** (pas "je testerai plus tard")
5. **Documenter son code** (docstrings + commentaires)
6. **Faire des commits réguliers** avec messages clairs
7. **Poser des questions** si quelque chose n'est pas clair
8. **Intégrer le feedback** des tests utilisateurs

### ❌ À NE PAS FAIRE
1. **Coder sans lire les docs** ("je vais commencer et voir")
2. **Commencer Phase 2 avant Phase 1 terminée** (dépendances!)
3. **Ignorer i18n** ("je ferai français plus tard")
4. **Passer la sécurité** ("on sécurisera en release")
5. **Oublier tests** ("ça fonctionne sur ma machine")
6. **Faire de gros commits** ("code d'1 semaine d'un coup")
7. **Inventer une architecture nouvelle** (suivre PROJECT_BRIEF)

---

## 🤔 Questions Fréquentes pour CLAUDE CODE

**Q: Par où je commence exactement?**  
R: Lire PROJECT_BRIEF.md (section "Plan d'Implémentation"), puis QUICKSTART_CLAUDE_CODE.md. Phase 1 Week 1, Task 1.

**Q: Dois-je installer Linux Mint réellement?**  
R: Non, d'abord sur machine dev (Docker/VM OK). Tests réels seulement Phase 3.

**Q: La BD doit être SQLite?**  
R: Oui, c'est plus simple (zéro server externe). Jamais PostgreSQL/MySQL pour app parental locale.

**Q: Je fais quoi si une spec n'est pas claire?**  
R: Relire PROJECT_BRIEF. Si encore pas clair, demander clarifications (les docs sont complètes, mais pas exhaustives).

**Q: Combien de temps Phase 1 va prendre?**  
R: 7-10 jours si full-time. C'est fondamental donc prendre le temps.

**Q: Je dois supporter Mac/Windows aussi?**  
R: NON. Linux Mint only pour MVP. Après c'est autre projet.

**Q: Quelle est la taille cible de l'app?**  
R: GUI + daemon < 20 MB total. Performance: lancer en 2 sec, no memory leaks.

**Q: Faut-il une API REST pour la GUI?**  
R: Non, D-Bus ou simple socket (localhost) suffit. API REST c'est future.

**Q: Comment tester sans être root?**  
R: Phase 1-2: Utiliser `/tmp` pour test DB. Phase 3 réel: besoin de root, VM linux ok.

---

## 📦 Ressources Disponibles

**Tous les documents fournis sont dans `/home/claude/`:**
- `PROJECT_BRIEF.md` - Spécifications
- `ANALYSE_FAISABILITE_TECHNIQUE.html` - Techniques
- `STRATEGIE_UX_UI.html` - Design UX
- `QUICKSTART_CLAUDE_CODE.md` - Instructions démarrage
- `CLAUDE_CODE_BRIEFING.md` - Ce fichier

**Tous ces documents seront fournis au Claude Code agent.**

---

## ✅ Checklist Pre-Implementation

**Avant de coder quoi que ce soit, CLAUDE CODE doit:**

- [ ] Lire PROJECT_BRIEF.md EN ENTIER
- [ ] Lire les 3 autres artifacts
- [ ] Lire QUICKSTART_CLAUDE_CODE.md
- [ ] Poser toutes les questions qui viennent à l'esprit
- [ ] Confirmer qu'il comprend l'architecture
- [ ] Confirmer qu'il comprend les phases
- [ ] Confirmer qu'il comprend les points critiques
- [ ] Commencer Phase 1 Week 1 Task 1

---

## 🎯 Succès = ?

Le projet est réussi quand:

1. ✅ **Interface:** Parent peut tout faire sans terminal (15 min de formation max)
2. ✅ **Multilingue:** FR/EN/DE/ES tous fonctionnels, auto-détection
3. ✅ **Sécurité:** Enfant NE PEUT PAS contourner (sauf escalade root)
4. ✅ **UX:** Parents 60+ ans trouvent ça facile (user testing confirms)
5. ✅ **Perf:** App lance en 2 sec, daemon consomme < 2% CPU
6. ✅ **Code:** Clean, testable, documenté (80%+ coverage)
7. ✅ **Accessible:** WCAG 2.1 AA passant (automated + manual tests)
8. ✅ **Production-ready:** Prêt pour GitHub, releases, community

---

## 📞 Dernières Notes

**Ceci est un GROS projet.** 8 semaines full-time c'est réaliste. Mais:
- La structure est claire
- Les specs sont détaillées
- Les phases sont bien définies
- Les risques sont identifiés
- La faisabilité est prouvée

**Claude Code, vous avez tout ce qu'il faut pour réussir. 🚀**

Si quelque chose n'est pas clair, **C'EST LE MOMENT DE DEMANDER.**

---

**Prêt à commencer? Phase 1 Week 1 Task 1: Initialiser structure projet.**

Bonne chance! 💪
