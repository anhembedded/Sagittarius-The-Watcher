from sagittarius_engine.interfaces.i_config import IConfig
from sagittarius_engine.interfaces.i_extension import IExtension
from sagittarius_engine.kernel.context import EngineContext

from logview.ui.main_window import MainWindow


class LogViewerModule(IExtension[EngineContext]):
    """
    Sagittarius Engine Extension for Log Viewer.
    Registers the core dependencies into the DI container.
    """

    def register(self, context: EngineContext) -> None:
        config_manager = context.container.resolve(IConfig)

        # 1. Register Root Window
        main_window = MainWindow(config_manager.get_all())
        context.container.singleton(MainWindow, main_window)

    def boot(self, context: EngineContext) -> None:
        pass

    def shutdown(self, context: EngineContext) -> None:
        pass
