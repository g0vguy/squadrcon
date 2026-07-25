from squadrcon import events, parsers

SAMPLE_PLAYERS = (
    "ID: 0 | Online IDs: EOS: 000 steam: 76561198000000001 | Name: Alice | "
    "Team ID: 1 | Squad ID: 2 | Is Leader: True | Role: SL\n"
    "ID: 1 | Online IDs: EOS: 000 steam: 76561198000000002 | Name: Bob | "
    "Team ID: 2 | Squad ID: N/A | Is Leader: False | Role: Rifleman"
)


def test_parse_players():
    result = parsers.parse_players(SAMPLE_PLAYERS)
    assert len(result.players) == 2

    alice = result.players[0]
    assert alice.name == "Alice"
    assert alice.steam_id == "76561198000000001"
    assert alice.team_id == "1"
    assert alice.squad_id == "2"
    assert alice.is_leader is True

    bob = result.players[1]
    assert bob.squad_id is None
    assert bob.is_leader is False


def test_parse_players_empty_input():
    result = parsers.parse_players("")
    assert result.players == []


def test_parse_squads():
    raw = (
        "Team ID: 1 (Team One)\n"
        "ID: 1 | Name: Alpha | Size: 4 | Locked: False\n"
        "Team ID: 2 (Team Two)\n"
        "ID: 2 | Name: Bravo | Size: 2 | Locked: True\n"
    )
    result = parsers.parse_squads(raw)
    assert len(result.squads) == 2
    assert result.squads[0].team_id == "1"
    assert result.squads[1].locked is True


def test_parse_broadcast_chat():
    line = "[ChatAll] [SteamID:76561198000000001] Alice : hello team"
    name, obj = parsers.parse_broadcast_line(line)
    assert name == events.CHAT_MESSAGE
    assert obj.player_name == "Alice"
    assert obj.message == "hello team"


def test_parse_broadcast_kick():
    line = "Kicked player 3. [SteamID: 76561198000000003] Charlie"
    name, obj = parsers.parse_broadcast_line(line)
    assert name == events.PLAYER_KICKED
    assert obj.player_name == "Charlie"


def test_parse_broadcast_ban():
    line = "Banned player 4. [SteamID: 76561198000000004] Dave for 1d"
    name, obj = parsers.parse_broadcast_line(line)
    assert name == events.PLAYER_BANNED
    assert obj.player_name == "Dave"
    assert obj.duration == "1d"


def test_parse_broadcast_warn():
    line = 'Remote admin has warned player Eve. Message was "stop team killing"'
    name, obj = parsers.parse_broadcast_line(line)
    assert name == events.PLAYER_WARNED
    assert obj.player_name == "Eve"
    assert obj.reason == "stop team killing"


def test_parse_broadcast_unmatched_line():
    assert parsers.parse_broadcast_line("random log noise") is None


def test_parse_current_map():
    raw = "Current level is Narva, layer is Narva_RAAS_v1"
    result = parsers.parse_current_map(raw)
    assert result.level == "Narva"
    assert result.layer == "Narva_RAAS_v1"


def test_parse_next_map():
    raw = "Next level is Gorodok, layer is Gorodok_AAS_v1"
    result = parsers.parse_next_map(raw)
    assert result.level == "Gorodok"
    assert result.layer == "Gorodok_AAS_v1"
