from squadrcon.emitter import EventEmitter


def test_on_and_emit():
    received = []
    e = EventEmitter()
    e.on("test", lambda data: received.append(data))
    e.emit("test", "hello")
    assert received == ["hello"]


def test_multiple_listeners():
    calls = []
    e = EventEmitter()
    e.on("test", lambda d: calls.append("a"))
    e.on("test", lambda d: calls.append("b"))
    e.emit("test")
    assert calls == ["a", "b"]


def test_off_removes_listener():
    calls = []
    e = EventEmitter()

    def handler(data):
        calls.append(data)

    e.on("test", handler)
    e.off("test", handler)
    e.emit("test", "x")
    assert calls == []


def test_emit_unknown_event_does_nothing():
    e = EventEmitter()
    e.emit("nothing_registered")
