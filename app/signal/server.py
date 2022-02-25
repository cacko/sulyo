import subprocess
from pathlib import Path
from app.config import Config
import time
# import select


def run_signal_cli():
    params = [
        Config.signal.signalcli,
        "-a",
        Config.signal.account,
        "daemon",
        "--socket",
        Config.signal.host
    ]
    subprocess.Popen(params, start_new_session=True)
    p = Path(Config.signal.host)
    while True:
        print(f"{p} {p.exists()}")
        time.sleep(1)
