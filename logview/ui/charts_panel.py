from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCharts import QChart, QChartView, QPieSeries
from PySide6.QtGui import QPainter
from PySide6.QtCore import Slot

class LiveStatsPanel(QWidget):
    """
    Panel to show live statistics of log levels.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.series = QPieSeries()
        self.series.setHoleSize(0.35)

        # Initialize slices
        self.slice_info = self.series.append("INFO", 0)
        self.slice_warn = self.series.append("WARNING", 0)
        self.slice_error = self.series.append("ERROR", 0)
        self.slice_debug = self.series.append("DEBUG", 0)
        self.slice_crit = self.series.append("CRITICAL", 0)

        # Colors match status bar
        self.slice_error.setColor("#e74c3c")
        self.slice_crit.setColor("#8e44ad")
        self.slice_warn.setColor("#e67e22")
        self.slice_debug.setColor("#7f8c8d")
        self.slice_info.setColor("#3498db") # Default info color

        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle("Log Levels")
        self.chart.legend().hide()
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        layout.addWidget(self.chart_view)

    @Slot(dict)
    def update_counts(self, counts: dict):
        self.slice_info.setValue(counts.get("INFO", 0))
        self.slice_warn.setValue(counts.get("WARNING", 0))
        self.slice_error.setValue(counts.get("ERROR", 0))
        self.slice_debug.setValue(counts.get("DEBUG", 0))
        self.slice_crit.setValue(counts.get("CRITICAL", 0))

        # Only show labels for non-zero slices
        for slc in [self.slice_info, self.slice_warn, self.slice_error, self.slice_debug, self.slice_crit]:
            if slc.value() > 0:
                slc.setLabelVisible(True)
                slc.setLabel(f"{slc.label().split()[0]} ({int(slc.value())})")
            else:
                slc.setLabelVisible(False)
