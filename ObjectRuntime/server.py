import argparse
import socket
import struct
import threading
import json
from typing import Tuple

try:
    import dill as pickle  # more flexible than pickle for arbitrary objects
except Exception:  # pragma: no cover - fallback
    import pickle  # type: ignore

from .slurm_batch_system import WPSlurmBatchSystem
from .slurm_partition import WPSlurmPartition


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


def handle_client(connection: socket.socket, address: Tuple[str, int]) -> None:
    try:
        raw = read_message(connection)
        try:
            message = json.loads(raw.decode("utf-8"))
        except Exception:
            raise ValueError("Invalid JSON request")

        action = message.get("action")
        
        if action != "GetObject":
            raise ValueError("Unsupported action")

        if action == "GetObject":
            object_path = message.get("path")
            print(f"Received message: {action} {object_path}")
            if object_path == "/Slurm/Quartz":
                obj = WPSlurmBatchSystem("Quartz Batch System", "/Slurm/Quartz", "quartz.uits.iu.edu")
                obj.getPartitions()
            elif object_path.startswith("/Slurm/Quartz/"):
                partition_name = object_path.rsplit("/", 1)[-1]
                obj = WPSlurmPartition(partition_name, object_path, "quartz.uits.iu.edu")
                obj.getJobs()
            else:
                raise KeyError(f"Unknown object path: {object_path}")
            payload = pickle.dumps(obj)
            write_message(connection, payload)
    except Exception as exc:
        # send a structured error back to the client
        try:
            error_payload = pickle.dumps({"error": str(exc)})
            write_message(connection, error_payload)
        except Exception:
            pass
    finally:
        try:
            connection.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        connection.close()


def serve(port: int, host: str = "0.0.0.0") -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((host, port))
        server_sock.listen(5)
        print(f"ObjectRuntime listening on {host}:{port}")
        while True:
            conn, addr = server_sock.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()


def main() -> None:
    parser = argparse.ArgumentParser(description="Object Runtime Server")
    parser.add_argument("--port", type=int, default=9100, help="TCP port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host/IP to bind to")
    args = parser.parse_args()
    serve(args.port, args.host)


if __name__ == "__main__":
    main()



