import os
from pathlib import Path
from app.config import Config
import time
# import select


def run_signal_cli():
    params = [
        "-a",
        Config.signal.account,
        "daemon",
        "--socket",
        Config.signal.host
    ]
    os.spawnl(os.P_NOWAIT, f'{Config.signal.signalcli} {" ".join(params)}')
    p = Path(Config.signal.host)
    while True:
        print(f"{p} {p.exists()}")
        time.sleep(1)
