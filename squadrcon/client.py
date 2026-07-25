import itertools
import queue
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
        self.send_lock = threading.Lock()
        self.closed = True
        self.reader_thread = None
        self._pending = {}
        self._pending_lock = threading.Lock()
        self._connect()

    def _connect(self):
        sock = socket.create_connection((self.config.host, int(self.config.port)), timeout=self.config.timeout)
        sock.settimeout(self.config.timeout)
        self.sock = sock
        self.buffer = b""

        auth_id = next(_ids)
        sock.sendall(protocol.encode_packet(auth_id, protocol.AUTH, self.config.password))

        pkt = self._read_packet_direct()
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

    def _read_packet_direct(self):
        """Used only during the initial auth handshake, before the
        reader thread exists, so there's no other reader to race with."""
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
        """The only thread that ever reads the socket after auth.
        Command responses get routed to the waiting queue in
        _pending; anything else is an unsolicited broadcast line
        (chat, kicks, bans, warns) and gets parsed and emitted."""
        while not self.closed:
            try:
                pkt, self.buffer = protocol.try_decode_packet(self.buffer)
                if pkt is None:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        if self.closed:
                            break
                        raise ConnectionError("socket closed by remote")
                    self.buffer += chunk
                    continue
            except (socket.timeout, OSError) as exc:
                if self.closed:
                    break
                self.emitter.emit(events.ERROR, exc)
                if self.config.auto_reconnect:
                    self._reconnect()
                    continue
                break
            except Exception as exc:
                self.emitter.emit(events.ERROR, exc)
                break

            with self._pending_lock:
                q = self._pending.get(pkt.id)

            if q is not None:
                q.put(pkt)
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

    def execute(self, command, timeout=None):
        if self.sock is None or self.closed:
            raise RconAuthError("not connected")

        timeout = timeout or self.config.timeout
        req_id = next(_ids)
        marker_id = next(_ids)

        q = queue.Queue()
        marker_q = queue.Queue()
        with self._pending_lock:
            self._pending[req_id] = q
            self._pending[marker_id] = marker_q

        try:
            with self.send_lock:
                self.sock.sendall(protocol.encode_packet(req_id, protocol.EXEC, command))
                self.sock.sendall(protocol.encode_packet(marker_id, protocol.EXEC, ""))

            chunks = []
            deadline = time.monotonic() + timeout
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    pkt = q.get(timeout=min(remaining, 0.1))
                    chunks.append(pkt.body)
                    continue
                except queue.Empty:
                    pass
                try:
                    marker_q.get_nowait()
                    break
                except queue.Empty:
                    continue

            raw = "".join(chunks)
        finally:
            with self._pending_lock:
                self._pending.pop(req_id, None)
                self._pending.pop(marker_id, None)

        self._dispatch(command, raw)
        return raw

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
