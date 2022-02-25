import subprocess
from pathlib import Path
from app.config import Config
import time
from contextlib import contextmanager


@contextmanager
def run_server(*args, **kwds):
    p = Path(Config.signal.host)
    if p.exists():
        p.unlink()
    params = [
        Config.signal.signalcli,
        "-a",
        Config.signal.account,
        "daemon",
        "--socket",
        Config.signal.host
    ]
    proc = subprocess.Popen(params, start_new_session=True)
    try:
        while True:
            if p.exists():
                break
            time.sleep(1)
        yield proc
    finally:
        proc.terminate()
