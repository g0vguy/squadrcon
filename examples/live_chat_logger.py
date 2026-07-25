from squadrcon import Rcon, RconConfig, events

r = Rcon(RconConfig(host="127.0.0.1", password="changeme", port="27165"))

r.emitter.on(events.CHAT_MESSAGE, lambda msg: print(f"[{msg.chat_type}] {msg.player_name}: {msg.message}"))
r.emitter.on(events.PLAYER_KICKED, lambda k: print(f"kicked: {k.player_name}"))
r.emitter.on(events.PLAYER_BANNED, lambda b: print(f"banned: {b.player_name} ({b.duration})"))

print("listening for events, ctrl+c to stop")
try:
    while True:
        pass
except KeyboardInterrupt:
    r.close()
