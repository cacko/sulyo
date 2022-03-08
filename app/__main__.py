from app.signal.client import Client
from botyo_client.app import App
from app import log
from botyo_client.core.config import Config as BotyoConfig
from app.config import Config
from app.signal.server import run_server

try:
    log.info(f">> Starting signal-cli daemon at {Config.signal.host}...")
    with run_server(
        exec=Config.signal.signalcli,
        account=Config.signal.account,
        host=Config.signal.host
    ) as (contacts, groups):
        log.info(">> starting the client")
        client = Client()
        client.contacts = contacts
        client.groups = groups
        app = App(
            BotyoConfig.from_dict(Config.botyo.to_dict()),
            client
        )
        app.start()
except KeyboardInterrupt:
    import sys
    sys.exit(0)
except Exception as e:
    log.exception(e, exc_info=True)
