from concurrent.futures import ThreadPoolExecutor
from subprocess import Popen, PIPE, STDOUT
from unidecode import unidecode
import time
import logging
from contextlib import contextmanager
from pathlib import Path


def command_as_dict(exec, account, cmd, tokens: list):
    with Popen([exec, "-a", account, cmd], stdout=PIPE, stderr=STDOUT) as p:
        assert p.stdout
        for line in iter(p.stdout.readline, b""):
            try:
                id, rest = line.decode().strip().split(tokens[0])[-1].split(tokens[1])
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
    params = [exec, "-a", account, "daemon", "--socket", host]
    logging.info(">> firing up the shitties daemon in the world")
    proc = Popen(params, start_new_session=True)
    logging.info(">> waiting for the junk to open the socker")
    while True:
        if pf.exists():
            break
        time.sleep(1)
    logging.info(">> daemon started")
    return proc


@contextmanager
def run_server(exec, account, host, *args, **kwds):
    contacts = {}
    logging.info(">> fetching contacts...")
    contacts = {
        id: name
        for id, name in command_as_dict(
            exec, account, "listContacts", ["Number:", "Name:", "Blocked"]
        )
    }
    logging.info(f">> {len(contacts)} contacts found")
    logging.info(">> fetching groups...")
    groups = {
        id: name
        for id, name in command_as_dict(
            exec, account, "listGroups", ["Id:", "Name:", "Active"]
        )
    }
    logging.info(f">> {len(groups)} grounps found")
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(open_signal_socket, exec, host, account)
            proc = future.result()
            yield contacts, groups, proc
    finally:
        logging.info("finally")
