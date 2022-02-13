from app.core.blueprint import Blueprint
from app.core.app import command
from app.json_rpc.context import Context
from app.zson_client.models import Method, ZSONRequest, ErrorResult
from app import log


bp = Blueprint("avatar")


@command(
    method=Method.AVATAR_MULTIAVATAR,
    desc="generates multiavatar for given name",
)
async def wiki_command(context: Context):
    log.info(f"trigger {Method.AVATAR_MULTIAVATAR} {context}")
    if not context.query:
        return await context.respond(ErrorResult())
    await context.request(ZSONRequest(
        method=Method.AVATAR_MULTIAVATAR,
        query=context.query
    ))
