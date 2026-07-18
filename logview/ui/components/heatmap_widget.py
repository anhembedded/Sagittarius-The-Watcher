from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, Slot


class LogHeatmapWidget(QWidget):
    """
    Minimap / Heatmap widget displayed next to the scrollbar.
    Draws warning/error markers and a viewport overlay.
    """

    def __init__(self, model, table_view, parent=None):
        super().__init__(parent)
        self.model = model
        self.table_view = table_view
        self.setFixedWidth(16)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Connect to scrollbar and model signals to trigger repaints
        self.table_view.verticalScrollBar().valueChanged.connect(self.update)
        self.table_view.verticalScrollBar().rangeChanged.connect(self.update)
        self.model.layoutChanged.connect(self.update)
        self.model.dataChanged.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # Draw track background
        painter.fillRect(self.rect(), QColor("#1e1e24"))

        n = self.model.rowCount()
        if n == 0:
            return

        h = self.height()

        # Helper to map row index to y-coordinate
        def row_to_y(r):
            return int((r / n) * h)

        # Draw Warning markers (orange)
        warning_rows = getattr(self.model, "_warning_rows", [])
        painter.setPen(QPen(QColor("#ff7800"), 1))
        for r in warning_rows:
            y = row_to_y(r)
            painter.drawLine(0, y, self.width(), y)

        # Draw Error/Critical markers (red)
        error_rows = getattr(self.model, "_error_rows", [])
        painter.setPen(QPen(QColor("#f66151"), 1))
        for r in error_rows:
            y = row_to_y(r)
            painter.drawLine(0, y, self.width(), y)

        # Draw Search highlight markers (yellow)
        find_match_rows = getattr(self.model, "_find_match_rows", [])
        painter.setPen(QPen(QColor("#e5c07b"), 1.5))
        for r in find_match_rows:
            y = row_to_y(r)
            painter.drawLine(0, y, self.width(), y)

        # Draw Viewport Overlay
        scrollbar = self.table_view.verticalScrollBar()
        val = scrollbar.value()
        page_step = scrollbar.pageStep()
        max_val = scrollbar.maximum()

        # Calculate viewport rows
        first_visible = val
        last_visible = val + page_step

        y_top = row_to_y(first_visible)
        y_bottom = row_to_y(last_visible)
        y_height = max(4, y_bottom - y_top)

        # Draw viewport box
        painter.fillRect(0, y_top, self.width(), y_height, QColor(255, 255, 255, 30))
        painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
        painter.drawRect(0, y_top, self.width() - 1, y_height)

    def mousePressEvent(self, event):
        self._scroll_to_mouse(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._scroll_to_mouse(event)

    def _scroll_to_mouse(self, event):
        n = self.model.rowCount()
        if n == 0:
            return
        y = event.y()
        h = self.height()
        percentage = max(0.0, min(1.0, y / h))
        target_row = int(percentage * n)

        scrollbar = self.table_view.verticalScrollBar()
        scrollbar.setValue(target_row - (scrollbar.pageStep() // 2))
        self.update()
