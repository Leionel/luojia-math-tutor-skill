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
