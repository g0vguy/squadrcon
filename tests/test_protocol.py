from squadrcon import protocol


def test_packet_round_trip():
    raw = protocol.encode_packet(5, protocol.EXEC, "ListPlayers")
    pkt, rest = protocol.try_decode_packet(raw)
    assert pkt.id == 5
    assert pkt.type == protocol.EXEC
    assert pkt.body == "ListPlayers"
    assert rest == b""


def test_incomplete_buffer_returns_none():
    raw = protocol.encode_packet(1, protocol.EXEC, "ping")
    partial = raw[:5]
    pkt, rest = protocol.try_decode_packet(partial)
    assert pkt is None
    assert rest == partial


def test_multiple_packets_in_buffer():
    a = protocol.encode_packet(1, protocol.EXEC, "one")
    b = protocol.encode_packet(2, protocol.EXEC, "two")
    buf = a + b

    pkt1, buf = protocol.try_decode_packet(buf)
    pkt2, buf = protocol.try_decode_packet(buf)

    assert pkt1.body == "one"
    assert pkt2.body == "two"
    assert buf == b""


def test_empty_body():
    raw = protocol.encode_packet(9, protocol.EXEC, "")
    pkt, rest = protocol.try_decode_packet(raw)
    assert pkt.body == ""
    assert rest == b""
