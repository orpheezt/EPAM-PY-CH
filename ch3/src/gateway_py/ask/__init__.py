from ..registry import Module
from .errors import AskError
from .handlers import on_ask_error
from .routes import router
from .settings import AskSettings

MODULE: Module = Module(
    name="ask",
    router=router,
    settings=AskSettings,
    exception_handlers={
        AskError: on_ask_error,
    },
)

__all__ = ["MODULE"]
