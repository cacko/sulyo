from app.core.text import to_mono
from app.core.models import EmptyResult, RenderResult
from app.core.decorators import command
from app.json_rpc.context import Context, Typing
from argparse import ArgumentTypeError
from happybd import HappyBD


@command(trigger="+447479303304")
async def traceroute_command(context: Context):
    try:
        message = HappyBD.message(context.source)
        if message:
            await context.send(RenderResult(message=message))
    except ArgumentTypeError:
        pass
