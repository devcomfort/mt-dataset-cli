from phoenix.client import Client
from phoenix.client.types.prompts import _FormattedPrompt
import os

# Phoenix 클라이언트 인스턴스 생성
client = Client()


class PromptExplainPage:
    @staticmethod
    def compile(html: str) -> _FormattedPrompt:
        """
        주어진 HTML 내용을 기반으로 페이지 설명 프롬프트를 생성합니다.

        Args:
            html (str): 웹 페이지의 HTML 내용

        Returns:
            _FormattedPrompt: 생성된 프롬프트 객체
        """
        # "explain_page" 프롬프트를 Phoenix 클라이언트에서 가져옵니다.
        prompt = client.prompts.get(
            prompt_version_id=os.environ["EXPLAIN_PAGE_PROMPT_ID"]
        )

        # 프롬프트를 HTML 내용으로 포맷팅하여 반환합니다.
        return prompt.format(variables={"html": html})
