"""
이 모듈은 코퍼스 관련 데이터 클래스들을 제공합니다.

## 주요 클래스
- `CorpusServer`: 독립적인 코퍼스 서버 정보 관리 클래스. 서버의 URL, 기본 정보 등을 포함합니다.
- `CorpusSource`: 코퍼스의 기본 정보를 정의하는 추상 베이스 클래스. 제목, 설명, 웹 페이지 URL을 포함합니다.
- `Corpus`: `CorpusSource`를 상속받아 구체적인 코퍼스 정보를 관리하는 클래스. 다운로드 링크 목록을 포함합니다.
- `DownloadLink`: 다운로드 링크의 언어 쌍과 URL을 관리하는 데이터 클래스.

## 클래스 관계
1. `CorpusSource` → `Corpus` (상속 관계)
   - `Corpus`는 `CorpusSource`의 기본 정보를 상속받아 확장
2. `Corpus` → `DownloadLink` (합성 관계)
   - `Corpus`는 여러 `DownloadLink` 객체를 포함
3. `CorpusServer`는 독립적으로 사용되며, 다른 모듈에서 코퍼스 목록을 관리할 때 활용

이 모듈을 통해 코퍼스 서버 정보, 코퍼스 기본 정보, 다운로드 링크를 구조적으로 관리할 수 있습니다.
"""

from .corpus_server import CorpusServer  # 코퍼스 서버 정보 관리 클래스
from .corpus_source import CorpusSource  # 코퍼스 기본 정보 클래스
from .corpus import Corpus  # 코퍼스 전체 정보 관리 클래스
from .download_link import DownloadLink  # 다운로드 링크 정보 클래스

__all__ = [
    "CorpusServer",  # 코퍼스 서버 정보 관리
    "CorpusSource",  # 코퍼스 기본 정보 제공
    "Corpus",  # 코퍼스 전체 정보 관리
    "DownloadLink",  # 다운로드 링크 정보 관리
]
