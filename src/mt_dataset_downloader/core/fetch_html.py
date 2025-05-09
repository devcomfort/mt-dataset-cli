import requests


def fetch_html(url: str) -> str:
    """
    주어진 URL에서 HTML 내용을 가져옵니다.

    Args:
        url (str): HTML 내용을 가져올 웹 페이지의 URL.

    Returns:
        str: 웹 페이지의 HTML 내용.

    Raises:
        requests.exceptions.RequestException: 네트워크 요청 실패 시
        requests.exceptions.HTTPError: HTTP 4xx/5xx 응답 코드 수신 시
        requests.exceptions.ConnectionError: 서버 연결 실패 시
        requests.exceptions.Timeout: 요청 타임아웃 발생 시
    """
    response = requests.get(url)  # HTTP GET 요청을 보내고 응답을 받습니다.
    response.raise_for_status()  # HTTP 오류(4xx, 5xx) 발생 시 예외를 발생시킵니다.
    return response.text  # 응답에서 HTML 내용을 문자열로 반환합니다.
