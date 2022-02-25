import subprocess
from pathlib import Path
from app.config import Config
import time


def run_signal_cli():
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
    subprocess.Popen(params, start_new_session=True)
    while True:
        if p.exists():
            break
        time.sleep(1)
