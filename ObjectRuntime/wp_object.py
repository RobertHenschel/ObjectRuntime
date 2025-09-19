from typing import Optional, List
import base64
import os

class WPObject:
    title: str
    icon: str
    host: Optional[str]
    port: Optional[int]
    children: List["WPObject"]
    children_count: int
    path: str

    def __init__(self, title: str, path: str) -> None:
        self.title = title
        self.children = []
        self.path = path
        self.children_count = 0
        self.host = None
        self.port = None
        icon = self.__class__.__name__ + ".png"
        resource_path = os.path.join(os.path.dirname(__file__), "Resources", icon)
        with open(resource_path, "rb") as f:
            self.icon = base64.b64encode(f.read()).decode("utf-8")

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

    def wp_open(self, view: str = None) -> None:
            from PyQt5 import QtWidgets
            from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QFont, QFontMetrics
            from PyQt5.QtCore import Qt, QRect

            app = QtWidgets.QApplication.instance()
            owns_app = False
            if app is None:
                app = QtWidgets.QApplication([])
                owns_app = True

            window = QtWidgets.QMainWindow()
            window.setWindowTitle(self.title)

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
            
            # Styles for selection visuals
            SELECTED_CELL_STYLE = (
                "QFrame#cell { border: 2px solid #2D7CFF; border-radius: 8px; "
                "background-color: rgba(45,124,255,0.08); } "
                "QLabel { border: none; background: transparent; }"
            )
            UNSELECTED_CELL_STYLE = (
                "QFrame#cell { border: 2px solid transparent; border-radius: 8px; } "
                "QLabel { border: none; background: transparent; }"
            )
            TITLE_SELECTED_STYLE = "border: none; background: transparent; color: #2D7CFF;"
            TITLE_UNSELECTED_STYLE = "border: none; background: transparent;"

            # Manage single selection across all cells in the grid
            selected_cell: Optional["_Clickable"] = None
            def _set_selected_cell(new_cell):
                nonlocal selected_cell
                # Deselect previous cell if different
                if selected_cell is not None and selected_cell is not new_cell:
                    selected_cell.setSelected(False)
                selected_cell = new_cell
                if new_cell is not None:
                    new_cell.setSelected(True)

            class _Clickable(QtWidgets.QFrame):
                def __init__(self, open_callback, select_callback):
                    super().__init__()
                    self._open_callback = open_callback
                    self._select_callback = select_callback
                    self._icon_label = None
                    self._title_label = None
                    self.setCursor(Qt.PointingHandCursor)
                    # Ensure stylesheet backgrounds/borders are painted on QWidget
                    self.setAttribute(Qt.WA_StyledBackground, True)
                    # Avoid focus outline that could look like a second border
                    self.setFocusPolicy(Qt.NoFocus)
                    # Give a predictable selector name for stylesheet scoping
                    self.setObjectName("cell")
                    # Start unselected
                    self.setSelected(False)
                
                def setContent(self, icon_label, title_label):
                    self._icon_label = icon_label
                    self._title_label = title_label
                
                def setSelected(self, is_selected: bool):
                    # Visual selection: single blue border around the whole cell and subtle blue background
                    if is_selected:
                        self.setStyleSheet(SELECTED_CELL_STYLE)
                        if self._title_label is not None:
                            self._title_label.setStyleSheet(TITLE_SELECTED_STYLE)
                    else:
                        self.setStyleSheet(UNSELECTED_CELL_STYLE)
                        if self._title_label is not None:
                            self._title_label.setStyleSheet(TITLE_UNSELECTED_STYLE)

                def mousePressEvent(self, event):
                    # Single click selects this cell
                    if event.button() == Qt.LeftButton and callable(self._select_callback):
                        self._select_callback(self)
                    super().mousePressEvent(event)

                def mouseDoubleClickEvent(self, event):
                    if callable(self._open_callback):
                        self._open_callback()
                    super().mouseDoubleClickEvent(event)

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

                cell = _Clickable(_launch_viewer, _set_selected_cell)
                vbox = QtWidgets.QVBoxLayout(cell)
                vbox.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
                vbox.setContentsMargins(8, 8, 8, 8)

                icon_label = QtWidgets.QLabel()
                icon_label.setFixedSize(96, 96)
                icon_label.setAlignment(Qt.AlignCenter)
                icon_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
                icon_label.setStyleSheet("border: none; background: transparent;")

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
                        if hasattr(part, "getBadge") and part.getBadge() != "":
                            # Paint badge on a copy of the pixmap
                            composed = QPixmap(scaled)
                            painter = QPainter(composed)
                            try:
                                painter.setRenderHint(QPainter.Antialiasing, True)
                                # Measure text and compute pill rect size
                                text = str(part.getBadge())
                                font = painter.font()
                                font.setBold(True)
                                painter.setFont(font)
                                metrics = QFontMetrics(font)
                                text_w = metrics.horizontalAdvance(text)
                                text_h = metrics.height()
                                pad_x = 8
                                pad_y = 4
                                rect_w = text_w + 2 * pad_x
                                rect_h = text_h + 2 * pad_y
                                x = composed.width() - rect_w - 4
                                y = composed.height() - rect_h - 4
                                radius = rect_h / 2.0
                                # Draw red rounded rectangle
                                painter.setBrush(QBrush(QColor(220, 0, 0)))
                                painter.setPen(Qt.NoPen)
                                painter.drawRoundedRect(QRect(x, y, rect_w, rect_h), radius, radius)
                                # Draw white text centered
                                painter.setPen(QColor(255, 255, 255))
                                painter.drawText(QRect(x, y, rect_w, rect_h), Qt.AlignCenter, text)
                            finally:
                                painter.end()
                            icon_label.setPixmap(composed)
                        else:
                            icon_label.setPixmap(scaled)
                except Exception:
                    pass

                title_label = QtWidgets.QLabel(title)
                title_label.setAlignment(Qt.AlignCenter)
                title_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
                title_label.setStyleSheet("border: none; background: transparent;")

                cell.setContent(icon_label, title_label)

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
