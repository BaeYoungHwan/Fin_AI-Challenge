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

def _default_store_path() -> Path:
    return Path(os.getenv("VECTOR_STORE_PATH", "src/db/store/cases.json"))


def _load(store_path: str | Path | None) -> list[dict]:
    path = Path(store_path) if store_path is not None else _default_store_path()
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save(records: list[dict], store_path: str | Path | None) -> None:
    path = Path(store_path) if store_path is not None else _default_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def add_case(
    case_id: str, text: str, embedding: list[float], metadata: dict, store_path: str | Path | None = None
) -> None:
    """store_path 미지정 시 VECTOR_STORE_PATH 환경변수(없으면 기본 시드 경로)를 사용한다.
    테스트에서 저장소를 격리할 때는 store_path를 명시적으로 넘긴다 — 환경변수 공유는
    테스트 파일 import 순서에 따라 서로 경로를 덮어쓰는 문제가 있어 피한다."""
    records = _load(store_path)
    records = [r for r in records if r["id"] != case_id]
    records.append({"id": case_id, "content": text, "embedding": embedding, "metadata": metadata})
    _save(records, store_path)


def query_similar_cases(
    embedding: list[float], n_results: int = 3, store_path: str | Path | None = None
) -> list[dict]:
    records = _load(store_path)
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
