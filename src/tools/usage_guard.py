"""Groq 무료 티어 일일 요청 한도를 여유 있게 넘기지 않도록 로컬에서 사용량을 추적한다.

Groq 무료 티어(llama-3.3-70b-versatile 기준)의 일일 요청 한도(RPD)는 계정 설정에 따라
console.groq.com/settings/limits 에서 바뀔 수 있으므로 GROQ_DAILY_REQUEST_LIMIT 환경변수로
직접 확인 후 맞춰 조정한다. 기본값은 이 프로젝트 조사 시점 기준 1,000회/일이다.

이 카운터는 로컬 JSON 파일 기반이라 앱이 재배포되면(예: Streamlit Cloud가 git push 시
컨테이너를 새로 만드는 경우) 초기화된다 — Groq 콘솔의 실제 사용량과 100% 일치를 보장하지
않는 '최선 노력' 방어선이며, 실제 한도 초과는 여전히 Groq API가 최종적으로 막아준다.
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

_DEFAULT_STORE_PATH = "src/db/store/groq_usage.json"


def _daily_limit() -> int:
    return int(os.getenv("GROQ_DAILY_REQUEST_LIMIT", "1000"))


def _warn_ratio() -> float:
    return float(os.getenv("GROQ_USAGE_WARN_RATIO", "0.9"))


def _store_path(store_path: str | Path | None) -> Path:
    if store_path is not None:
        return Path(store_path)
    return Path(os.getenv("GROQ_USAGE_STORE_PATH", _DEFAULT_STORE_PATH))


def _today() -> str:
    return date.today().isoformat()


def _load(store_path: str | Path | None) -> dict:
    path = _store_path(store_path)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict, store_path: str | Path | None) -> None:
    path = _store_path(store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def today_count(store_path: str | Path | None = None) -> int:
    return _load(store_path).get(_today(), 0)


def soft_cap() -> int:
    return int(_daily_limit() * _warn_ratio())


def limit_reached(store_path: str | Path | None = None) -> bool:
    return today_count(store_path) >= soft_cap()


def record_request(store_path: str | Path | None = None) -> None:
    # 지난 날짜의 기록은 정리한다 — 파일이 무한히 커지지 않도록 오늘 것만 남긴다.
    today = _today()
    count = today_count(store_path) + 1
    _save({today: count}, store_path)
