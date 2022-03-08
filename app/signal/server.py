from concurrent.futures import ThreadPoolExecutor
from subprocess import Popen, PIPE, STDOUT
from unidecode import unidecode
import time
from contextlib import contextmanager
from app import log
from pathlib import Path


def command_as_dict(exec, account, cmd):
    with Popen(
        [exec, "-a", account, cmd],
        stdout=PIPE,
        stderr=STDOUT
    ) as p:
        for line in iter(p.stdout.readline, b""):
            yield line.decode().strip()


def open_signal_socket(exec, host, account):
    p = host
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
    log.info(">> firing up the shitties daemon in the world")
    proc = Popen(
        params,
        start_new_session=True
    )
    log.info(">> waiting for the junk to open the socker")
    while True:
        if Path(p).exists():
            break
        time.sleep(1)
    log.info(">> daemon started")
    return proc


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

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(open_signal_socket, exec, host, account)
            proc = future.result()
            yield contacts, groups, proc
    finally:
        log.info("finally")
