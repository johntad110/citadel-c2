import pytest
from unittest.mock import Mock, patch
from citadel.server.citadel import CitadelServer
from citadel.protocol import C2Protocol


@pytest.fixture
def mock_server():
    server = CitadelServer(host='localhost', c2_port=0, shell_port=0)
    server._is_testing = True
    yield server
    if hasattr(server, 'running'):
        server.running = False
    if hasattr(server, 'c2_socket'):
        server.c2_socket.close()


def test_server_initialization(mock_server):
    assert mock_server.host == 'localhost'
    assert len(mock_server.active_agents) == 0


@patch('socket.socket')
def test_agent_registration(mock_socket, mock_server):
    mock_server.c2_socket = Mock()
    mock_conn = Mock()
    mock_conn.recv.return_value = C2Protocol.build_message(
        "SYSTEM_INFO", {"hostname": "test-pc"}
    )

    mock_server._register_agent(mock_conn)
    assert len(mock_server.active_agents) == 1
    assert mock_server.active_agents[1][1]['hostname'] == "test-pc"
