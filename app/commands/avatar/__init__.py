# from app.core.decorators import command
# from app.json_rpc.context import Context


# @command(trigger="avatar", desc="generates random avatar for the arguments")
# async def avatar_command(context: Context):
#     url = f"avatar/{context.query}"
#     response = await Request(url).fetch()
#     await context.send(response)
