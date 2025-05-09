"""
코퍼스 데이터 처리 및 다운로드를 위한 핵심 기능 모듈입니다.

이 모듈은 데이터 수집과 처리를 위한 기본적인 기능을 제공하며,
다양한 코퍼스 데이터셋 작업을 위한 기반을 마련합니다.

주요 기능:
- HTML 콘텐츠 가져오기(fetch_html)

Example:
    >>> from mt_dataset_downloader.core import fetch_html
    >>> html_content = fetch_html("https://example.com/corpus")
"""

from .fetch_html import fetch_html
from .create_model import create_model
from .errors import CorpusProcessingError

__all__ = [
    "fetch_html",
    "create_model",
    "CorpusProcessingError",
]
