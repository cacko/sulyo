from subprocess import Popen, PIPE, STDOUT
from pathlib import Path
from unidecode import unidecode
from app.config import Config
import time
from contextlib import contextmanager


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
    for line in command_as_dict(exec, account, "listContacts"):
        try:
            number, rest = line.split("Number:")[-1].split("Name:")
            name, _ = rest.split("Blocked")
            contacts[unidecode(number).strip()] = unidecode(
                name).strip()
        except ValueError:
            pass
    groups = {}
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
        yield (contacts, groups)
    finally:
        proc.terminate()
