# MintGuard — Guide utilisateur

*Pour que vos enfants explorent Internet en toute sécurité.*

Ce guide s'adresse aux parents. Pour l'installation technique, voir [INSTALLATION.md](INSTALLATION.md).

---

## 1. Qu'est-ce que MintGuard ?

MintGuard est une application de contrôle parental pour Linux Mint. Elle tourne en deux parties :

- **Un programme de surveillance** qui démarre avec l'ordinateur et applique vos règles en continu, même si vous n'ouvrez jamais la fenêtre principale.
- **Une fenêtre de configuration** (celle que vous ouvrez pour changer les réglages, voir les rapports) : c'est elle que ce guide décrit.

MintGuard peut :
- **Bloquer des sites web** (réseaux sociaux, jeux en ligne, divertissement, ou n'importe quel site que vous ajoutez vous-même).
- **Bloquer des applications** (jeux, messageries, etc.).
- **Limiter les horaires d'utilisation de l'ordinateur**, avec fermeture automatique de la session en dehors des heures autorisées.
- **Vous montrer un résumé** de ce qui a été bloqué dans la semaine.

**Prérequis important** : MintGuard suppose que chaque enfant a **son propre compte Linux** sur l'ordinateur (pas de compte partagé avec vous ou entre enfants). C'est ce compte qui permet à MintGuard de savoir qui utilise l'ordinateur.

---

## 2. Premier lancement : l'assistant de configuration

Au premier lancement, un assistant en 6 étapes vous guide :

1. **Bienvenue** — présentation rapide.
2. **Quel enfant voulez-vous protéger ?** — le prénom de l'enfant (pour l'affichage) et son **nom d'utilisateur Linux** (le nom du compte, pas le prénom — demandez à un technicien si vous ne le connaissez pas).
3. **Configuration rapide** — deux profils prêts à l'emploi selon l'âge :
   - **6-12 ans** : 2h d'accès par jour, réseaux sociaux et jeux en ligne bloqués.
   - **13-18 ans** : 3h d'accès par jour, principaux réseaux sociaux limités (TikTok, Instagram, Snapchat).
   Vous pourrez tout modifier ensuite dans les Réglages — ce ne sont que des points de départ.
4. **Code PIN** — un code à 4 chiffres (jusqu'à 8) qui protège l'accès aux Réglages et aux Rapports. **Notez-le et gardez-le en lieu sûr** : voir la section [Sécurité et confidentialité](#5-sécurité-et-confidentialité) pour ce qui se passe si vous l'oubliez.
5. **Comment ça marche** — rappel visuel du principe (MintGuard observe, applique les règles, vous informe).
6. **C'est prêt !** — vos réglages sont enregistrés, direction le Tableau de bord.

**Dernière étape possible** : si le Tableau de bord affiche un bandeau **« La protection n'est pas encore activée »**, cliquez sur **« Activer la protection maintenant »**. Une seule fenêtre système s'ouvre pour confirmer (votre mot de passe habituel) — après quoi la protection tourne réellement, même fenêtre principale fermée. Ce bandeau ne réapparaît normalement pas ensuite (la protection redémarre seule avec l'ordinateur), sauf en cas de problème système — il suffit alors de recliquer dessus.

---

## 3. Le tableau de bord

C'est l'écran principal, ouvert à chaque lancement de l'application.

- **Sélecteur d'enfant** : si vous avez configuré plusieurs enfants, choisissez lequel afficher.
- **Statut de protection** : `ACTIVE` si au moins une règle (horaire ou site bloqué) est configurée pour cet enfant, sinon `INACTIVE`.
- **Créneau du jour** : les horaires autorisés aujourd'hui pour l'enfant sélectionné, ou « Accès libre aujourd'hui » si aucune règle n'est définie pour ce jour.
- **Dernière restriction** : le dernier événement enregistré (application bloquée, ou limite de temps atteinte).
- **Boutons Réglages / Rapports** : demandent votre code PIN avant de s'ouvrir.

---

## 4. Modifier les réglages

Cliquer sur **Réglages** vous demande votre code PIN, puis ouvre trois onglets.

### Onglet Temps

Pour chaque jour de la semaine : activer/désactiver une plage horaire, et définir l'heure de début et de fin. En dehors de cette plage, **la session de l'enfant se ferme automatiquement**. Une icône dans la zone de notification de l'enfant prévient quelques minutes avant (10, 5 puis 1 minute) et signale les applications fermées car interdites — un avertissement à titre indicatif, pas garanti (dépend de l'affichage systray du bureau) : prévenez tout de même votre enfant de cette règle à l'avance. Un jour sans plage activée = accès libre ce jour-là.

Au moment même où le temps est écoulé, votre enfant n'est **pas déconnecté sans prévenir** : un écran s'affiche au premier plan avec un compte à rebours (environ 1 à 2 minutes) l'invitant à enregistrer son travail avant la fermeture réelle de la session. Cet écran-là, contrairement au popup systray, s'affiche toujours, quel que soit le bureau utilisé.

**Limiter le temps d'utilisation par jour** : en plus de la plage horaire, vous pouvez cocher « Limiter le temps d'utilisation par jour » pour fixer un nombre de minutes maximum utilisées dans la journée (par exemple 120 min/jour), même si la plage horaire elle-même est plus large. Dès que ce quota est atteint, la session de l'enfant se ferme automatiquement pour le reste de la journée, comme pour une sortie de plage horaire — le quota repart à zéro le lendemain.

Les changements ne sont appliqués qu'après avoir cliqué sur **Sauvegarder**.

### Onglet Sites

Des catégories à cocher (Réseaux sociaux, Divertissement, Jeux en ligne) et une liste de sites personnalisés que vous pouvez ajouter/retirer librement (ex: `tiktok.com`).

**Important** : contrairement aux horaires, le blocage de sites s'applique à **tout l'ordinateur**, pas seulement au compte de l'enfant sélectionné — parce qu'un seul système de blocage DNS gère toute la machine. Si plusieurs enfants partagent le même ordinateur, ils partagent la même liste de sites bloqués.

**Ce que voit concrètement votre enfant** : MintGuard n'affiche pas de page « Ce site est bloqué ». Le blocage se fait au niveau du réseau (DNS), avant même que la page ne commence à se charger — votre enfant voit donc l'écran d'erreur habituel de son navigateur, du type « Impossible d'établir une connexion » ou « Ce site est inaccessible ». C'est normal : ça signifie que le blocage fonctionne, pas qu'il y a un problème technique. Il est utile d'expliquer cela à votre enfant à l'avance, pour qu'il comprenne qu'un tel message est une limite fixée par vous, et non une panne d'internet.

Les changements sur cet onglet sont enregistrés **sans bouton Sauvegarder** — mais comptez jusqu'à une trentaine de secondes avant que le blocage soit réellement actif (le temps que le service en arrière-plan relise la liste).

### Onglet Applications

Les applications installées sur l'ordinateur sont détectées automatiquement et proposées à cocher par catégorie, plus une liste personnalisée pour ajouter d'autres noms de programme. Une application bloquée qui tourne déjà est fermée automatiquement dans les secondes qui suivent. Comme pour les sites, ceci s'applique à l'ordinateur entier.

**Limiter le temps d'utilisation par jour (au lieu d'un blocage total)** : pour une application cochée, vous pouvez activer « Limiter le temps d'utilisation par jour » plutôt que de la bloquer complètement. Votre enfant peut alors l'utiliser jusqu'au nombre de minutes par jour que vous fixez (par exemple 30 min/jour) ; une fois ce temps dépassé, l'application se ferme automatiquement et ne peut plus être rouverte jusqu'au lendemain.

---

## 5. Sécurité et confidentialité

- **Le code PIN** protège l'ouverture des Réglages et des Rapports. Il est stocké de façon sécurisée (jamais en clair).
- **Code PIN oublié ?** Cliquez sur « Code PIN oublié ? » dans la fenêtre de saisie. MintGuard affiche d'abord un message expliquant ce qui va se passer, avant qu'une fenêtre du système ne s'ouvre — pour que cette dernière ne soit pas une surprise. Vous devrez confirmer avec **le mot de passe de votre propre compte** (celui que vous utilisez pour ouvrir une session sur cet ordinateur) via cette fenêtre système — la même que celle qui apparaît par exemple pour installer une mise à jour. Ce mot de passe n'est jamais géré ni stocké par MintGuard lui-même. Une fois confirmé, vous pourrez définir un nouveau code PIN immédiatement.
- Les journaux d'activité et la base de données de MintGuard ne sont lisibles que par un compte administrateur — votre enfant n'y a pas accès, même s'il sait où chercher.

---

## 6. Les rapports

L'onglet **Rapports** (protégé par le code PIN) montre, sur les 7 derniers jours et par enfant :
- Les applications bloquées et combien de fois chacune a été fermée.
- Le nombre de fois où la limite de temps a été atteinte (fermeture automatique de session) — que ce soit en sortant de la plage horaire autorisée ou en dépassant un quota quotidien de minutes.

**MintGuard n'affiche pas le "temps d'écran total utilisé"** : l'application ne mesure pas en continu la durée des sessions, seulement les événements de blocage. C'est un choix assumé — plutôt que d'inventer un chiffre approximatif, nous préférons ne rien afficher que vous ne pourriez pas pleinement vérifier vous-même.

---

## 7. Ce que MintGuard ne fait pas (limites à connaître)

Pour rester honnête sur ce que la protection couvre réellement :

- **Pas de filtrage "contenu adulte" automatique.** Un filtrage fiable nécessiterait une liste de sites tenue à jour par un tiers, ce que MintGuard n'intègre pas pour l'instant. Vous pouvez ajouter manuellement des sites dans l'onglet Sites.
- **Un enfant techniquement débrouillard pourrait tenter de contourner le blocage** en configurant un service de résolution DNS chiffré (« DNS-over-HTTPS ») directement dans son navigateur. MintGuard bloque le changement de résolveur DNS classique, mais pas cette méthode plus avancée.
- **Le blocage d'applications repose sur le nom du programme**, pas sur un contrôle plus profond du système — une application renommée pourrait passer inaperçue.
- **MintGuard suppose un compte Linux dédié par enfant.** Si votre enfant utilise votre propre session ou une session partagée, la protection ne s'applique pas correctement.
- **Un seul ordinateur = un ensemble de sites bloqués partagé** entre tous les enfants qui l'utilisent (voir section Sites ci-dessus).

Ces limites sont documentées volontairement plutôt que cachées : mieux vaut savoir ce que la protection couvre réellement.

---

## 8. Besoin d'aide ?

- Chaque écran comporte des boutons **« ? »** avec une explication simple en langage courant.
- Pour un problème technique (installation, daemon qui ne démarre pas), voir [INSTALLATION.md](INSTALLATION.md) ou contactez la personne qui a installé MintGuard chez vous.
