import subprocess
from pathlib import Path
from app.config import Config
import time
from contextlib import contextmanager


@contextmanager
def run_server(exec, account, host, *args, **kwds):
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
    proc = subprocess.Popen(params, start_new_session=True)
    try:
        while True:
            if p.exists():
                break
            time.sleep(1)
        yield proc
    finally:
        proc.terminate()
