from typing import Optional
import base64

class WPObject:
    title: str
    icon: str
    host: Optional[str]
    port: Optional[int]
    children: []
    path: str

    def __init__(self, title: str, path: str, host: Optional[str] = None, port: Optional[int] = None) -> None:
        self.title = title
        self.host = host
        self.port = port
        self.children = []
        self.path = path

    def getTitle(self) -> str:
        return self.title

    def setHost(self, host: str) -> None:
        self.host = host

    def setPort(self, port: int) -> None:
        self.port = port
    
    def setIcon(self, icon: str) -> None:
        self.icon = icon
    
    def getIcon(self) -> str:
        return self.icon

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
            except Exception as e:
                print(f"Failed to set window icon: {e}")
                pass

            scroll = QtWidgets.QScrollArea()
            container = QtWidgets.QWidget()
            grid = QtWidgets.QGridLayout(container)
            grid.setAlignment(Qt.AlignTop)

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

            for part in self.children:
                # Determine child path for launching viewer
                child_path = getattr(part, "path")
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
                if part is not None:
                    if hasattr(part, "getTitle"):
                        try:
                            title = part.getTitle()
                        except Exception:
                            pass
                    if hasattr(part, "getIcon"):
                        try:
                            icon_b64 = part.getIcon()
                        except Exception:
                            pass

                try:
                    icon_bytes = base64.b64decode(icon_b64)
                    pixmap = QPixmap()
                    if pixmap.loadFromData(icon_bytes, "PNG"):
                        scaled = pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        # Draw badge with number of jobs if > 0
                        if len(part.children) > 0:
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
                                painter.drawText(QRect(x, y, badge_d, badge_d), Qt.AlignCenter, str(len(part.children)))
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
