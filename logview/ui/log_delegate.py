from PySide6.QtWidgets import (
    QStyledItemDelegate, QStyleOptionViewItem, QApplication, QStyle
)
from PySide6.QtGui import QPainter, QColor, QTextCharFormat, QTextCursor, QTextDocument
from PySide6.QtCore import Qt, QModelIndex, QRectF


class HighlightDelegate(QStyledItemDelegate):
    """Item delegate that draws a yellow highlight behind text matching a search term.

    Works for any column that displays plain text. When no term is set, it
    falls back to the default painting so performance is unaffected.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._term: str = ""

    def set_term(self, term: str):
        """Set the search term to highlight. Empty string disables highlighting."""
        self._term = term

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        if not self._term:
            super().paint(painter, option, index)
            return

        self.initStyleOption(option, index)
        text = option.text

        painter.save()

        # Draw selection / hover background using the platform style
        style = option.widget.style() if option.widget else QApplication.style()
        option.text = ""
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)

        # Compute the text rect
        text_rect = style.subElementRect(
            QStyle.SubElement.SE_ItemViewItemText, option, option.widget
        )
        painter.setClipRect(text_rect)

        # Build a QTextDocument for rich highlighting
        doc = QTextDocument()
        doc.setDocumentMargin(0)
        doc.setDefaultFont(option.font)
        doc.setPlainText(text)

        # Apply yellow highlight to every match (case-insensitive)
        highlight_fmt = QTextCharFormat()
        highlight_fmt.setBackground(QColor("#FFFF00"))
        highlight_fmt.setForeground(QColor("#000000"))

        cursor = QTextCursor(doc)
        find_flags = QTextDocument.FindFlag(0)  # case-insensitive by default
        while True:
            cursor = doc.find(self._term, cursor, find_flags)
            if cursor.isNull():
                break
            cursor.mergeCharFormat(highlight_fmt)

        # Translate and render
        painter.translate(text_rect.topLeft())
        doc.setTextWidth(text_rect.width())
        ctx = doc.documentLayout().PaintContext()
        # Use the foreground color from the view item if selected
        if option.state & QStyle.StateFlag.State_Selected:
            ctx.palette.setColor(
                ctx.palette.ColorRole.Text,
                option.palette.color(option.palette.ColorGroup.Active,
                                     option.palette.ColorRole.HighlightedText)
            )
        doc.documentLayout().draw(painter, ctx)
        painter.restore()
