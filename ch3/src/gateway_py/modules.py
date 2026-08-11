from fastapi import FastAPI

from . import ask, health
from .registry import Module

MODULES: tuple[Module, ...] = (health.MODULE, ask.MODULE)


def install_modules(app: FastAPI) -> None:
    for module in MODULES:
        if not module.settings().enabled:
            continue
        app.include_router(module.router)
        for exc_type, handler in module.exception_handlers.items():
            app.exception_handler(exc_type)(handler)
