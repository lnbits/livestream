import asyncio

from fastapi import APIRouter
from loguru import logger

from .crud import db
from .tasks import wait_for_paid_invoices
from .views import livestream_generic_router
from .views_api import livestream_api_router
from .views_lnurl import livestream_lnurl_router

livestream_static_files = [
    {
        "path": "/livestream/static",
        "name": "livestream_static",
    }
]

livestream_ext: APIRouter = APIRouter(prefix="/livestream", tags=["livestream"])
livestream_ext.include_router(livestream_generic_router)
livestream_ext.include_router(livestream_api_router)
livestream_ext.include_router(livestream_lnurl_router)

scheduled_tasks: list[asyncio.Task] = []


def livestream_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)


def livestream_start():
    from lnbits.tasks import create_permanent_unique_task

    task = create_permanent_unique_task("ext_livestream", wait_for_paid_invoices)
    scheduled_tasks.append(task)


__all__ = [
    "livestream_ext",
    "livestream_static_files",
    "livestream_start",
    "livestream_stop",
    "db",
]
