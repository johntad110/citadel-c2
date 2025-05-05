import pytest
from unittest.mock import patch, MagicMock
from citadel.agent.phantom import PhantomAgent


@pytest.fixture
def mock_agent():
    agent = PhantomAgent(c2_host='localhost')
    yield agent
    agent.running = False
    if agent.connection:
        try:
            agent.connection.close()
        except Exception:
            pass


def test_system_intel_gathering(mock_agent):
    intel = mock_agent._gather_intel()
    assert 'hostname' in intel
    assert 'os' in intel


@patch('subprocess.run')
def test_command_execution(mock_run, mock_agent):
    mock_process = MagicMock()
    mock_process.stdout = "test output\n"
    mock_process.stderr = ""
    mock_run.return_value = mock_process
    mock_agent.connection = MagicMock()
    mock_agent._execute_command("ls")
    mock_run.assert_called_with(
        "ls", shell=True, capture_output=True, text=True, timeout=30)
    mock_agent.connection.send.assert_called_once()
