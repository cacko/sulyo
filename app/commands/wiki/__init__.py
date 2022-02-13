from app.core.blueprint import Blueprint
from app.core.app import command
from app.json_rpc.context import Context
from app.zson_client.models import Method, ZSONRequest, ErrorResult
from app import log


bp = Blueprint("wiki")


@command(
    method=Method.WIKI_ARTICLE,
    desc="search and displayed the first match for a term from wikipedia",
)
async def wiki_command(context: Context):
    log.info(f"trigger {Method.WIKI_ARTICLE} {context}")
    if not context.query:
        return await context.respond(ErrorResult())
    await context.request(ZSONRequest(
        method=Method.WIKI_ARTICLE,
        query=context.query
    ))
