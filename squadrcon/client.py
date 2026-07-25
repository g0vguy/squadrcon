import itertools
import socket
import threading
import time
from dataclasses import dataclass

from . import events, parsers, protocol
from .emitter import EventEmitter

_ids = itertools.count(1)


@dataclass
class RconConfig:
    host: str
    password: str
    port: str = 27165
    auto_reconnect: bool = False
    auto_reconnect_delay: float = 5.0
    timeout: float = 10.0


class RconAuthError(Exception):
    pass


class Rcon:
    def __init__(self, config: RconConfig):
        self.config = config
        self.emitter = EventEmitter()
        self.sock = None
        self.buffer = b""
        self.lock = threading.Lock()
        self.closed = True
        self.reader_thread = None
        self._connect()

    def _connect(self):
        sock = socket.create_connection((self.config.host, int(self.config.port)), timeout=self.config.timeout)
        sock.settimeout(self.config.timeout)
        self.sock = sock
        self.buffer = b""

        auth_id = next(_ids)
        sock.sendall(protocol.encode_packet(auth_id, protocol.AUTH, self.config.password))

        pkt = self._read_packet()
        if pkt is None or pkt.id == -1:
            self.close()
            raise RconAuthError("auth failed, check rcon password")

        self.closed = False
        self.emitter.emit(events.CONNECTED)

        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()

    def close(self):
        self.closed = True
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
        self.emitter.emit(events.CLOSE)

    def _read_packet(self):
        while True:
            pkt, self.buffer = protocol.try_decode_packet(self.buffer)
            if pkt is not None:
                return pkt
            try:
                chunk = self.sock.recv(4096)
            except (socket.timeout, OSError):
                return None
            if not chunk:
                return None
            self.buffer += chunk

    def _reader_loop(self):
        while not self.closed:
            try:
                pkt = self._read_packet()
            except Exception as exc:
                self.emitter.emit(events.ERROR, exc)
                if self.config.auto_reconnect:
                    self._reconnect()
                    continue
                break

            if pkt is None:
                if self.closed:
                    break
                continue

            if pkt.body:
                self.emitter.emit(events.DATA, pkt.body)
                for line in pkt.body.splitlines():
                    result = parsers.parse_broadcast_line(line)
                    if result:
                        name, obj = result
                        self.emitter.emit(name, obj)

    def _reconnect(self):
        self.emitter.emit(events.RECONNECTING)
        time.sleep(self.config.auto_reconnect_delay)
        try:
            self._connect()
        except Exception as exc:
            self.emitter.emit(events.ERROR, exc)

    def execute(self, command):
        if self.sock is None or self.closed:
            raise RconAuthError("not connected")

        req_id = next(_ids)
        with self.lock:
            self.sock.sendall(protocol.encode_packet(req_id, protocol.EXEC, command))
            raw = self._collect(req_id)

        self._dispatch(command, raw)
        return raw

    def _collect(self, req_id):
        marker_id = next(_ids)
        self.sock.sendall(protocol.encode_packet(marker_id, protocol.EXEC, ""))

        chunks = []
        while True:
            pkt = self._read_packet()
            if pkt is None or pkt.id == marker_id:
                break
            if pkt.id == req_id:
                chunks.append(pkt.body)
        return "".join(chunks)

    def _dispatch(self, command, raw):
        name = command.strip().split(" ", 1)[0]

        if name == events.LIST_PLAYERS:
            self.emitter.emit(events.LIST_PLAYERS, parsers.parse_players(raw))
        elif name == events.LIST_SQUADS:
            self.emitter.emit(events.LIST_SQUADS, parsers.parse_squads(raw))
        elif name == events.SHOW_CURRENT_MAP:
            parsed = parsers.parse_current_map(raw)
            if parsed:
                self.emitter.emit(events.SHOW_CURRENT_MAP, parsed)
        elif name == events.SHOW_NEXT_MAP:
            parsed = parsers.parse_next_map(raw)
            if parsed:
                self.emitter.emit(events.SHOW_NEXT_MAP, parsed)

    def switch_team(self, target):
        return self.execute(f"AdminForceTeamChange {target}")

    def kick(self, target, reason=""):
        return self.execute(f"AdminKick {target} {reason}".rstrip())

    def ban(self, target, duration, reason=""):
        return self.execute(f"AdminBan {target} {duration} {reason}".rstrip())

    def warn(self, target, message):
        return self.execute(f'AdminWarn {target} "{message}"')

    def list_players(self):
        return parsers.parse_players(self.execute(events.LIST_PLAYERS))

    def list_squads(self):
        return parsers.parse_squads(self.execute(events.LIST_SQUADS))
