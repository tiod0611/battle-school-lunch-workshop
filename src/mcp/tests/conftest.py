import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# app.config.Settings()가 임포트 시점에 환경변수를 읽으므로, 테스트에서 실제
# NEIS API를 호출하지 않도록 더미 키를 먼저 주입해둔다. (모든 NEIS 호출은
# respx/monkeypatch로 목킹되며, 이 키가 실제로 사용되는 일은 없다.)
os.environ.setdefault("NEIS_API_KEY", "test-dummy-key")
