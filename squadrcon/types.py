from dataclasses import dataclass, field


@dataclass
class Player:
    player_id: str
    steam_id: str
    name: str
    team_id: str = None
    squad_id: str = None
    is_leader: bool = False
    role: str = None


@dataclass
class Players:
    raw: str
    players: list = field(default_factory=list)


@dataclass
class Squad:
    squad_id: str
    name: str
    team_id: str
    size: int = None
    locked: bool = False


@dataclass
class Squads:
    raw: str
    squads: list = field(default_factory=list)


@dataclass
class Message:
    chat_type: str
    steam_id: str
    player_name: str
    message: str


@dataclass
class Warn:
    player_name: str
    reason: str


@dataclass
class Kick:
    player_name: str


@dataclass
class Ban:
    player_name: str
    duration: str = None


@dataclass
class CurrentMap:
    level: str
    layer: str


@dataclass
class NextMap:
    level: str
    layer: str
