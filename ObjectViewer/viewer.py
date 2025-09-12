import argparse
import sys
import os
import socket
import json
import struct
from typing import Any

try:
    import dill as pickle
except Exception:  # pragma: no cover
    import pickle  # type: ignore


def recv_all(connection: socket.socket, num_bytes: int) -> bytes:
    data = bytearray()
    while len(data) < num_bytes:
        chunk = connection.recv(num_bytes - len(data))
        if not chunk:
            raise ConnectionError("Connection closed while receiving data")
        data.extend(chunk)
    return bytes(data)


def read_message(connection: socket.socket) -> bytes:
    header = recv_all(connection, 4)
    (length,) = struct.unpack("!I", header)
    if length > 128 * 1024 * 1024:
        raise ValueError("Message too large")
    return recv_all(connection, length)


def write_message(connection: socket.socket, payload: bytes) -> None:
    connection.sendall(struct.pack("!I", len(payload)) + payload)


def spawn_detached(func) -> None:
    """Run func() in a fully detached child using double-fork + setsid."""
    pid = os.fork()
    if pid > 0:
        # Parent returns immediately
        return
    os.setsid()
    pid2 = os.fork()
    if pid2 > 0:
        os._exit(0)
    # Grandchild: run target, then exit
    try:
        func()
    finally:
        os._exit(0)

def fetch_object(host: str, port: int, object_path: str) -> Any:
    with socket.create_connection((host, port), timeout=10) as sock:
        request = {"action": "GetObject", "path": object_path}
        write_message(sock, json.dumps(request).encode("utf-8"))
        payload = read_message(sock)
        obj = pickle.loads(payload)
        return obj


def main() -> None:
    parser = argparse.ArgumentParser(description="Object Viewer")
    parser.add_argument("--object", dest="object_path", required=True, help="Path of object to fetch")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=9100, help="Server port")
    parser.add_argument("--view", default=None, help="View to open (icon(Default), settings)")
    args = parser.parse_args()

    obj = fetch_object(args.host, args.port, args.object_path)
    # If the server returned an error dict
    if isinstance(obj, dict) and "error" in obj:
        raise RuntimeError(f"Server error: {obj['error']}")
    obj.setHost(args.host)
    obj.setPort(args.port)
    if hasattr(obj, "getTitle"):
        title = getattr(obj, "getTitle")()
        print(title)
    if hasattr(obj, "wp_open"):
        def _launch():
            getattr(obj, "wp_open")(args.view)
        spawn_detached(_launch)
    print("Done")
    # end the application
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
    sys.exit(0)

if __name__ == "__main__":
    main()


