# MintGuard - Application de controle parental pour Linux Mint
# Copyright (C) 2026 Mickael Tavenart
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Listes de référence par catégorie, utilisées par l'onboarding (préréglages par âge)
et par l'écran Settings > Sites (Phase 2 Semaine 4) pour les cases à cocher par catégorie.
Non exhaustif : le parent peut toujours ajouter des sites personnalisés.
"""

SOCIAL_MEDIA_DOMAINS = [
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "snapchat.com",
    "twitter.com",
    "x.com",
]

ENTERTAINMENT_DOMAINS = [
    "youtube.com",
    "netflix.com",
    "twitch.tv",
]

GAMING_DOMAINS = [
    "steampowered.com",
    "epicgames.com",
    "roblox.com",
]

CATEGORIES = {
    "social": SOCIAL_MEDIA_DOMAINS,
    "entertainment": ENTERTAINMENT_DOMAINS,
    "gaming": GAMING_DOMAINS,
}

# Préréglages onboarding par tranche d'âge. Pas de catégorie "contenu adulte" :
# un filtrage fiable demande une liste de blocage tierce maintenue à jour,
# hors scope MVP (voir Settings pour ajout manuel de sites par le parent).
AGE_PRESETS = {
    "young": {  # 6-12 ans
        "daily_hours": 2,
        "blocked_domains": SOCIAL_MEDIA_DOMAINS + GAMING_DOMAINS,
    },
    "teen": {  # 13-18 ans
        "daily_hours": 3,
        "blocked_domains": ["tiktok.com", "instagram.com", "snapchat.com"],
    },
}


def category_for_domain(domain: str) -> str:
    for category, domains in CATEGORIES.items():
        if domain in domains:
            return category
    return "custom"
