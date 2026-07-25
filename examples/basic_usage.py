from squadrcon import Rcon, RconConfig

r = Rcon(RconConfig(host="127.0.0.1", password="changeme", port="27165"))

players = r.list_players()
for p in players.players:
    print(p.player_id, p.name, p.steam_id, p.team_id, p.squad_id)

r.close()
