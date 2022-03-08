from subprocess import Popen, PIPE, STDOUT
from pathlib import Path
from unidecode import unidecode
from app.config import Config
import time
from contextlib import contextmanager
from app import log


def command_as_dict(exec, account, cmd):
    with Popen(
        [exec, "-a", account, cmd],
        stdout=PIPE,
        stderr=STDOUT
    ) as p:
        for line in iter(p.stdout.readline, b""):
            yield line.decode().strip()


@contextmanager
def run_server(exec, account, host, *args, **kwds):
    contacts = {}
    log.info(">> fetching contacts...")
    for line in command_as_dict(exec, account, "listContacts"):
        try:
            number, rest = line.split("Number:")[-1].split("Name:")
            name, _ = rest.split("Blocked")
            contacts[unidecode(number).strip()] = unidecode(
                name).strip()
        except ValueError:
            pass
    groups = {}
    log.info(f">> {len(contacts)} contacts found")
    log.info(">> fetching groups...")
    for line in command_as_dict(exec, account, "listGroups"):
        try:
            id, rest = line.split("Id:")[-1].split("Name:")
            name, _ = rest.split("Active")
            if name == "null":
                continue
            groups[unidecode(id).strip()] = unidecode(
                name).strip()
        except ValueError:
            pass
    log.info(f">> {len(groups)} grounps found")
    log.info(">> firing up the shitties daemon in the world")
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
    proc = Popen(
        params,
        start_new_session=True,
        stdout=PIPE,
        stderr=STDOUT
    )
    try:
        log.info(">> waiting for the junk to open the socker")
        while True:
            if p.exists():
                break
            time.sleep(1)
        log.info(">> daemon started")
        yield (contacts, groups, proc)
    finally:
        pass
