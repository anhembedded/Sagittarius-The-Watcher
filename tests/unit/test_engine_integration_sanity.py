import pytest
from sagittarius_engine import App
from sagittarius_engine.infrastructure.config.config_manager import ConfigManager
from sagittarius_engine.interfaces.i_config import IConfig

def test_bootstrapper_di_sanity(qapp):
    """Sanity test to ensure the engine bootstrapper correctly sets up DI."""
    try:
        from logview.__main__ import create_app
    except ImportError:
        pytest.fail("create_app is not implemented yet in logview.__main__")
        
    config_manager = ConfigManager()
    
    # We expect create_app to return a valid Engine App
    app = create_app(config_manager, is_test=True)
    assert isinstance(app, App)
    
    # Assert IConfig is resolvable
    resolved_config = app.context.container.resolve(IConfig)
    assert resolved_config is config_manager
    
    # Check if boot and stop run without exceptions
    app.boot()
    app.stop()
    
    # Assert MainWindow is resolvable (registered by LogViewerModule)
    from logview.ui.main_window import MainWindow
    resolved_window = app.context.container.resolve(MainWindow)
    assert isinstance(resolved_window, MainWindow)
