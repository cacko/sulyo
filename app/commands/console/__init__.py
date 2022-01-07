from app.core.text import to_mono
from app.core.models import EmptyResult, RenderResult
from app.core.decorators import command
from app.json_rpc.context import Context, Typing
from .traceroute import Traceroute
from .dig import Dig
from .whois import WhoIs
from .tcptraceroute import TcpTraceroute
from argparse import ArgumentTypeError


@command(trigger="traceroute", desc="dumps traceroute to given location")
async def traceroute_command(context: Context):
    try:
        async with Typing(context) as ctx:
            traceroute = Traceroute(ctx.query)
            text = traceroute.text
            if not text:
                await ctx.send(EmptyResult())
            else:
                await ctx.send(RenderResult(message=text))
    except ArgumentTypeError:
        await context.send(RenderResult(message=to_mono("are you stupid?")))


@command(trigger="tcptraceroute", desc="dumps tcptraceroute to given location")
async def tcptraceroute_command(context: Context):
    try:
        async with Typing(context) as ctx:
            traceroute = TcpTraceroute(ctx.query)
            text = traceroute.text
            if not text:
                await ctx.send(EmptyResult())
                return
            await ctx.send(RenderResult(message=text))
    except ArgumentTypeError:
        await context.send(RenderResult(message=to_mono("are you stupid?")))


@command(trigger="dig", desc="dumps dig to given location")
async def dig_command(context: Context):
    try:
        async with Typing(context) as ctx:
            dig = Dig(ctx.query)
            text = dig.text
            if not text:
                await ctx.send(EmptyResult())
                return
            await ctx.send(RenderResult(message=text))
    except ArgumentTypeError:
        await context.send(RenderResult(message=to_mono("are you stupid?")))


@command(trigger="whois", desc="dumps whois to given domain")
async def whois_command(context: Context):
    try:
        async with Typing(context) as ctx:
            whois = WhoIs(ctx.query)
            text = whois.text
            if not text:
                await ctx.send(EmptyResult())
                return
            await ctx.send(RenderResult(message=text))
    except ArgumentTypeError:
        await context.send(RenderResult(message=to_mono("are you stupid?")))
