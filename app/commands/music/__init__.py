# from app.core.models import EmptyResult, RenderResult
# from app.core import Request
# from app.core.decorators import command
# from app.json_rpc.context import Context, Typing


# @command(trigger="song", desc="searches for song and attaches it")
# async def song_command(context: Context) -> RenderResult:
#     if len(context.query.strip()) < 2:
#         await context.send(EmptyResult())
#         return
#     async with Typing(context) as ctx:
#         url = f"music/song/{ctx.query}"
#         res = await Request(url).fetch()
#         if not res:
#             res = EmptyResult()
#         await ctx.send(res)


# @command(trigger="albumart", desc="album art")
# async def albumart_command(context: Context):
#     if len(context.query.strip()) < 2:
#         await context.send(EmptyResult())
#         return
#     async with Typing(context) as ctx:
#         url = f"music/albumart/{ctx.query}"
#         res = await Request(url).fetch()
#         if not res:
#             res = EmptyResult()
#         await ctx.send(res)


# @command(trigger="lyrics", desc="dump lyrics of a song")
# async def lyrics_command(context: Context):
#     if len(context.query.strip()) < 2:
#         await context.send(EmptyResult())
#         return
#     async with Typing(context) as ctx:
#         url = f"music/lyrics/{ctx.query}"
#         res = await Request(url).fetch()
#         if not res:
#             res = EmptyResult()
#         await ctx.send(res)
