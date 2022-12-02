from .znayko.app import App
from .znayko.core.config import Config as ZnaykoConfig
from .config import Config
from .signal.server import run_server
from .signal.client import Client
import logging

try:
    logging.info(f">> Starting signal-cli daemon at {Config.signal.host}...")
    with run_server(
        exec=Config.signal.signalcli,
        account=Config.signal.account,
        host=Config.signal.host,
    ) as (contacts, groups, proc):
        logging.info(">> starting the client")
        client = Client()
        client.contacts = contacts
        client.groups = groups
        app = App(
            ZnaykoConfig.from_dict(Config.znayko.to_dict()), client  # type: ignore
        )
        try:
            app.start()
        except KeyboardInterrupt:
            import sys

            proc.terminate()
            sys.exit(0)
except Exception as e:
    logging.exception(e, exc_info=True)
