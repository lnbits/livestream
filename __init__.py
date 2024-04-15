import asyncio

from fastapi import APIRouter
from loguru import logger

from lnbits.db import Database
from lnbits.helpers import template_renderer
from lnbits.tasks import create_permanent_unique_task

db = Database("ext_livestream")

livestream_static_files = [
    {
        "path": "/livestream/static",
        "name": "livestream_static",
    }
]

livestream_ext: APIRouter = APIRouter(prefix="/livestream", tags=["livestream"])


def livestream_renderer():
    return template_renderer(["livestream/templates"])


from .lnurl import *  # noqa: F401,F403
from .tasks import wait_for_paid_invoices
from .views import *  # noqa: F401,F403
from .views_api import *  # noqa: F401,F403


scheduled_tasks: list[asyncio.Task] = []

def livestream_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)

def livestream_start():
    task = create_permanent_unique_task("ext_livestream", wait_for_paid_invoices)
    scheduled_tasks.append(task)
