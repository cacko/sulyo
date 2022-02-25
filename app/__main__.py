from app.json_rpc.api import JsonRpcAPI
from botyo.app import App
from app import log
from botyo.core.config import Config as BotyoConfig
from app.config import Config

try:
    app = App(
        BotyoConfig.from_dict(Config.botyo.to_dict()),
        JsonRpcAPI()
    )
    app.start()
except KeyboardInterrupt:
    import sys
    sys.exit(0)
except Exception as e:
    log.exception(e, exc_info=True)
