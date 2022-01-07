from app.commands.cve.subscription import Subscription
from app.core.decorators import command
from app.core.models import EmptyResult, RenderResult
from app.core.text import to_mono
from app.json_rpc.context import Context, Typing
from .cve import CVE


@command(trigger="cve", desc="generates random avatar for the arguments supplied")
async def cve_command(context: Context) -> RenderResult:
    async with Typing(context) as ctx:
        cve = CVE(ctx.query)
        message = await cve.message
        if not message:
            await ctx.send(EmptyResult())
        await ctx.send(RenderResult(message=message))


@command(trigger="cvesubscribe", desc="subscribe for CVE updates")
async def cvesubscribe_command(context: Context) -> RenderResult:
    sub = Subscription(context.group, context.query)
    await sub.schedule()
    await context.send(
        RenderResult(message=to_mono(f"Subscribed for {sub.subscription_name}"))
    )


@command(trigger="cveunsubscribe", desc="unsubscribe for CVE updates")
async def cveunsubscribe_command(context: Context) -> RenderResult:
    sub = Subscription(context.group, context.query)
    try:
        sub.cancel()
        await context.send(
            RenderResult(message=to_mono(f"Unsubscribed for {sub.subscription_name}"))
        )
    except:
        await context.send(EmptyResult())


@command(
    trigger="cvelistsubscriptions", desc="list current subscrionts for CVE updates"
)
async def cvelistsubscriptions_command(context: Context) -> RenderResult:
    response = Subscription.forGroup(context.group)
    await context.send(response)
