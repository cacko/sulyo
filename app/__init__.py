import logging
from os import environ

logging.basicConfig(
    level=getattr(logging, environ.get("BOTYO_LOG_LEVEL", "WARN")),
    format="%(filename)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("BOTYO")
