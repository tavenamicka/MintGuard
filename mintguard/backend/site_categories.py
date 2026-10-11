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


# Domaines techniques servant le contenu d'un site sans porter son nom : une video YouTube
# est servie par *.googlevideo.com, une page Instagram charge ses images depuis
# cdninstagram.com... Sans eux, le temps passe sur le site etait presque invisible dans les
# requetes DNS (seul le chargement de la page touche youtube.com), et un site bloque restait
# partiellement accessible (lecteurs integres sur d'autres sites). Utilises a la fois par
# SiteUsageTracker (decompte) et DNSController (blocage). Liste volontairement limitee aux
# domaines propres a chaque service, jamais a un CDN partage avec d'autres sites.
COMPANION_DOMAINS = {
    "youtube.com": ["googlevideo.com", "ytimg.com", "youtu.be", "youtube-nocookie.com", "youtubei.googleapis.com"],
    "facebook.com": ["fbcdn.net", "fb.com", "facebook.net"],
    "instagram.com": ["cdninstagram.com"],
    "tiktok.com": ["tiktokcdn.com", "tiktokv.com", "tiktokcdn-us.com", "tiktokv.us"],
    "snapchat.com": ["sc-cdn.net", "snap-dev.net"],
    "twitter.com": ["twimg.com", "t.co"],
    "x.com": ["twimg.com", "t.co"],
    "netflix.com": ["nflxvideo.net", "nflximg.net", "nflxext.com", "nflxso.net"],
    "twitch.tv": ["ttvnw.net", "jtvnw.net"],
    "roblox.com": ["rbxcdn.com"],
    "steampowered.com": ["steamstatic.com", "steamcommunity.com"],
    "epicgames.com": ["epicgames.dev"],
}


def domains_for_site(domain: str) -> list[str]:
    """Le domaine enregistre par le parent, suivi de ses domaines techniques connus."""
    return [domain] + COMPANION_DOMAINS.get(domain.strip().lower(), [])


def category_for_domain(domain: str) -> str:
    for category, domains in CATEGORIES.items():
        if domain in domains:
            return category
    return "custom"


def domain_matches(queried: str, registered: str) -> bool:
    """Vrai si `queried` EST le domaine `registered`, ou l'un de ses sous-domaines (ex:
    www.youtube.com, i.ytimg.com...) - les logs de requetes DNS contiennent le nom litteral
    interroge, jamais le domaine enregistre nu (voir SiteUsageTracker)."""
    queried = queried.strip().lower().rstrip(".")
    registered = registered.strip().lower()
    return queried == registered or queried.endswith("." + registered)
