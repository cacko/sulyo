from app.signal.client import Client
from botyo.app import App
from app import log
from botyo.core.config import Config as BotyoConfig
from app.config import Config
from app.signal.server import run_signal_cli

try:
    with run_signal_cli() as server:
        app = App(
            BotyoConfig.from_dict(Config.botyo.to_dict()),
            Client()
        )
        app.start()
except KeyboardInterrupt:
    import sys
    sys.exit(0)
except Exception as e:
    log.exception(e, exc_info=True)
