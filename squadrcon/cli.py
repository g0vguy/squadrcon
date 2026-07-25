import argparse
import os
import sys

from . import Rcon, RconConfig, events


def main():
    p = argparse.ArgumentParser(prog="squadrcon", description="squad rcon tool")
    p.add_argument("--host", default=os.environ.get("SQUAD_HOST", ""))
    p.add_argument("--port", default=os.environ.get("SQUAD_PORT", "27165"))
    p.add_argument("--pass", dest="password", default=os.environ.get("SQUAD_PASS", ""))
    p.add_argument("--list", action="store_true")
    p.add_argument("--kick", metavar="NAME_OR_STEAMID", default="")
    p.add_argument("--switch-team", metavar="NAME_OR_STEAMID", default="")
    p.add_argument("--reason", default="Kicked by admin")
    p.add_argument("--timeout", type=float, default=8.0)
    args = p.parse_args()

    if not args.host or not args.password:
        print("[-] missing --host or --pass")
        sys.exit(1)
    if not args.list and not args.kick and not args.switch_team:
        print("[-] specify --list, --kick <name/steamid> or --switch-team <name/steamid>")
        sys.exit(1)

    print(f"[*] connecting to {args.host}:{args.port}")
    try:
        r = Rcon(RconConfig(host=args.host, password=args.password, port=args.port, timeout=args.timeout))
    except Exception as exc:
        print(f"[-] connection failed: {exc}")
        sys.exit(1)

    print("[+] connected")
    r.emitter.on(events.ERROR, lambda data: print(f"[-] rcon error: {data}"))

    kicked = {"ok": False}
    r.emitter.on(events.PLAYER_KICKED, lambda k: (print(f"[+] kicked: {k.player_name}"), kicked.update(ok=True)))

    try:
        if args.list:
            players = r.list_players()
            if not players.players:
                print("[-] no players parsed, raw response:")
                print(players.raw)
                return
            print(f"[*] {len(players.players)} players online")
            for pl in players.players:
                print(f"    {pl.player_id:<4} {pl.steam_id:<18} {pl.name:<25} team {pl.team_id or '-':<3} squad {pl.squad_id or '-'}")
            return

        if args.switch_team:
            print(f"[*] switching {args.switch_team} to the opposite team")
            resp = r.switch_team(args.switch_team)
            if resp:
                print(f"[+] server response: {resp}")
            else:
                print("[*] command sent, no response text, check with --list")
            return

        print(f"[*] kicking {args.kick}")
        r.kick(args.kick, args.reason)
        if not kicked["ok"]:
            print("[*] command sent, no confirmation seen yet, check with --list")
    finally:
        r.close()


if __name__ == "__main__":
    main()
