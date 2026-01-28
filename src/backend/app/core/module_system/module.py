from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional, Union

from fastapi import APIRouter, FastAPI


StartupFn = Callable[[FastAPI], Union[None, Any, Awaitable[Any]]]
ShutdownFn = Callable[[FastAPI], Union[None, Any, Awaitable[Any]]]


@dataclass(frozen=True)
class Module:
    name: str
    router: APIRouter
    startup: Optional[StartupFn] = None
    shutdown: Optional[ShutdownFn] = None
