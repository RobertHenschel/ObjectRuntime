import base64
import subprocess


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

    # Create a constructor that takes the title as an argument
    def __init__(self, title: str, host: str) -> None:
        import os
        resource_path = os.path.join(os.path.dirname(__file__), "Resources", "Slurm.png")
        with open(resource_path, "rb") as f:
            self.icon = base64.b64encode(f.read()).decode("utf-8")
        self.title = title
        self.host = host
        self.partitions = self._getPartitions()

    def getTitle(self) -> str:
        return self.title

    def getPartitions(self) -> list[str]:
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
            return stdout.decode('utf-8').splitlines()
    
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
        partitions_list.addItems(self.getPartitions())

        layout.addWidget(host_label)
        layout.addWidget(partitions_list)

        window.setCentralWidget(central)
        window.resize(460, 340)
        window.show()

        if owns_app:
            app.exec_()


