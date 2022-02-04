from app.commands.music.albumart import AlbumArt
from app.core.output import to_mono
from app.core.models import EmptyResult, RenderResult
from app.core.decorators import command
from app.json_rpc.context import Context, Typing
from .song import Song
from .lyrics import Lyrics


@command(trigger="song", desc="searches for song and attaches it")
async def song_command(context: Context) -> RenderResult:
    if len(context.query.strip()) < 2:
        await context.send(EmptyResult())
        return
    response = EmptyResult()
    async with Typing(context) as ctx:
        song = Song(ctx.query)
        found = await song.find()
        if found:
            response = RenderResult(
                message=song.messsage, attachment=song.destination.as_posix()
            )
        await ctx.send(response)


@command(trigger="albumart", desc="album art")
async def albumart_command(context: Context):
    if len(context.query.strip()) < 2:
        await context.send(EmptyResult())
        return
    art = AlbumArt(context.query)
    found = await art.find()
    result = (
        EmptyResult()
        if not found
        else RenderResult(attachment=art.destination.as_posix())
    )
    await context.send(result)


@command(trigger="lyrics", desc="dump lyrics of a song")
async def lyrics_command(context: Context):
    if len(context.query.strip()) < 2:
        await context.send(EmptyResult())
        return
    async with Typing(context) as ctx:
        song = Lyrics(ctx.query)
        text = song.text
        result = EmptyResult() if not text else RenderResult(message=to_mono(text))
        await ctx.send(result)
