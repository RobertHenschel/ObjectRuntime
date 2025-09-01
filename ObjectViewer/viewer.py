import argparse
import threading
import socket
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


def fetch_object(host: str, port: int, object_path: str) -> Any:
    with socket.create_connection((host, port), timeout=10) as sock:
        write_message(sock, object_path.encode("utf-8"))
        payload = read_message(sock)
        obj = pickle.loads(payload)
        return obj


def main() -> None:
    parser = argparse.ArgumentParser(description="Object Viewer")
    parser.add_argument("--object", dest="object_path", required=True, help="Path of object to fetch")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=9100, help="Server port")
    args = parser.parse_args()

    obj = fetch_object(args.host, args.port, args.object_path)
    # If the server returned an error dict
    if isinstance(obj, dict) and "error" in obj:
        raise RuntimeError(f"Server error: {obj['error']}")
    # Version 1: call getTitle dynamically and print
    if hasattr(obj, "getTitle"):
        title = getattr(obj, "getTitle")()
        print(title)
    if hasattr(obj, "getPartitions"):
        partitions = getattr(obj, "getPartitions")()
        print(partitions)
    if hasattr(obj, "wp_open"):
        wp_thread = threading.Thread(target=getattr(obj, "wp_open"), daemon=True)
        wp_thread.start()
    print("Done")
    try:
        input("Press Enter to exit...")
    except EOFError:
        pass


if __name__ == "__main__":
    main()


