import asyncio, socket, time
import nodriver as uc
import time
from pathlib import Path
import yaml


ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config" / "nodriver_config.yaml"
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

def wait_for_port(host, port, timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return True
        except:
            time.sleep(0.2)
    return False

async def connect_browser(
        host,
        port,
        usr_data_dir,
        headless=False,
        no_sandbox=True
        ):
    if not wait_for_port(host, port, timeout=10):
        raise Exception(f"Cannot connect to browser at {host}:{port}")
    browser = await uc.start(
    host=host,
    port=port,
    headless=headless,
    no_sandbox=no_sandbox,
    user_data_dir=usr_data_dir
    )
    return browser