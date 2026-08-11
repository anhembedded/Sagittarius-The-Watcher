import re

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QColor, QPainter, QTextCharFormat, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)

from logview.ui.log_model import COL_MESSAGE


class LogDelegate(QStyledItemDelegate):
    """Custom delegate for the log table view.
    Ensures model-configured level background/foreground colors override stylesheet themes,
    and supports search term highlighting in the message column.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._term: str = ""
        self._use_regex: bool = False
        self._compiled_regex: re.Pattern | None = None

    def set_term(self, term: str, use_regex: bool = False):
        """Set the search term to highlight. Empty string disables highlighting."""
        self._term = term
        self._use_regex = use_regex
        self._compiled_regex = None
        # Performance optimization:
        # Pre-compile the search regex here in set_term() instead of dynamically
        # compiling it inside the highly-frequent paint() method.
        # This significantly reduces CPU overhead and prevents UI lag during fast scrolling
        # when a regex search term is active.
        if self._term and self._use_regex:
            try:
                self._compiled_regex = re.compile(self._term, re.IGNORECASE)
            except re.error:
                self._compiled_regex = None

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        bg_brush = index.data(Qt.ItemDataRole.BackgroundRole)
        fg_brush = index.data(Qt.ItemDataRole.ForegroundRole)

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        # 1. Override Background Color (even with stylesheets active)
        if bg_brush:
            opt.backgroundBrush = bg_brush
            if not (opt.state & QStyle.StateFlag.State_Selected):
                painter.save()
                painter.fillRect(opt.rect, bg_brush)
                painter.restore()
                # Clear alternate feature to prevent Qt from drawing stylesheet alternate bg over it
                opt.features &= ~QStyleOptionViewItem.ViewItemFeature.Alternate

        # 2. Override Foreground Color
        if fg_brush:
            opt.palette.setBrush(opt.palette.ColorGroup.Active, opt.palette.ColorRole.Text, fg_brush)
            opt.palette.setBrush(opt.palette.ColorGroup.Inactive, opt.palette.ColorRole.Text, fg_brush)

        # 3. Rich search term highlighting for the message column (column 5)
        if index.column() == COL_MESSAGE and self._term:
            painter.save()
            text = opt.text

            # Draw selection/hover state if needed
            style = opt.widget.style() if opt.widget else QApplication.style()
            opt.text = ""
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)

            text_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemText, opt, opt.widget)
            painter.setClipRect(text_rect)

            doc = QTextDocument()
            doc.setDocumentMargin(0)
            doc.setDefaultFont(opt.font)
            doc.setPlainText(text)

            highlight_fmt = QTextCharFormat()
            highlight_fmt.setBackground(QColor("#FFFF00"))
            highlight_fmt.setForeground(QColor("#000000"))

            if self._use_regex:
                if self._compiled_regex:
                    for match in self._compiled_regex.finditer(text):
                        cursor = QTextCursor(doc)
                        cursor.setPosition(match.start())
                        cursor.setPosition(match.end(), QTextCursor.MoveMode.KeepAnchor)
                        cursor.mergeCharFormat(highlight_fmt)
            else:
                cursor = QTextCursor(doc)
                find_flags = QTextDocument.FindFlag(0)
                while True:
                    cursor = doc.find(self._term, cursor, find_flags)
                    if cursor.isNull():
                        break
                    cursor.mergeCharFormat(highlight_fmt)

            painter.translate(text_rect.topLeft())
            doc.setTextWidth(text_rect.width())
            ctx = doc.documentLayout().PaintContext()

            # Keep selected text color if row is selected and not matched by term
            if opt.state & QStyle.StateFlag.State_Selected:
                ctx.palette.setColor(
                    ctx.palette.ColorRole.Text,
                    opt.palette.color(opt.palette.ColorGroup.Active, opt.palette.ColorRole.HighlightedText),
                )
            else:
                if fg_brush:
                    ctx.palette.setBrush(ctx.palette.ColorRole.Text, fg_brush)

            doc.documentLayout().draw(painter, ctx)
            painter.restore()
        else:
            style = opt.widget.style() if opt.widget else QApplication.style()
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)
