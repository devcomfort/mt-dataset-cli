from dataclasses import dataclass


@dataclass
class DownloadLink:
    """
    언어 쌍별 다운로드 리소스를 표현하는 데이터 클래스입니다.
    이 클래스는 단일 언어 쌍에 대한 다운로드 URL을 관리하며,
    `Corpus` 클래스 내에서 여러 언어 쌍의 다운로드 정보를 저장하는 데 사용됩니다.

    Attributes:
        language_pair (str):
            언어 쌍을 나타내는 문자열.
            형식: "{소스언어}-{대상언어}" (예: "en-fr", "ko-zh")
        url (str):
            해당 언어 쌍의 다운로드 리소스 URL.
            예: "https://data.statmt.org/europarl/v10/en-fr.tar.gz"

    Example:
        >>> link = DownloadLink(
        ...     language_pair="en-fr",
        ...     url="https://data.statmt.org/europarl/v10/en-fr.tar.gz"
        ... )
    """

    language_pair: str  # 언어 쌍 식별자 (예: "en-fr", "ko-zh")
    url: str  # 언어 쌍별 다운로드 리소스 URL
