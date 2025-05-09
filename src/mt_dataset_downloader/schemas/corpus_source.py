from dataclasses import dataclass


@dataclass
class CorpusSource:
    """
    독립적인 코퍼스 데이터셋 소스를 정의하는 데이터 클래스입니다.
    이 클래스는 단일 코퍼스 저장소의 메타데이터를 표현하며,
    코퍼스의 식별자 정보와 공식 정보 페이지를 제공합니다.

    Attributes:
        title (str): 코퍼스의 공식 명칭.
                   예: "Europarl Corpus" - 데이터셋의 대표 이름
        description (str): 코퍼스의 주요 특징과 목적을 설명하는 텍스트.
                   예: "유럽 의회 회의록을 기반으로 한 다국어 병렬 코퍼스"
        url (str): 코퍼스의 공식 정보 페이지 주소.
                   예: "https://www.statmt.org/europarl/v10/" - 메타데이터 확인용 링크
    """

    title: str  # 코퍼스의 공식 명칭 (예: "UN Corpus")
    description: str  # 코퍼스의 상세 설명 (예: "UN 공식 문서 기반 다국어 병렬 코퍼스")
    url: str  # 코퍼스의 공식 정보 페이지 URL
