import base64
import subprocess
import socket
import struct
import json

class WPSlurmPartition:
    """
    Minimal representation of a Slurm partition object.
    """
    title: str
    icon: str
    path: str

    def __init__(self, title: str, path: str) -> None:
        import os
        self.title = title
        self.path = path
        # Use same Slurm icon by default
        resource_path = os.path.join(os.path.dirname(__file__), "Resources", "Partition.png")
        with open(resource_path, "rb") as f:
            self.icon = base64.b64encode(f.read()).decode("utf-8")

    def getTitle(self) -> str:
        return self.title

    def getIcon(self) -> str:
        return self.icon

class WPSlurmBatchSystem:
    """
    Minimal representation of a Slurm batch system object.

    Properties:
        - icon: base64-encoded PNG image data (str)
        - title: human-readable title (str)

    Methods:
        - getTitle(): return the title for display in the viewer
    """
    host: str
    port: int
    icon: str
    partition: str
    partitions: list[str]
    children: []

    # Create a constructor that takes the title as an argument
    def __init__(self, title: str, path: str, host: str) -> None:
        import os
        resource_path = os.path.join(os.path.dirname(__file__), "Resources", "Slurm.png")
        with open(resource_path, "rb") as f:
            self.icon = base64.b64encode(f.read()).decode("utf-8")
        self.title = title
        self.host = host
        self.partitions = self._getPartitions()
        self.path = path
    def getTitle(self) -> str:
        return self.title

    def getPartitionNames(self) -> list[str]:
        return self.partitions
    
    def setPort(self, port: int) -> None:
        self.port = port
    
    def setHost(self, host: str) -> None:
        self.host = host
    

    # create a function that uses the slurm binaries to list all partitions
    # ssh into "hostname" first using the current user
    def _getPartitions(self) -> list[str]:
        # make it skip the header
        with subprocess.Popen(["ssh", self.host, "sinfo -O partition -h"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to get partitions: {stderr.decode('utf-8')}")
            # strip the partitions and remove ending "*" that marks the default partition
            return [line.strip() for line in stdout.decode('utf-8').splitlines() if line.strip() and not line.strip().endswith("*")]
    
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

    def wp_open_icon_view(self) -> None:
        from PyQt5 import QtWidgets
        from PyQt5.QtGui import QIcon, QPixmap
        from PyQt5.QtCore import Qt

        app = QtWidgets.QApplication.instance()
        owns_app = False
        if app is None:
            app = QtWidgets.QApplication([])
            owns_app = True

        window = QtWidgets.QMainWindow()
        window.setWindowTitle(self.title + " - Partitions")

        # Set app icon same as wp_open
        try:
            icon_bytes = base64.b64decode(self.icon)
            pixmap = QPixmap()
            if pixmap.loadFromData(icon_bytes, "PNG"):
                icon = QIcon(pixmap)
                window.setWindowIcon(icon)
                app.setWindowIcon(icon)
        except Exception:
            pass

        scroll = QtWidgets.QScrollArea()
        container = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(container)
        grid.setAlignment(Qt.AlignTop)

        # Fetch child objects for each partition
        children = []
        for part in self.getPartitionNames():
            child_path = f"{self.path}/{part}"
            try:
                child = self._fetch_object(child_path)
                children.append((part, child))
            except Exception:
                # If fetch fails, still show placeholder
                children.append((part, None))

        # Populate grid
        col_count = 4
        row = 0
        col = 0
        for part, child in children:
            cell = QtWidgets.QWidget()
            vbox = QtWidgets.QVBoxLayout(cell)
            vbox.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

            icon_label = QtWidgets.QLabel()
            icon_label.setFixedSize(96, 96)
            icon_label.setAlignment(Qt.AlignCenter)

            title = part
            icon_b64 = self.icon
            if child is not None:
                if hasattr(child, "getTitle"):
                    try:
                        title = child.getTitle()
                    except Exception:
                        pass
                if hasattr(child, "getIcon"):
                    try:
                        icon_b64 = child.getIcon()
                    except Exception:
                        pass

            try:
                icon_bytes = base64.b64decode(icon_b64)
                pixmap = QPixmap()
                if pixmap.loadFromData(icon_bytes, "PNG"):
                    icon_label.setPixmap(pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except Exception:
                pass

            title_label = QtWidgets.QLabel(title)
            title_label.setAlignment(Qt.AlignCenter)

            vbox.addWidget(icon_label)
            vbox.addWidget(title_label)

            grid.addWidget(cell, row, col)
            col += 1
            if col >= col_count:
                col = 0
                row += 1

        container.setLayout(grid)
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

        window.setCentralWidget(scroll)
        window.resize(640, 480)
        window.show()

        if owns_app:
            app.exec_()

    def wp_open(self) -> None:
        """Open a Qt5 window listing available partitions with a refresh button."""
        from PyQt5 import QtWidgets
        from PyQt5.QtGui import QIcon, QPixmap

        app = QtWidgets.QApplication.instance()
        owns_app = False
        if app is None:
            app = QtWidgets.QApplication([])
            owns_app = True

        window = QtWidgets.QMainWindow()
        window.setWindowTitle(self.title)

        # Set application/window icon from base64-encoded PNG bytes
        try:
            icon_bytes = base64.b64decode(self.icon)
            pixmap = QPixmap()
            if pixmap.loadFromData(icon_bytes, "PNG"):
                icon = QIcon(pixmap)
                window.setWindowIcon(icon)
                app.setWindowIcon(icon)
        except Exception:
            # If icon loading fails, continue without blocking the UI
            pass

        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)

        host_label = QtWidgets.QLabel(f"Host: {self.host}")
        partitions_list = QtWidgets.QListWidget()
        partitions_list.addItems(self.getPartitionNames())

        layout.addWidget(host_label)
        layout.addWidget(partitions_list)

        window.setCentralWidget(central)
        window.resize(460, 340)
        window.show()

        if owns_app:
            app.exec_()


