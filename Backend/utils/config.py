import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = BASE_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

PAGE_TIMEOUT = int(os.getenv("PAGE_TIMEOUT", 60000))
RENDER_WAIT = int(os.getenv("RENDER_WAIT", 2000))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VISION_MODEL = os.getenv("VISION_MODEL", "gemini-1.5-flash")

# Windows Edge Profile specific settings
EDGE_USER_DATA_DIR = os.getenv("EDGE_USER_DATA_DIR", "")
EDGE_PROFILE_NAME = os.getenv("EDGE_PROFILE_NAME", "Default")