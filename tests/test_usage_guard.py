"""Groq 무료 티어 사용량 가드(src/tools/usage_guard.py) 단위 테스트. API 호출 없음.

실행: PYTHONPATH=. python tests/test_usage_guard.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.tools import usage_guard

_TEST_STORE_PATH = os.path.join(tempfile.gettempdir(), "vpg_usage_guard_test.json")


def test_soft_cap_blocks_at_warn_ratio() -> bool:
    if os.path.exists(_TEST_STORE_PATH):
        os.remove(_TEST_STORE_PATH)

    os.environ["GROQ_DAILY_REQUEST_LIMIT"] = "10"
    os.environ["GROQ_USAGE_WARN_RATIO"] = "0.9"

    ok = usage_guard.soft_cap() == 9
    print(f"[usage_guard] soft_cap={usage_guard.soft_cap()} -> {'PASS' if ok else 'FAIL'}")
    assert ok, f"soft_cap 계산 오류: {usage_guard.soft_cap()} (기대: 9)"

    for i in range(8):
        assert not usage_guard.limit_reached(_TEST_STORE_PATH), f"{i}번째 요청에서 조기 차단됨"
        usage_guard.record_request(_TEST_STORE_PATH)

    count_at_8 = usage_guard.today_count(_TEST_STORE_PATH)
    print(f"[usage_guard] 8회 기록 후 count={count_at_8}, limit_reached="
          f"{usage_guard.limit_reached(_TEST_STORE_PATH)}")
    assert count_at_8 == 8
    assert not usage_guard.limit_reached(_TEST_STORE_PATH), "8회(soft_cap 미만)인데 차단됨"

    usage_guard.record_request(_TEST_STORE_PATH)  # 9번째 = soft_cap 도달
    print(f"[usage_guard] 9회 기록 후 limit_reached={usage_guard.limit_reached(_TEST_STORE_PATH)}")
    assert usage_guard.limit_reached(_TEST_STORE_PATH), "9회(soft_cap) 도달했는데 차단 안 됨"

    if os.path.exists(_TEST_STORE_PATH):
        os.remove(_TEST_STORE_PATH)
    return True


if __name__ == "__main__":
    results = [test_soft_cap_blocks_at_warn_ratio()]
    print(f"\n{sum(results)}/{len(results)} 통과")
