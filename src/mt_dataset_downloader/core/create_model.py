from openai import OpenAI
import os


def create_model() -> OpenAI:
    """
    OpenAI 클라이언트 인스턴스를 생성하여 반환합니다.

    환경 변수 `OPENAI_API_KEY`와 `OPENAI_API_BASE`를 사용하여 OpenAI 클라이언트를 초기화합니다.
    이 함수는 OpenAI API와의 통신을 위한 클라이언트 객체를 생성합니다.

    Returns:
        OpenAI: 초기화된 OpenAI 클라이언트 인스턴스.
    """
    return OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_API_BASE"],
    )
