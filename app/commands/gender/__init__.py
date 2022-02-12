# from app.core.decorators import command
# from app.core import Request
# from app.core.models import EmptyResult
# from app.json_rpc.context import Context


# @command(trigger="gender", desc="genderiya")
# async def gender_command(context: Context):
#     query = context.query
#     res = await Request(f"/gender/name/{query}").fetch()
#     if not res:
#         res = EmptyResult()
#     await context.send(res)
