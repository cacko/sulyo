from app.signal.client import Client
from botyo_client.app import App
from botyo_client.core.config import Config as BotyoConfig
from app.config import Config
from app.signal.server import run_server
import logging

try:
    logging.info(f">> Starting signal-cli daemon at {Config.signal.host}...")
    with run_server(
        exec=Config.signal.signalcli,
        account=Config.signal.account,
        host=Config.signal.host
    ) as (contacts, groups, proc):
        logging.info(">> starting the client")
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
    proc.terminate()
    sys.exit(0)
except Exception as e:
    logging.exception(e, exc_info=True)
