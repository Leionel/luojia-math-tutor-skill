import os
import tempfile
from pathlib import Path


_TEST_DATABASE_DIR = tempfile.TemporaryDirectory(
    prefix="luojia-tutor-tests-",
)
_TEST_DATABASE_PATH = (
    Path(_TEST_DATABASE_DIR.name) / "luojia_tutor_test.db"
)

os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DATABASE_PATH}"

# Keep the suite offline and deterministic: app.config loads apps/api/.env at
# import time, which would otherwise hand the tests the developer's real
# LLM_API_KEY and make them issue live model calls. Must be set before any
# `app.*` import, which is why it lives here rather than in a fixture.
os.environ["LUOJIA_NO_DOTENV"] = "1"
os.environ.pop("LLM_API_KEY", None)
os.environ.pop("MINERU_API_KEY", None)

os.environ.pop("TAVILY_API_KEY", None)
