import importlib.util
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent / "bot-md5-python"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

spec = importlib.util.spec_from_file_location("bot_md5_app", APP_DIR / "main.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

app = module.app
