from app.core.models import RenderResult
from app.core.decorators import command
from app.json_rpc.context import Context
from argparse import ArgumentTypeError
from .happybd import HappyBD


@command(trigger="+447479303304")
async def happydb_command(context: Context):
    try:
        message = HappyBD.message(context.source)
        if message:
            await context.send(RenderResult(message=message))
    except ArgumentTypeError:
        pass
