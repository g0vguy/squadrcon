# squadrcon

[![CI](https://github.com/yourname/squadrcon/actions/workflows/ci.yml/badge.svg)](https://github.com/yourname/squadrcon/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/squadrcon.svg)](https://pypi.org/project/squadrcon/)
[![Python versions](https://img.shields.io/pypi/pyversions/squadrcon.svg)](https://pypi.org/project/squadrcon/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Lightweight RCON client and CLI for Squad game servers. Pure Python,
zero runtime dependencies.

## Features

- Connect and authenticate over Squad's RCON protocol
- List players / squads with parsed, typed output
- Kick, ban, warn, and switch a player's team
- Live event stream for chat, kicks, bans, warns
- Small CLI for quick server admin from the terminal
- Fully type-hinted, ships a `py.typed` marker

## Install

```bash
pip install squadrcon
```

From source:

```bash
git clone https://github.com/yourname/squadrcon.git
cd squadrcon
pip install .
```

## CLI usage

```bash
squadrcon --host 1.2.3.4 --port 27165 --pass yourRconPass --list
squadrcon --host 1.2.3.4 --port 27165 --pass yourRconPass --kick "PlayerName" --reason "Team killing"
squadrcon --host 1.2.3.4 --port 27165 --pass yourRconPass --kick 76561198000000000 --reason "AFK"
squadrcon --host 1.2.3.4 --port 27165 --pass yourRconPass --switch-team "PlayerName"
```

Env vars work too:

```bash
export SQUAD_HOST=1.2.3.4
export SQUAD_PORT=27165
export SQUAD_PASS=yourRconPass
squadrcon --list
```

## Library usage

```python
from squadrcon import Rcon, RconConfig, events

r = Rcon(RconConfig(host="127.0.0.1", password="123456", port="27165"))

r.emitter.on(events.CHAT_MESSAGE, lambda msg: print("chat:", msg))
r.emitter.on(events.PLAYER_KICKED, lambda k: print("kicked:", k.player_name))

players = r.list_players()
for p in players.players:
    print(p.name, p.steam_id, p.team_id, p.squad_id)

r.kick("SomePlayerName", "AFK")
r.ban("76561198000000000", "1d", "Team killing")
r.switch_team("SomePlayerName")

r.close()
```

More runnable examples are in [`examples/`](examples/):

- [`basic_usage.py`](examples/basic_usage.py) — connect and list players
- [`live_chat_logger.py`](examples/live_chat_logger.py) — stream chat/kick/ban events
- [`auto_balance.py`](examples/auto_balance.py) — switch players to balance team sizes

## API overview

| Method | RCON command | Description |
|---|---|---|
| `list_players()` | `ListPlayers` | Returns a `Players` object with parsed `Player` entries |
| `list_squads()` | `ListSquads` | Returns a `Squads` object with parsed `Squad` entries |
| `kick(target, reason)` | `AdminKick` | Kicks by name or SteamID64 |
| `ban(target, duration, reason)` | `AdminBan` | Bans by name or SteamID64 |
| `warn(target, message)` | `AdminWarn` | Sends an in-game warning |
| `switch_team(target)` | `AdminForceTeamChange` | Moves a player to the opposite team |
| `execute(command)` | any | Sends a raw RCON command, returns raw text |

Events available on `r.emitter`:

`CONNECTED`, `RECONNECTING`, `CLOSE`, `ERROR`, `DATA`, `CHAT_MESSAGE`,
`PLAYER_WARNED`, `PLAYER_KICKED`, `PLAYER_BANNED`

## Layout

```
squadrcon/
  protocol.py   packet framing
  emitter.py    event emitter
  events.py     event name constants
  types.py      parsed data classes
  parsers.py    text -> object parsers
  client.py     the rcon client
  cli.py        command line tool (entry point: squadrcon)
tests/          pytest suite
examples/       runnable usage examples
```

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Notes

Player/squad list parsing and broadcast-line parsing are regex based,
matched against Squad's current RCON text output format. If your
server version formats things differently, `parsers.py` is the place
to adjust — please open an issue with a raw sample line and it'll get
fixed.

## License

MIT — see [LICENSE](LICENSE).
