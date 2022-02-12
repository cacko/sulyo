# from app.core.decorators import command
# from app.core import Request
# from app.json_rpc.context import Context


# @command(
#     trigger="logo", desc="logo for the requested football team"
# )
# async def logo_command(context: Context):
#     res = await Request(f"logo/{context.query}").fetch()
#     await context.send(res)
