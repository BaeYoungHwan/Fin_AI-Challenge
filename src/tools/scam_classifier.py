from __future__ import annotations

from dataclasses import dataclass, field

# 사기 여부를 단정하지 않는다 — 여기서 만드는 것은 "위험 신호 탐지 + 유형 후보 제시"이지 판정이 아니다.
# 최종 판정은 Analysis Agent가 법령 근거 + 유사 사례를 종합해 "위험도 + 안전 행동요령" 형태로만 출력한다.

SCAM_TYPES = {
    "기관사칭형": {
        "keywords": ["검찰", "경찰", "금융감독원", "금감원", "수사", "계좌 동결", "명의도용", "범죄에 연루"],
        "law_keywords": ["통신사기피해환급법", "전자금융거래법", "개인정보 보호법"],
    },
    "가족지인사칭형": {
        "keywords": [
            "엄마", "아빠", "딸", "아들", "자녀", "가족", "지인", "급전", "빌려",
            "폰 고장", "폰이 고장", "액정 깨", "액정이 깨",
        ],
        "law_keywords": ["통신사기피해환급법", "정보통신망법"],
    },
    "대출빙자형": {
        "keywords": ["저금리", "대환대출", "정부지원", "신용등급", "선입금", "보증보험료"],
        "law_keywords": ["대부업법", "특정경제범죄 가중처벌 등에 관한 법률"],
    },
    "몸캠피싱형": {
        "keywords": ["영상통화", "몸캠", "합성", "유포", "협박"],
        "law_keywords": ["정보통신망법", "성폭력범죄의 처벌 등에 관한 특례법"],
    },
}

RED_FLAG_RULES = [
    ("비대면 매체", ["문자", "메신저", "카톡", "톡으로", "전화로만", "영상통화"]),
    ("급전·이체 요구", ["급전", "이체", "송금", "입금해", "입금하라", "빌려줘", "빌려달라", "보내달라"]),
    ("개인정보·인증 요구", ["계좌번호", "otp", "비밀번호", "인증번호", "주민번호"]),
    ("원격/설치 유도", ["원격", "앱 설치", "설치", "링크 클릭", "링크", "apk"]),
    ("긴급성 강조", ["지금 당장", "급하게", "빨리", "오늘 안에", "시간 없어"]),
    ("협박·유포 위협", ["협박", "유포", "합성", "몸값"]),
]


@dataclass
class ClassificationResult:
    candidate_types: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    law_keywords: list[str] = field(default_factory=list)


def detect_red_flags(text: str) -> list[str]:
    lowered = text.lower()
    return [label for label, triggers in RED_FLAG_RULES if any(t.lower() in lowered for t in triggers)]


def classify(text: str) -> ClassificationResult:
    """텍스트에서 위험 신호와 유형 후보를 탐지한다. 확정 판정이 아니라 근거 제시용이다."""
    red_flags = detect_red_flags(text)

    candidate_types: list[str] = []
    law_keywords: set[str] = set()
    for scam_type, spec in SCAM_TYPES.items():
        if any(kw in text for kw in spec["keywords"]):
            candidate_types.append(scam_type)
            law_keywords.update(spec["law_keywords"])

    # 유형 키워드가 하나도 안 걸려도 위험 신호가 있으면 기본 법령(통신사기피해환급법)은 조회한다
    if not law_keywords and red_flags:
        law_keywords.add("통신사기피해환급법")

    return ClassificationResult(
        candidate_types=candidate_types,
        red_flags=red_flags,
        law_keywords=sorted(law_keywords),
    )
