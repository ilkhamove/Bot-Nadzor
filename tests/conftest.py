import sys
from pathlib import Path

import pytest

pytest.importorskip("aiohttp", reason="aiohttp is required for bot modules")
pytest.importorskip("aiogram", reason="aiogram is required for bot modules")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
