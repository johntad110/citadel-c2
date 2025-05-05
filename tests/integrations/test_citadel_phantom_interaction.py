import pytest
import time
from threading import Thread
from unittest.mock import MagicMock, patch
from citadel.server.citadel import CitadelServer
from citadel.agent.phantom import PhantomAgent


@pytest.fixture
def live_server():
    server = CitadelServer(host='localhost', c2_port=8886)
    server._is_testing = True
    server_thread = Thread(target=server.start)
    server_thread.start()
    yield server
    server.running = False
    server_thread.join()


def test_full_communication(live_server):
    agent = PhantomAgent(c2_host='localhost')
    agent_thread = Thread(target=agent.connect)
    agent_thread.daemon = True
    agent_thread.start()

    time.sleep(3)

    assert len(live_server.active_agents) == 1

    agent.running = False
    agent.connection = None
    agent_thread.join(timeout=2)

    live_server.running = False
    live_server.c2_socket.close()
