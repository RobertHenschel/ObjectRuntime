import base64
import subprocess
import socket
import struct
import json
from .wp_object import WPObject

class WPSlurmBatchSystem(WPObject):
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
    partitions: list[str]

    # Create a constructor that takes the title as an argument
    def __init__(self, title: str, path: str, host: str) -> None:
        super().__init__(title, host=host)
        import os
        resource_path = os.path.join(os.path.dirname(__file__), "Resources", "Slurm.png")
        with open(resource_path, "rb") as f:
            self.icon = base64.b64encode(f.read()).decode("utf-8")
        self.partitions = self._getPartitions()
        self.path = path
        self.children = []
    def getTitle(self) -> str:
        return self.title

    def getPartitionNames(self) -> list[str]:
        return self.partitions
    
    # setPort and setHost inherited from WPObject
    

    # create a function that uses the slurm binaries to list all partitions
    # ssh into "hostname" first using the current user
    def _getPartitions(self) -> list[str]:
        # make it skip the header
        with subprocess.Popen(["ssh", self.host, "sinfo -O partition -h"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to get partitions: {stderr.decode('utf-8')}")
            # strip the partitions and remove ending "*" that marks the default partition
            return [line.strip().rstrip("*").strip() for line in stdout.decode('utf-8').splitlines() if line.strip()]
    
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
        from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QFont
        from PyQt5.QtCore import Qt, QRect

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
        for part in self.getPartitionNames():
            child_path = f"{self.path}/{part}"
            try:
                child = self._fetch_object(child_path)
                self.children.append((part, child))
            except Exception as e:
                # If fetch fails, still show placeholder
                print(f"Failed to fetch object for {child_path}: {e}")
                self.children.append((part, None))

        # Populate grid
        col_count = 4
        row = 0
        col = 0
        
        class _Clickable(QtWidgets.QWidget):
            def __init__(self, callback):
                super().__init__()
                self._callback = callback
            def mouseDoubleClickEvent(self, event):
                try:
                    if callable(self._callback):
                        self._callback()
                finally:
                    try:
                        super().mouseDoubleClickEvent(event)
                    except Exception:
                        pass

        for part, child in self.children:
            # Determine child path for launching viewer
            child_path = getattr(child, "path", f"{self.path}/{part}")

            def _launch_viewer(p=child_path):
                try:
                    import sys as _sys
                    import subprocess as _sp
                    _sp.Popen([
                        _sys.executable,
                        "-m", "ObjectViewer.viewer",
                        "--obj", p,
                        "--host", str(self.host),
                        "--port", str(self.port),
                    ], stdout=_sp.DEVNULL, stderr=_sp.DEVNULL, stdin=_sp.DEVNULL, close_fds=True)
                except Exception as e:
                    print(f"Failed to launch viewer: {e}")
                    pass

            cell = _Clickable(_launch_viewer)
            try:
                cell.setCursor(Qt.PointingHandCursor)
            except Exception:
                pass
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
                    scaled = pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    # Draw badge with number of jobs if > 0
                    jobs = 0
                    try:
                        jobs = child.getNumJobs()
                    except Exception:
                        jobs = 0
                    if jobs > 0:
                        # Paint badge on a copy of the pixmap
                        composed = QPixmap(scaled)
                        painter = QPainter(composed)
                        try:
                            painter.setRenderHint(QPainter.Antialiasing, True)
                            badge_d = 22
                            x = composed.width() - badge_d - 2
                            y = composed.height() - badge_d - 2
                            # Draw red circle
                            painter.setBrush(QBrush(QColor(220, 0, 0)))
                            painter.setPen(Qt.NoPen)
                            painter.drawEllipse(x, y, badge_d, badge_d)
                            # Draw white text
                            painter.setPen(QColor(255, 255, 255))
                            font = painter.font()
                            font.setBold(True)
                            font.setPointSize(max(7, int(badge_d * 0.45)))
                            painter.setFont(font)
                            painter.drawText(QRect(x, y, badge_d, badge_d), Qt.AlignCenter, str(jobs))
                        finally:
                            painter.end()
                        icon_label.setPixmap(composed)
                    else:
                        icon_label.setPixmap(scaled)
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