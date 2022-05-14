from concurrent.futures import ThreadPoolExecutor
from subprocess import Popen, PIPE, STDOUT
from unidecode import unidecode
import time
from contextlib import contextmanager
from app import log
from pathlib import Path


def command_as_dict(exec, account, cmd, tokens: list):
    with Popen(
        [exec, "-a", account, cmd],
        stdout=PIPE,
        stderr=STDOUT
    ) as p:
        for line in iter(p.stdout.readline, b""):
            try:
                id, rest = line.decode().strip().split(
                    tokens[0])[-1].split(tokens[1])
                name, _ = rest.split(tokens[2])
                if name == "null":
                    continue
                yield unidecode(id).strip(), unidecode(name).strip()
            except ValueError:
                pass


def open_signal_socket(exec, host, account):
    p = host
    pf = Path(p)
    if pf.exists():
        pf.unlink()
    params = [
        exec,
        "-a",
        account,
        "daemon",
        "--socket",
        host
    ]
    log.info(">> firing up the shitties daemon in the world")
    proc = Popen(
        params,
        start_new_session=True
    )
    log.info(">> waiting for the junk to open the socker")
    while True:
        if pf.exists():
            break
        time.sleep(1)
    log.info(">> daemon started")
    return proc


@contextmanager
def run_server(exec, account, host, *args, **kwds):
    contacts = {}
    log.info(">> fetching contacts...")
    contacts = {
        id: name
        for id, name in command_as_dict(
            exec,
            account,
            "listContacts",
            ["Number:", "Name:", "Blocked"]
        )
    }
    log.info(f">> {len(contacts)} contacts found")
    log.info(">> fetching groups...")
    groups = {
        id: name
        for id, name in command_as_dict(
            exec,
            account,
            "listGroups",
            ["Id:", "Name:", "Active"]
        )
    }
    log.info(f">> {len(groups)} grounps found")
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(open_signal_socket, exec, host, account)
            proc = future.result()
            yield contacts, groups, proc
    finally:
        log.info("finally")
