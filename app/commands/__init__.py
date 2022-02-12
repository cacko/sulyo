__all__ = [
    "avatar_command",
    "logo_command",
    "wiki_command",
    "song_command",
    "lyrics_command",
    "albumart_command",
    "stats_command",
    "tv_command",
    "livescore_command",
    "subscribe_command",
    "unsubscribe_command",
    "subscriptions_command",
    "competitions_command",
    "lineups_command",
    "facts_command",
    "player_command",
    "logo_command",
    "traceroute_command",
    "dig_command",
    "whois_command",
    "tcptraceroute_command",
    "cve_command",
    "cvesubscribe_command",
    "cveunsubscribe_command",
    "cvelistsubscriptions_command",
]

from .avatar import avatar_command
from .logo import logo_command
from .wiki import wiki_command
from .music import song_command, lyrics_command, albumart_command
from .ontv.ontv import (
    stats_command,
    tv_command,
    livescore_command,
    subscribe_command,
    unsubscribe_command,
    competitions_command,
    lineups_command,
    facts_command,
    player_command
)
from .console import (
    whois_command,
    traceroute_command,
    tcptraceroute_command,
    dig_command
)
from .cve import (
    cve_command,
    cvelistsubscriptions_command,
    cvesubscribe_command,
    cveunsubscribe_command
)
