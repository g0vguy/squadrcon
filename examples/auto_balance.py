from squadrcon import Rcon, RconConfig

r = Rcon(RconConfig(host="127.0.0.1", password="changeme", port="27165"))

players = r.list_players()
team_counts = {}
for p in players.players:
    team_counts[p.team_id] = team_counts.get(p.team_id, 0) + 1

print("team counts:", team_counts)

if len(team_counts) == 2:
    teams = sorted(team_counts.items(), key=lambda kv: kv[1], reverse=True)
    bigger_team = teams[0][0]
    diff = teams[0][1] - teams[1][1]

    if diff > 2:
        movable = [p for p in players.players if p.team_id == bigger_team and not p.is_leader]
        to_move = movable[: diff // 2]
        for p in to_move:
            print(f"switching {p.name} to balance teams")
            r.switch_team(p.steam_id)

r.close()
