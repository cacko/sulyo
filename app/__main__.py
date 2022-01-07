from app import App, log, Config
from os import environ
from pathlib import Path
import toml


try:
    log.info(f"Init start")

    config: Config = Config.from_dict(
        {
            **environ,
            "SETTINGS": toml.loads(
                Path(environ.get("SETTINGS_PATH", "app/settings.toml")).read_text()
            ),
        }
    )
    app = App(config)
    from app.core.decorators import command, CommandDef
    from app.storage import Storage
    from app.commands.ontv.ontv import OnTV
    from app.commands.gender.predictor import Predictor
    from app.commands import *
    from app.core.help_command import Help

    Storage.register(app)
    Help.register(app)
    OnTV.register(app)
    Predictor.register(app)
    app.register_scheduler()
    log.info("Init done")
    app.start()
except KeyboardInterrupt:
    import sys

    sys.exit(0)
except Exception as e:
    log.exception(e, exc_info=True)
