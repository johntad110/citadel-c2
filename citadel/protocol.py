"""
C2 Communication Protocol Specification

Message Format:
[HEADER]|[JSON DATA]

Standard Headers:
- SYSTEM_INFO: Initial check-in data
- COMMAND: Execute system command
- SHELL: Start reverse shell
- FILE: File transfer operation
- SELF_DESTRUCT: Terminate agent
- KEEPALIVE: Connection health check

Author: johntad
Version: 0.0.0
"""

import json


class C2Protocol:
    """
    Defines the communication protocol between the Citadel and it's phantoms.
    """
    HEADER_SEP = "|"
    ENCODING = "utf-8"

    @staticmethod
    def build_message(header, data=None):
        """
        Construct a protocol-complient message.

        Args:
            header (str): The header indicating the type of messages.
            data (dict, optional): A dictionary containing the message payload. Defaults to None.

        Returns:
            bytes: The encoded protocol message.
        """
        payload = {"data": data} if data else {}
        return f"{header}{C2Protocol.HEADER_SEP}{json.dumps(payload)}".encode(C2Protocol.ENCODING)

    @staticmethod
    def parse_message(message):
        """
        Deconstruct protocol message

        Args: 
            message (bytes): The raw protocol message received.

        Returns:
            tuple[str | None, dict | None]: A tuple containing the header and the parsed JSON payload.
                                            Returns (None, None) if parsing fails. 
        """
        try:
            if not message:
                return None, None

            decoded = message.decode(C2Protocol.ENCODING)
            if C2Protocol.HEADER_SEP not in decoded:
                return None, None

            header, payload = decoded.split(C2Protocol.HEADER_SEP, 1)
            return header, json.loads(payload) if payload else {}
        except (ValueError, json.JSONDecodeError):
            return None, None
