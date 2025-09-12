import base64
import subprocess
import os
from .wp_object import WPObject


class WPSlurmJob(WPObject):
    """
    Minimal representation of a Slurm job object.
    """
    state: str # Pending or Running
    slurm_host: str

    def __init__(self, title: str, path: str) -> None:
        super().__init__(title, path)
        # get number of jobs in the partition
        self.children = []
        self.state = "Pending"
        self.slurm_host = None
    
    def setSlurmHost(self, slurm_host: str) -> None:
        self.slurm_host = slurm_host

    def getBadge(self) -> str:
        return self.state
    
    def getDetails(self) -> None:
        # get the details of the job
        with subprocess.Popen(["ssh", self.slurm_host, "scontrol", "show", "job", self.title], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to get job details: {stderr.decode('utf-8')}")
            self.details = stdout.decode('utf-8')
        self.state = self.details.split("State=")[1].split("\n")[0]

    
    def wp_open(self, view: str = None) -> None:
        from PyQt5 import QtWidgets
        from PyQt5.QtGui import QIcon, QPixmap
        from PyQt5.QtCore import Qt
        from .notebook import NotebookWidget
        
        app = QtWidgets.QApplication.instance()
        owns_app = False
        if app is None:
            app = QtWidgets.QApplication([])
            owns_app = True

        window = QtWidgets.QMainWindow()
        window.setWindowTitle(f"Job {self.title} - {self.state}")
        window.resize(800, 600)

        # Set window icon
        try:
            icon_bytes = base64.b64decode(self.icon)
            pixmap = QPixmap()
            if pixmap.loadFromData(icon_bytes, "PNG"):
                icon = QIcon(pixmap)
                window.setWindowIcon(icon)
                app.setWindowIcon(icon)
        except Exception as e:
            print(f"Failed to set window icon: {e}")

        # Create tab content widgets
        general_tab = QtWidgets.QWidget()
        general_layout = QtWidgets.QVBoxLayout(general_tab)
        
        # General tab content
        job_info = QtWidgets.QLabel(f"""
        <h2>Job Information</h2>
        <p><b>Job ID:</b> {self.title}</p>
        <p><b>State:</b> {self.state}</p>
        """)
        job_info.setAlignment(Qt.AlignTop)
        job_info.setWordWrap(True)
        general_layout.addWidget(job_info)
        
        # Output tab content
        output_tab = QtWidgets.QWidget()
        output_layout = QtWidgets.QVBoxLayout(output_tab)
        
        output_text = QtWidgets.QTextEdit()
        output_text.setPlainText(f"""Job Output for {self.title}
        ...
        """)
        output_text.setReadOnly(True)
        output_layout.addWidget(output_text)

        # Errors tab content
        errors_tab = QtWidgets.QWidget()
        errors_layout = QtWidgets.QVBoxLayout(errors_tab)
        
        errors_info = QtWidgets.QLabel(f"""
        <h2>Error Stream</h2>
        <p><b>...</b></p>
        """)
        errors_info.setAlignment(Qt.AlignTop)
        errors_info.setWordWrap(True)
        errors_layout.addWidget(errors_info)

        # Create notebook with the three tabs
        tabs = [
            ("General", general_tab),
            ("Output", output_tab),
            ("Errors", errors_tab)
        ]
        
        notebook = NotebookWidget(parent=None, tabs=tabs)
        window.setCentralWidget(notebook)
        window.show()

        if owns_app:
            app.exec_()