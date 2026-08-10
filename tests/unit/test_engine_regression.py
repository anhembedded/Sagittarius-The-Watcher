import pytest
from sagittarius_engine.infrastructure.config.config_manager import ConfigManager

from logview.models import LogEntry


def test_engine_regression_pipeline(qapp):
    """Regression test ensuring the data pipeline works when bootstrapped via Engine."""
    try:
        from logview.__main__ import create_app
        from logview.ui.main_window import MainWindow
    except ImportError:
        pytest.fail("Imports not implemented yet")

    config_manager = ConfigManager()
    # Mocking some config for the test
    config_manager.set("display", {"max_lines": 100})
    config_manager.set("server", {"host": "localhost", "port": 0})
    config_manager.set("log_format", {"pattern": ""})
    config_manager.set("colors", {})

    app = create_app(config_manager, is_test=True)

    main_window = app.context.container.resolve(MainWindow)
    assert main_window is not None

    tab = main_window.tab_widget.widget(0)
    assert tab is not None

    # Inject a log to ensure pipeline still works
    tab.on_logs_received([LogEntry(raw="test", message="test msg")])
    assert tab.model.rowCount() == 1
    main_window.close()
