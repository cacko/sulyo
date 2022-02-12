# from app.core.decorators import command
# from app.core.models import EmptyResult
# from app.json_rpc.context import Context
# from app.core import Request


# @command(
#     trigger="wikipedia",
#     desc="search and displayed the first match for a term from wikipedia",
# )
# async def wiki_command(context: Context):
#     url = f"wiki/artist/{context.query}"
#     res = await Request(url).fetch()
#     if not res:
#         res = EmptyResult()
#     await context.send(res)
