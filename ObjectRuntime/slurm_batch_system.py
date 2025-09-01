import base64
import subprocess
import socket
import struct
import json
import os
from .wp_object import WPObject
from .slurm_partition import WPSlurmPartition

class WPSlurmBatchSystem(WPObject):
    """
    Minimal representation of a Slurm batch system object.

    Properties:
        - icon: base64-encoded PNG image data (str)
        - title: human-readable title (str)

    Methods:
        - getTitle(): return the title for display in the viewer
    """

    # Create a constructor that takes the title as an argument
    def __init__(self, title: str, path: str, host: str) -> None:
        super().__init__(title, path, host=host)
        resource_path = os.path.join(os.path.dirname(__file__), "Resources", "Slurm.png")
        with open(resource_path, "rb") as f:
            icon = base64.b64encode(f.read()).decode("utf-8")
            self.setIcon(icon)
        
        self.children = self._getPartitions()
        
    
    # setPort and setHost inherited from WPObject
    

    # create a function that uses the slurm binaries to list all partitions
    # ssh into "hostname" first using the current user
    def _getPartitions(self) -> list[WPSlurmPartition]:
        # make it skip the header
        with subprocess.Popen(["ssh", self.host, "sinfo -O partition -h"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to get partitions: {stderr.decode('utf-8')}")
            for partition in stdout.decode('utf-8').splitlines():
                # remove the ending "*" that marks the default partition
                partition = partition.strip().rstrip("*").strip()
                self.children.append(WPSlurmPartition(partition, f"{self.path}/{partition}", self.host, self.port))
            # strip the partitions and remove ending "*" that marks the default partition
            return self.children
    
    def _recv_all(self, connection: socket.socket, num_bytes: int) -> bytes:
        data = bytearray()
        while len(data) < num_bytes:
            chunk = connection.recv(num_bytes - len(data))
            if not chunk:
                raise ConnectionError("Connection closed while receiving data")
            data.extend(chunk)
        return bytes(data)

    def _read_message(self, connection: socket.socket) -> bytes:
        header = self._recv_all(connection, 4)
        (length,) = struct.unpack("!I", header)
        if length > 128 * 1024 * 1024:
            raise ValueError("Message too large")
        return self._recv_all(connection, length)

    def _write_message(self, connection: socket.socket, payload: bytes) -> None:
        connection.sendall(struct.pack("!I", len(payload)) + payload)

    def _fetch_object(self, object_path: str):
        try:
            import dill as pickle  # type: ignore
        except Exception:
            import pickle  # type: ignore
        with socket.create_connection((self.host, self.port), timeout=10) as sock:
            request = {"action": "GetObject", "path": object_path}
            self._write_message(sock, json.dumps(request).encode("utf-8"))
            payload = self._read_message(sock)
            return pickle.loads(payload)

    