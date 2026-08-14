import atexit
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Tests must never read/write the real dev/production SQLite database.
# app.database creates its engine at import time from Settings().database_url,
# so this env var has to be set before any `app.*` module is imported anywhere
# in the test session. conftest.py is guaranteed to run first.
_TEST_DB_DIR = tempfile.mkdtemp(prefix="battle-school-lunch-test-")
os.environ["DATABASE_PATH"] = str(Path(_TEST_DB_DIR) / "test.db")
atexit.register(shutil.rmtree, _TEST_DB_DIR, True)
