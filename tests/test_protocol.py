import pytest
from citadel.protocol import C2Protocol


def test_message_building():
    header = "COMMAND"
    data = {"cmd": "whoami"}
    message = C2Protocol.build_message(header, data)
    assert message.startswith(b"COMMAND|")
    assert b"whoami" in message


@pytest.mark.parametrize("message,expected_header,expected_data", [
    (b"COMMAND|{\"data\": \"ls\"}", "COMMAND", "ls"),
    (b"KEEPALIVE|", "KEEPALIVE", {}),
    (b"INVALID|garbage", None, None)
])
def test_message_parsing(message, expected_header, expected_data):
    header, payload = C2Protocol.parse_message(message)
    assert header == expected_header
    if expected_data:
        assert payload['data'] == expected_data
