# Journal des modifications

Français · [English](CHANGELOG.en.md)

Chaque version de MintGuard est décrite ici, la plus récente en premier. Pour savoir quelle version vous avez, regardez le titre de la fenêtre MintGuard. Pour mettre à jour, voir « Mettre à jour MintGuard » dans le [README](README.md).

## Non publié

Changements présents dans le code mais pas encore dans une version téléchargeable ; ils seront inclus dans la prochaine.

- **Compte d'enfant introuvable** : le Tableau de bord signale un enfant enregistré avec un compte qui n'existe pas sur l'ordinateur (aucune règle ne s'applique alors à lui), et propose « Corriger le compte » sans perdre ses réglages.

## 0.1.2 — 2026-10-11

### Corrections
- **Icône de l'enfant** : un clic ouvre maintenant une petite fenêtre avec le temps restant aujourd'hui (ou « pas de limite aujourd'hui »), les applications et sites bloqués pour l'enfant (avec le temps restant de leur limite quotidienne) et la dernière application fermée. Avant, le clic n'affichait parfois rien du tout, et l'enfant ne voyait les applications bloquées que pendant 30 secondes.
- Les notifications de l'enfant n'affichent plus « Application bloquée : … a été fermé », et utilisent la langue de l'enfant.

## 0.1.1 — 2026-10-11

### À faire après la mise à jour depuis la 0.1.0
- Ouvrez MintGuard. Si la carte « La protection n'est pas encore activée » apparaît, cliquez sur **« Activer la protection maintenant »**.
- Si la carte « Le blocage des sites ne fonctionne pas » apparaît, cliquez sur **« Activer le blocage des sites »**. Sans cette étape, aucun site n'était réellement bloqué en 0.1.0 sur une installation neuve.

### Nouveautés
- **Blocage des sites vérifié et réparable** : le Tableau de bord et l'icône de la zone de notification signalent quand l'ordinateur ne passe pas par MintGuard pour trouver les sites, et un bouton le corrige. Le DNS suit maintenant le réseau courant (portable qui change de Wi-Fi).
- **Libre / Horaires autorisés / Pas d'accès** pour chaque jour de la semaine, au lieu d'une simple case à cocher.
- **Le parent seul sur l'ordinateur** n'est plus soumis aux sites bloqués pour ses enfants. Les règles d'un enfant s'appliquent dès qu'il se connecte.
- **Temps par site mieux compté** : un site reste compté une minute après la dernière activité, et les domaines qui servent son contenu (par exemple les vidéos YouTube) comptent pour lui et sont bloqués avec lui.
- **Applications copiées ou renommées** : une application bloquée est reconnue même si son programme a été copié sous un autre nom.
- **Version affichée** dans le titre de la fenêtre.
- **Après une mise à jour**, la protection se relance d'elle-même (à partir des mises à jour suivantes).

### Corrections
- Plage horaire impossible (fin avant le début, ou qui passe minuit) refusée au lieu de déconnecter l'enfant en permanence.
- Barre de temps du Tableau de bord juste quand une limite quotidienne est plus courte que la plage horaire.
- Applications Flatpak (par exemple Roblox via Sober, ou ZapZap) reconnues sous leur vrai nom.
- Nom de compte enfant inexistant (faute de frappe) refusé avec un message.
- Le service de protection ne s'arrête plus sur une erreur passagère ; un enfant non connecté n'est plus visé par des tentatives de déconnexion.
- Filtrage DNS du pare-feu mis à jour après la suppression puis l'ajout d'un enfant.
- Désinstallation : le DNS d'origine de l'ordinateur est rétabli, et toutes les règles du pare-feu (IPv6 comprise) sont retirées.
- Les avertissements « il reste 10/5/1 minutes » reviennent si vous rallongez le temps de l'enfant.

## 0.1.0 — 2026-10-03

Première version publiée : limites de temps par jour, sites et applications bloqués par enfant, limites quotidiennes, rapports, icônes de notification parent et enfant, interface en 4 langues.
