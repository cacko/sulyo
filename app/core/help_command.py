from app.core.decorators import command
from app.core.models import RenderResult
from app.core.output import Column, Align, TextOutput
from app.json_rpc import Context


class HelpMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(HelpMeta, cls).__call__(*args, **kwargs)
        return cls._instance

    def register(cls, app):
        if not cls._instance:
            cls._instance = cls(app)
        return cls._instance

    def response(cls) -> RenderResult:
        return RenderResult(message=cls._instance.render())


class Help(metaclass=HelpMeta):

    app = None

    def __init__(self, app) -> None:
        self.app = app

    def render(self, *args, **kwargs) -> str:
        columnns = (
            Column(size=10, align=Align.RIGHT, title="Command"),
            Column(size=50, align=Align.LEFT, title="Description"),
        )
        content = (
            (cmd.trigger, cmd.desc.upper())
            for cmd in sorted(self.app.commands, key=lambda x: x.trigger)
            if cmd.desc
        )
        return TextOutput.renderColumns(
            columns=columnns, content=content, with_header=True
        )


# @command(trigger="botyo", desc="info")
# def botyo(query, groupID, source) -> RenderResult:
#     return RenderResult(message=to_mono(f"Botyo: https://gitlab.com/cacko/botyo"))


@command(trigger="help", desc="shows available commands")
async def help_command(context: Context) -> RenderResult:
    response = Help.response()
    await context.send(response)
