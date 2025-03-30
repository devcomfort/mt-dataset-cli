"""
Apache HTTP 서버 웹 페이지 파싱을 위한 모듈
"""

import httpx
import re
import time
from functools import lru_cache
from bs4 import BeautifulSoup
from typing import List

from .schemas import WebParser, FileSystemEntry

class ApacheHttpServerParser(WebParser):
    """
    Apache HTTP 서버 디렉토리 리스팅 페이지를 파싱하는 클래스
    
    WebParser를 상속받아 Apache 스타일의 디렉토리 리스팅 페이지에서
    파일과 디렉토리 링크를 추출하는 기능을 제공합니다.
    """

    def __init__(self, url: str, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Args:
            url (str): 파싱할 웹 페이지의 URL
            max_retries (int): 최대 재시도 횟수
            retry_delay (float): 재시도 간 대기 시간(초)
        """
        super().__init__(url)
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @lru_cache(maxsize=1000)
    def fetch(self) -> str:
        """
        웹 페이지의 내용을 가져옵니다. 실패 시 재시도합니다.
        
        Args:
            url (str): 가져올 웹 페이지의 URL
            
        Returns:
            str: 웹 페이지의 HTML 내용
            
        Raises:
            httpx.HTTPError: 모든 재시도 후에도 HTTP 요청이 실패한 경우
        """
        retries = 0
        while retries < self.max_retries:
            try:
                response = httpx.get(self.url, follow_redirects=True, timeout=30.0)
                response.raise_for_status()
                return response.text
            except httpx.HTTPError as e:
                retries += 1
                if retries == self.max_retries:
                    raise
                time.sleep(self.retry_delay * retries)  # 지수 백오프

    def parse(self) -> List[FileSystemEntry]:
        """
        웹 페이지를 파싱하여 Apache 디렉토리 리스팅의 요소들을 반환합니다.
        
        Returns:
            List[FileSystemEntry]: 파싱된 파일/디렉토리 요소 리스트
        """
        content = self.fetch()
        soup = BeautifulSoup(content, 'lxml')

        elements = []
        rows = soup.select("body > table tr")[3:-1]  # 헤더와 푸터 제외
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:  # Name, Last modified, Size, Description 컬럼이 있는지 확인
                anchor = cols[1].find('a')
                if anchor:
                    filename = anchor.text
                    url = anchor.get('href')
                    url = url if url.startswith('http') else self.url.rstrip('/') + '/' + url
                else:
                    filename = ''
                    url = ''

                last_modified = cols[2].text.strip()
                size = cols[3].text.strip()
                description = cols[4].text.strip()
                
                element = FileSystemEntry(
                    url=url,
                    filename=filename,
                    last_modified=last_modified,
                    size=size,
                    description=description
                )
                elements.append(element)
                
        return elements

if __name__ == "__main__":
    # 사용 예시
    parser = ApacheHttpServerParser("https://www.statmt.org/europarl/v10/")
    
    # 모든 링크 가져오기
    links = parser.parse()
    print(f"발견된 링크 수: {len(links)}")
    for link in links[:5]:  # 처음 5개 링크만 출력      
        print(f"- {link}")
