from __future__ import annotations

import importlib
import inspect
from typing import Any, List

from fastapi import FastAPI

from app.core.module_system.module import Module
from app.utils.custom_logger import log


def load_modules(app: FastAPI, settings: Any) -> List[Module]:
    enabled_str = getattr(settings, "MODULES_ENABLED", "")
    enabled = enabled_str.split(",") if enabled_str else []
    modules: List[Module] = []

    log.info(f"📦 加载模块: {enabled}")

    for module_name in enabled:
        try:
            mod = importlib.import_module(f"app.modules.{module_name}.module")
        except Exception as e:
            log.error(f"❌ Failed to import module '{module_name}': {e}")
            continue

        module_obj = getattr(mod, "MODULE", None)
        if module_obj is None:
            log.error(f"❌ Module '{module_name}' does not export MODULE")
            continue

        if not isinstance(module_obj, Module):
            log.error(f"❌ MODULE in '{module_name}' is not an app.core.module_system.module.Module")
            continue

        # 为每个模块添加对应的路由前缀，避免路由冲突
        app.include_router(module_obj.router, prefix=f"{settings.API_STR}/{module_obj.name}")
        modules.append(module_obj)
        log.info(f"✅ 成功加载模块: {module_name}")

    log.info(f"🎉 共加载 {len(modules)} 个模块")
    return modules


async def run_startup(modules: List[Module], app: FastAPI) -> None:
    for m in modules:
        if m.startup is None:
            continue
        result = m.startup(app)
        if inspect.isawaitable(result):
            await result


async def run_shutdown(modules: List[Module], app: FastAPI) -> None:
    for m in modules:
        if m.shutdown is None:
            continue
        result = m.shutdown(app)
        if inspect.isawaitable(result):
            await result
