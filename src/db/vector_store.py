"""순수 파이썬 로컬 벡터 저장소 (numpy + JSON 파일).

ChromaDB 대신 사용한다 — chromadb의 chroma-hnswlib 의존성은 네이티브(C++) 컴파일이 필요해
Visual C++ 빌드 도구 없이는 Windows에 설치되지 않는다. 이 프로젝트 규모(시드 수십 건 +
피드백 누적)에서는 브루트포스 코사인 유사도로도 성능 문제가 없어 이 방식이 더 낫다.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

_STORE_PATH = Path(os.getenv("VECTOR_STORE_PATH", "src/db/store/cases.json"))


def _load() -> list[dict]:
    if not _STORE_PATH.exists():
        return []
    with open(_STORE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save(records: list[dict]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def add_case(case_id: str, text: str, embedding: list[float], metadata: dict) -> None:
    records = _load()
    records = [r for r in records if r["id"] != case_id]
    records.append({"id": case_id, "content": text, "embedding": embedding, "metadata": metadata})
    _save(records)


def query_similar_cases(embedding: list[float], n_results: int = 3) -> list[dict]:
    records = _load()
    if not records:
        return []

    query = np.array(embedding)
    query_norm = np.linalg.norm(query) or 1.0

    scored = []
    for r in records:
        vec = np.array(r["embedding"])
        vec_norm = np.linalg.norm(vec) or 1.0
        similarity = float(np.dot(query, vec) / (query_norm * vec_norm))
        scored.append((similarity, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {"id": r["id"], "content": r["content"], "metadata": r["metadata"], "similarity": sim}
        for sim, r in scored[:n_results]
    ]
