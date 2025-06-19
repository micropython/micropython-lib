#!/usr/bin/env python3
"""DAP protocol monitor - sits between VS Code and MicroPython debugpy."""

import socket
import threading
import json
import time
import sys
import argparse

class DAPMonitor:
    def __init__(self, listen_port=5679, target_host='127.0.0.1', target_port=5678):
        self.disconnect = False
        self.listen_port = listen_port
        self.target_host = target_host
        self.target_port = target_port
        self.client_sock = None
        self.server_sock = None

    def start(self):
        """Start the DAP monitor proxy."""
        print(f"DAP Monitor starting on port {self.listen_port}")
        print(f"Will forward to {self.target_host}:{self.target_port}")
        print("Start MicroPython debugpy server first, then connect VS Code to port 5679")

        # Create listening socket
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(('127.0.0.1', self.listen_port))
        listener.listen(1)

        print(f"Listening for VS Code connection on port {self.listen_port}...")

        try:
            # Wait for VS Code to connect
            self.client_sock, client_addr = listener.accept()
            print(f"VS Code connected from {client_addr}")

            # Connect to MicroPython debugpy server
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.connect((self.target_host, self.target_port))
            print(f"Connected to MicroPython debugpy at {self.target_host}:{self.target_port}")

            # Start forwarding threads
            threading.Thread(target=self.forward_client_to_server, daemon=True).start()
            threading.Thread(target=self.forward_server_to_client, daemon=True).start()

            print("DAP Monitor active - press Ctrl+C to stop")
            while not self.disconnect:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\nStopping DAP Monitor...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.cleanup()

    def forward_client_to_server(self):
        """Forward messages from VS Code client to MicroPython server."""
        try:
            while True:
                data = self.receive_dap_message(self.client_sock, "VS Code")
                if data is None:
                    break
                self.send_raw_data(self.server_sock, data)
        except Exception as e:
            print(f"Client->Server forwarding error: {e}")

    def forward_server_to_client(self):
        """Forward messages from MicroPython server to VS Code client."""
        try:
            while True:
                data = self.receive_dap_message(self.server_sock, "MicroPython")
                if data is None:
                    break
                self.send_raw_data(self.client_sock, data)
        except Exception as e:
            print(f"Server->Client forwarding error: {e}")

    def receive_dap_message(self, sock, source):
        """Receive and log a DAP message."""
        try:
            # Read headers
            header = b""
            while b"\r\n\r\n" not in header:
                byte = sock.recv(1)
                if not byte:
                    return None
                header += byte

            # Parse content length
            header_str = header.decode('utf-8')
            content_length = 0
            for line in header_str.split('\r\n'):
                if line.startswith('Content-Length:'):
                    content_length = int(line.split(':', 1)[1].strip())
                    break

            if content_length == 0:
                return None

            # Read content
            content = b""
            while len(content) < content_length:
                chunk = sock.recv(content_length - len(content))
                if not chunk:
                    return None
                content += chunk

            # Parse and Log the message
            message = self.parse_dap(source, content)
            self.log_dap_message(source, message)
            # Check for disconnect command
            if message:
                if "disconnect" == message.get('command', message.get('event', 'unknown')):
                    print(f"\n[{source}] Disconnect command received, stopping monitor.")
                    self.disconnect = True
            return header + content
        except Exception as e:
            print(f"Error receiving from {source}: {e}")
            return None

    def parse_dap(self, source, content):
        """Parse DAP message and log it."""
        try:
            message = json.loads(content.decode('utf-8'))
            return message
        except json.JSONDecodeError:
            print(f"\n[{source}] Invalid JSON: {content}")
            return None

    def log_dap_message(self, source, message):
        """Log DAP message details."""
        msg_type = message.get('type', 'unknown')
        command = message.get('command', message.get('event', 'unknown'))
        seq = message.get('seq', 0)

        print(f"\n[{source}] {msg_type.upper()}: {command} (seq={seq})")

        if msg_type == 'request':
            args = message.get('arguments', {})
            if args:
                print(f"  Arguments: {json.dumps(args, indent=2)}")
        elif msg_type == 'response':
            success = message.get('success', False)
            req_seq = message.get('request_seq', 0)
            print(f"  Success: {success}, Request Seq: {req_seq}")
            body = message.get('body')
            if body:
                print(f"  Body: {json.dumps(body, indent=2)}")
            msg = message.get('message')
            if msg:
                print(f"  Message: {msg}")
        elif msg_type == 'event':
            body = message.get('body', {})
            if body:
                print(f"  Body: {json.dumps(body, indent=2)}")

    def send_raw_data(self, sock, data):
        """Send raw data to socket."""
        try:
            sock.send(data)
        except Exception as e:
            print(f"Error sending data: {e}")

    def cleanup(self):
        """Clean up sockets."""
        if self.client_sock:
            self.client_sock.close()
        if self.server_sock:
            self.server_sock.close()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="DAP protocol monitor proxy")
    parser.add_argument("--target-host", "--th", default="127.0.0.1", help="Target debugpy host (default: 127.0.0.1)")
    parser.add_argument("--target-port", "--tp", type=int, default=5678, help="Target debugpy port (default: 5678)")
    parser.add_argument("--listen-port", "--lp", type=int, default=5679, help="Port to listen for VS Code (default: 5679)")
    args = parser.parse_args()

    monitor = DAPMonitor(
        listen_port=args.listen_port,
        target_host=args.target_host,
        target_port=args.target_port
    )
    monitor.start()
