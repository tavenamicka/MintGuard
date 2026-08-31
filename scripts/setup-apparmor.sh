#!/usr/bin/env bash
# Confinement AppArmor par utilisateur (enfant) : ECARTE DU MVP, volontairement.
#
# Un profil AppArmor s'attache soit a un chemin binaire (s'applique alors a
# TOUS les utilisateurs de la machine, pas qu'a l'enfant), soit a une session
# via pam_apparmor (une mauvaise config PAM peut bloquer une connexion,
# y compris celle du parent). Le blocage d'applications est deja assure par
# ProcessMonitor (mintguard/backend/process_monitor.py), coherent avec
# l'hypothese deja actee du projet : un ordinateur = un enfant.
#
# Voir SUIVI.md (entree Phase 3) pour le detail de cette decision.
# etc/apparmor/mintguard-restrict-child reste dans le depot comme reference
# pour une eventuelle integration PAM future, non chargee par install.sh.
echo "setup-apparmor.sh : confinement par utilisateur volontairement differe (voir SUIVI.md)."
exit 0
