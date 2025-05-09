from dataclasses import dataclass
from .download_link import DownloadLink
from .corpus_source import CorpusSource


@dataclass
class Corpus(CorpusSource):
    """
    완전한 코퍼스 데이터셋을 표현하는 데이터 클래스입니다.
    이 클래스는 CorpusSource를 상속받아 기본 메타데이터를 확장하고,
    실제 다운로드 가능한 리소스 정보를 추가로 포함합니다.

    사용 목적:
    - 웹 크롤링을 통한 코퍼스 정보 수집
    - 언어 쌍별 다운로드 링크 관리
    - 데이터셋 처리 및 변환 작업 지원

    Attributes:
        title (str): 코퍼스의 공식 명칭 (CorpusSource 상속)
        description (str): 코퍼스의 상세 설명 (CorpusSource 상속)
        url (str): 코퍼스의 공식 정보 페이지 URL (CorpusSource 상속)
        download_links (list[DownloadLink]):
            지원되는 언어 쌍별 다운로드 링크 목록.
            예: [DownloadLink(src_lang='en', tgt_lang='fr', url='...'), ...]

    Example:
        >>> corpus = Corpus(
        ...     title="Europarl Corpus",
        ...     description="유럽 의회 회의록 기반 병렬 코퍼스",
        ...     url="https://www.statmt.org/europarl/v10/",
        ...     download_links=[
        ...         DownloadLink('en', 'fr', 'https://data.statmt.org/europarl/v10/en-fr.tar.gz'),
        ...         DownloadLink('en', 'de', 'https://data.statmt.org/europarl/v10/en-de.tar.gz')
        ...     ]
        ... )
    """

    download_links: list[DownloadLink]  # 언어 쌍별 다운로드 URL 목록
