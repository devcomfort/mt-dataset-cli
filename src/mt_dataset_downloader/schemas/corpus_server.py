from dataclasses import dataclass, field


@dataclass
class CorpusServer:
    """
    코퍼스 서버(Corpus Server)를 나타내는 데이터 클래스입니다.
    이 서버는 다중 기계 번역 코퍼스를 호스팅하는 저장소로,
    각 코퍼스는 독립적인 메타데이터(제목, 설명, URL)를 가진 개별 리소스입니다.

    Attributes:
        url (str): 코퍼스 서버의 기본 URL입니다.
                   예: "https://www.statmt.org/" - 여러 코퍼스를 포함하는 루트 페이지
        title (str): 서버의 공식 명칭.
                   예: "StatMT" - 기계 번역 연구용 코퍼스 컬렉션
        description (str): 서버의 기능과 포함된 코퍼스 유형에 대한 간략한 설명.
                   예: "StatMT는 기계 번역 연구를 위한 다국어 코퍼스 컬렉션입니다."
    """

    url: str = field(default="https://www.statmt.org/")  # 코퍼스 서버의 루트 URL
    title: str = field(default="StatMT")  # 서버의 공식 명칭
    description: str = field(
        default="StatMT는 기계 번역 연구를 위한 다국어 코퍼스 컬렉션입니다."
    )  # 서버의 기능 설명
