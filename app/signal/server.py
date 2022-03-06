from subprocess import Popen, PIPE, STDOUT
from pathlib import Path

from app.config import Config
import time
from contextlib import contextmanager


@contextmanager
def run_server(exec, account, host, *args, **kwds):
    contacts: dict[str, str] = {}
    with Popen(
        [exec, "-a", account, "listContacts"],
        stdout=PIPE,
        stderr=STDOUT
    ) as p:
        for line in iter(p.stdout.readline, b""):
            line = line.decode().strip()
            number, rest = line.split("Number:")[-1].split("Name:")
            name, _ = rest[-1].split("Blocked")
            contacts[number.strip()] = name.strip()
    p = Path(Config.signal.host)
    if p.exists():
        p.unlink()
    params = [
        exec,
        "-a",
        account,
        "daemon",
        "--socket",
        host
    ]
    proc = Popen(params, start_new_session=True)
    try:
        while True:
            if p.exists():
                break
            time.sleep(1)
        yield contacts
    finally:
        proc.terminate()
