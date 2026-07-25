import re

from . import types

PLAYER_LINE = re.compile(
    r"ID:\s*(?P<id>\d+)\s*\|.*?steam:\s*(?P<steam>\d+)\s*\|\s*"
    r"Name:\s*(?P<name>.*?)\s*\|\s*Team ID:\s*(?P<team>\d+)\s*\|\s*"
    r"Squad ID:\s*(?P<squad>[\w/-]+)\s*\|\s*Is Leader:\s*(?P<leader>True|False)"
    r"(?:\s*\|\s*Role:\s*(?P<role>\S+))?",
    re.IGNORECASE,
)

TEAM_HEADER = re.compile(r"Team ID:\s*(?P<team>\d+)")
SQUAD_LINE = re.compile(
    r"ID:\s*(?P<id>\d+)\s*\|\s*Name:\s*(?P<name>.*?)\s*\|\s*"
    r"Size:\s*(?P<size>\d+)\s*\|\s*Locked:\s*(?P<locked>True|False)",
    re.IGNORECASE,
)

CHAT = re.compile(
    r"\[(?P<chat_type>Chat\w+)]\s*\[SteamID:(?P<steam>\d+)]\s*(?P<name>.*?)\s*:\s*(?P<msg>.*)"
)
KICK = re.compile(r"Kicked player \d+\.\s*\[SteamID:\s*(?P<steam>\d+)]\s*(?P<name>.*)")
BAN = re.compile(
    r"Banned player \d+\.\s*\[SteamID:\s*(?P<steam>\d+)]\s*(?P<name>.*?)(?:\s+for\s+(?P<duration>.+))?$"
)
WARN = re.compile(r'warned player\s+(?P<name>.*?)\.\s*Message was\s*"(?P<reason>.*)"')


def parse_players(raw):
    players = []
    for line in raw.splitlines():
        m = PLAYER_LINE.search(line)
        if not m:
            continue
        squad_id = m.group("squad")
        players.append(types.Player(
            player_id=m.group("id"),
            steam_id=m.group("steam"),
            name=m.group("name").strip(),
            team_id=m.group("team"),
            squad_id=None if squad_id in ("N/A", "-") else squad_id,
            is_leader=m.group("leader").lower() == "true",
            role=m.group("role"),
        ))
    return types.Players(raw=raw, players=players)


def parse_squads(raw):
    squads = []
    current_team = None
    for line in raw.splitlines():
        th = TEAM_HEADER.search(line)
        if th:
            current_team = th.group("team")
            continue
        sm = SQUAD_LINE.search(line)
        if sm and current_team is not None:
            squads.append(types.Squad(
                squad_id=sm.group("id"),
                name=sm.group("name").strip(),
                team_id=current_team,
                size=int(sm.group("size")),
                locked=sm.group("locked").lower() == "true",
            ))
    return types.Squads(raw=raw, squads=squads)


def parse_broadcast_line(line):
    from . import events

    m = CHAT.search(line)
    if m:
        return events.CHAT_MESSAGE, types.Message(
            chat_type=m.group("chat_type"),
            steam_id=m.group("steam"),
            player_name=m.group("name").strip(),
            message=m.group("msg"),
        )

    m = KICK.search(line)
    if m:
        return events.PLAYER_KICKED, types.Kick(player_name=m.group("name").strip())

    m = BAN.search(line)
    if m:
        return events.PLAYER_BANNED, types.Ban(
            player_name=m.group("name").strip(), duration=m.group("duration")
        )

    m = WARN.search(line)
    if m:
        return events.PLAYER_WARNED, types.Warn(
            player_name=m.group("name").strip(), reason=m.group("reason")
        )

    return None


def parse_current_map(raw):
    m = re.search(r"Current level is (?P<level>.+?), layer is (?P<layer>.+)", raw)
    return types.CurrentMap(m.group("level").strip(), m.group("layer").strip()) if m else None


def parse_next_map(raw):
    m = re.search(r"Next level is (?P<level>.+?), layer is (?P<layer>.+)", raw)
    return types.NextMap(m.group("level").strip(), m.group("layer").strip()) if m else None
