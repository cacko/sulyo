from app.commands.gender.predictor import Predictor
from app.core.decorators import command
from app.core.models import EmptyResult, RenderResult
from app.core.output import to_mono
from app.json_rpc.context import Context
from enum import Enum
from stringcase import titlecase


class GenderIcon(Enum):
    M = ":male_sign:"
    F = ":female_sign:"
    U = ":hear-no-evil_monkey:"


@command(trigger="gender", desc="genderiya")
async def gender_command(context: Context):
    query = context.query
    if query.lower() == "boris johnson":
        message = f"{query.upper()} : :transgender_symbol: faggot"
        await context.send(RenderResult(message=to_mono(message)))
        return
    if len(query.strip()) < 2:
        await context.send(EmptyResult())
        return
    gender = Predictor.classify(query)
    icon = getattr(GenderIcon, gender.name)
    message = f"{query.upper()} : {icon.value}{titlecase(gender.value)}"
    await context.send(RenderResult(message=to_mono(message)))
