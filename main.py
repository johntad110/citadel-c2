#!/usr/bin/env python3
"""
Citadel C2 Server - Main Entry Point

Usage:
  python main.py [--host <ip>] [--port <port>] [--shell-port <port>]
"""

import argparse
from citadel.server import CitadelServer

import colorama
colorama.init()


def parse_args():
    parser = argparse.ArgumentParser(description='Citadel C2 Server')
    parser.add_argument('--host', default='0.0.0.0',
                        help='Server host address')
    parser.add_argument('--port', type=int, default=8886,
                        help='C2 command port')
    parser.add_argument('--shell-port', type=int, default=8887,
                        help='Reverse shell port')
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        server = CitadelServer(
            host=args.host,
            c2_port=args.port,
            shell_port=args.shell_port
        )
        print(f"""
        ██████╗██╗████████╗ █████╗ ██████╗ ███████╗██╗
        ██╔════╝██║╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║
        ██║     ██║   ██║   ███████║██║  ██║█████╗  ██║
        ██║     ██║   ██║   ██╔══██║██║  ██║██╔══╝  ╚═╝
        ╚██████╗██║   ██║   ██║  ██║██████╔╝███████╗██╗
         ╚═════╝╚═╝   ╚═╝   ╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝
        
        Starting Your Citadel...
        Listening on {args.host}:{args.port}
        Shell Port: {args.shell_port}
        """)
        server.start()
    except KeyboardInterrupt:
        print("\n[!] Server shutdown requested")
    except Exception as e:
        print(f"[!] Fatal error: {str(e)}")
    finally:
        if 'server' in locals():
            server.shutdown()


if __name__ == "__main__":
    main()
