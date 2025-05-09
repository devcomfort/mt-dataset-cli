from typing import Tuple
import openai
import json

from mt_dataset_downloader.core.errors.corpus_processing_error import (
    CorpusProcessingError,
)
from mt_dataset_downloader.prompts.prompt_extract_corpora_sources import (
    PromptExtractCorporaSources,
)
from mt_dataset_downloader.schemas import CorpusServer, CorpusSource
from mt_dataset_downloader.core import create_model, fetch_html


def __get_llm_response(model: openai.OpenAI, html_content: str) -> str:
    """
    HTML 콘텐츠에서 코퍼스 소스 정보를 추출하기 위해 LLM에 요청을 보내고 응답을 반환합니다.

    처리 흐름:
    1. 주어진 HTML 콘텐츠로 프롬프트 생성
    2. OpenAI API를 통해 LLM 호출
    3. 응답 내용 추출 및 검증

    Args:
        model (openai.OpenAI): 인증된 OpenAI API 클라이언트 인스턴스
        html_content (str): 분석할 HTML 문서 전체 내용 (최대 30,000 토큰 권장)

    Returns:
        str: LLM이 추출한 JSON 형식의 코퍼스 소스 정보

    Raises:
        CorpusProcessingError:
            - 프롬프트 생성 실패
            - API 호출 실패
            - 빈 응답 수신
            - 응답 형식 검증 실패
    """
    try:
        # 1. 프롬프트 생성
        prompt_extract_corpora_sources = PromptExtractCorporaSources.compile(
            html=html_content
        )

        # 2. LLM 호출
        response = (
            model.chat.completions.create(
                **prompt_extract_corpora_sources,
            )
            .choices[0]
            .message.content
        )

        # 3. 응답 검증
        if not response:
            raise CorpusProcessingError("LLM 응답이 비어 있습니다.")

        return response

    except Exception as e:
        raise CorpusProcessingError(f"LLM 응답 처리 실패: {e}")


def __process_corpus_data(raw_result: str) -> Tuple[CorpusSource, ...]:
    """
    LLM의 원시 응답을 파싱하여 CorpusSource 객체 튜플로 변환합니다.

    JSON 구조 요구사항:
    {
        "corpora": [
            {
                "title": "코퍼스 명칭",
                "description": "코퍼스 설명",
                "url": "https://example.com/corpus"
            }
        ]
    }

    Args:
        raw_result (str): LLM이 반환한 JSON 형식의 문자열

    Returns:
        Tuple[CorpusSource, ...]: 검증된 코퍼스 소스 객체 튜플

    Raises:
        CorpusProcessingError:
            - JSON 파싱 실패
            - 필수 필드(title, description, url) 누락
            - 코퍼스 배열 누락
    """
    try:
        # 1. JSON 파싱
        corpora_data = json.loads(raw_result)
    except json.JSONDecodeError as e:
        raise CorpusProcessingError(f"JSON 파싱 실패: {e}")

    # 2. 코퍼스 배열 존재 검증
    if "corpora" not in corpora_data:
        raise CorpusProcessingError("응답에 'corpora' 배열이 누락되었습니다.")

    corpus_sources = []
    # 3. 개별 코퍼스 객체 생성
    for corpus in corpora_data.get("corpora", []):
        try:
            corpus_sources.append(
                CorpusSource(
                    title=corpus["title"],
                    description=corpus["description"],
                    url=corpus["url"],
                )
            )
        except KeyError as e:
            raise CorpusProcessingError(f"필수 필드 누락: {e}")

    return tuple(corpus_sources)


def get_corpora_source_list() -> Tuple[CorpusSource, ...]:
    """
    코퍼스 서버에서 사용 가능한 코퍼스 목록을 추출합니다.

    전체 처리 흐름:
    1. CorpusServer 인스턴스 생성 (기본 URL: https://www.statmt.org/)
    2. 서버 URL에서 HTML 콘텐츠 다운로드
    3. LLM을 통한 코퍼스 정보 추출
    4. 결과 파싱 및 CorpusSource 객체 생성

    Returns:
        Tuple[CorpusSource, ...]: 추출된 코퍼스 소스 객체 튜플

    Raises:
        CorpusProcessingError:
            - HTML 다운로드 실패
            - LLM 처리 실패
            - 응답 파싱 실패
    """
    # 1. 의존성 초기화
    corpus_server = CorpusServer()
    model = create_model()

    # 2. HTML 콘텐츠 가져오기
    url = corpus_server.url
    html = fetch_html(url)

    # 3. LLM 처리
    raw_result = __get_llm_response(model, html)

    # 4. 결과 파싱
    corpus_sources = __process_corpus_data(raw_result)

    return tuple(corpus_sources)
