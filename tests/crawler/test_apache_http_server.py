"""
Apache HTTP Server 파서 테스트 모듈

pytest를 사용하여 ApacheHttpServerParser 클래스의 기능을 테스트합니다.
"""
import pytest
import os
import sys
import asyncio
from unittest.mock import MagicMock, patch
from typing import List
import httpx
from bs4 import BeautifulSoup

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.mt_dataset_cli.crawler.apache_http_server import ApacheHttpServerParser, crawl_and_display
from src.mt_dataset_cli.crawler.schemas import FileSystemEntry

# 테스트용 HTML 콘텐츠
SAMPLE_HTML = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
<head>
<title>Index of /europarl/v10</title>
</head>
<body>
<h1>Index of /europarl/v10</h1>
<table>
<tr><th valign="top"><img src="/icons/blank.gif" alt="[ICO]"></th><th><a href="?C=N;O=D">Name</a></th><th><a href="?C=M;O=A">Last modified</a></th><th><a href="?C=S;O=A">Size</a></th><th><a href="?C=D;O=A">Description</a></th></tr>
<tr><th colspan="5"><hr></th></tr>
<tr><td valign="top"><img src="/icons/back.gif" alt="[PARENTDIR]"></td><td><a href="/">Parent Directory</a></td><td>&nbsp;</td><td align="right">  - </td><td>&nbsp;</td></tr>
<tr><td valign="top"><img src="/icons/text.gif" alt="[TXT]"></td><td><a href="README">README</a></td><td align="right">2020-01-27 15:34  </td><td align="right">270 </td><td>&nbsp;</td></tr>
<tr><td valign="top"><img src="/icons/folder.gif" alt="[DIR]"></td><td><a href="training-monolingual/">training-monolingual/</a></td><td align="right">2020-01-27 15:30  </td><td align="right">  - </td><td>&nbsp;</td></tr>
<tr><td valign="top"><img src="/icons/folder.gif" alt="[DIR]"></td><td><a href="training/">training/</a></td><td align="right">2024-05-27 11:34  </td><td align="right">  - </td><td>&nbsp;</td></tr>
<tr><th colspan="5"><hr></th></tr>
</table>
</body>
</html>
"""

SAMPLE_HTML_MONOLINGUAL = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
<head>
<title>Index of /europarl/v10/training-monolingual</title>
</head>
<body>
<h1>Index of /europarl/v10/training-monolingual</h1>
<table>
<tr><th valign="top"><img src="/icons/blank.gif" alt="[ICO]"></th><th><a href="?C=N;O=D">Name</a></th><th><a href="?C=M;O=A">Last modified</a></th><th><a href="?C=S;O=A">Size</a></th><th><a href="?C=D;O=A">Description</a></th></tr>
<tr><th colspan="5"><hr></th></tr>
<tr><td valign="top"><img src="/icons/back.gif" alt="[PARENTDIR]"></td><td><a href="/europarl/v10/">Parent Directory</a></td><td>&nbsp;</td><td align="right">  - </td><td>&nbsp;</td></tr>
<tr><td valign="top"><img src="/icons/compressed.gif" alt="[   ]"></td><td><a href="europarl-v10.cs.tsv.gz">europarl-v10.cs.tsv.gz</a></td><td align="right">2020-01-27 15:30  </td><td align="right"> 36M</td><td>&nbsp;</td></tr>
<tr><td valign="top"><img src="/icons/compressed.gif" alt="[   ]"></td><td><a href="europarl-v10.de.tsv.gz">europarl-v10.de.tsv.gz</a></td><td align="right">2020-01-27 15:30  </td><td align="right">111M</td><td>&nbsp;</td></tr>
<tr><td valign="top"><img src="/icons/compressed.gif" alt="[   ]"></td><td><a href="europarl-v10.en.tsv.gz">europarl-v10.en.tsv.gz</a></td><td align="right">2020-01-27 15:30  </td><td align="right">113M</td><td>&nbsp;</td></tr>
<tr><th colspan="5"><hr></th></tr>
</table>
</body>
</html>
"""

# 파서 테스트 클래스
@pytest.fixture
def mock_response():
    """테스트를 위한 httpx 응답 모의 객체를 반환합니다."""
    mock = MagicMock()
    mock.text = SAMPLE_HTML
    mock.raise_for_status = MagicMock()
    return mock

@pytest.fixture
def mock_monolingual_response():
    """monolingual 디렉토리를 위한 httpx 응답 모의 객체를 반환합니다."""
    mock = MagicMock()
    mock.text = SAMPLE_HTML_MONOLINGUAL
    mock.raise_for_status = MagicMock()
    return mock

@pytest.fixture
def parser():
    """테스트를 위한 ApacheHttpServerParser 인스턴스를 반환합니다."""
    return ApacheHttpServerParser("https://www.statmt.org/europarl/v10/")

class TestApacheHttpServerParser:
    """ApacheHttpServerParser 클래스의 단위 테스트"""

    def test_init(self):
        """초기화 테스트"""
        parser = ApacheHttpServerParser("https://example.com", max_retries=5, retry_delay=2.0)
        assert parser.url == "https://example.com"
        assert parser.max_retries == 5
        assert parser.retry_delay == 2.0

    @patch("httpx.get")
    def test_fetch(self, mock_get, parser, mock_response):
        """fetch 메서드 테스트"""
        mock_get.return_value = mock_response
        result = parser.fetch()
        
        mock_get.assert_called_once_with(
            "https://www.statmt.org/europarl/v10/", 
            follow_redirects=True, 
            timeout=30.0
        )
        assert result == SAMPLE_HTML

    @patch("httpx.get")
    def test_fetch_retry(self, mock_get, parser):
        """fetch 메서드의 재시도 테스트"""
        # 첫 번째 호출에서 예외 발생, 두 번째는 성공
        mock_get.side_effect = [
            httpx.HTTPError("Error"),
            MagicMock(text=SAMPLE_HTML, raise_for_status=MagicMock())
        ]
        
        with patch("time.sleep") as mock_sleep:  # sleep 시간 건너뛰기
            result = parser.fetch()
        
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once_with(parser.retry_delay)
        assert result == SAMPLE_HTML

    @patch("httpx.get")
    def test_fetch_max_retries_exceeded(self, mock_get, parser):
        """최대 재시도 횟수 초과 테스트"""
        mock_get.side_effect = httpx.HTTPError("Error")
        
        with patch("time.sleep") as mock_sleep:  # sleep 시간 건너뛰기
            with pytest.raises(httpx.HTTPError):
                parser.fetch()
        
        assert mock_get.call_count == parser.max_retries
        assert mock_sleep.call_count == parser.max_retries - 1  # 마지막 재시도 후에는 sleep 없음

    @patch.object(ApacheHttpServerParser, "fetch")
    def test_parse(self, mock_fetch, parser):
        """parse 메서드 테스트"""
        mock_fetch.return_value = SAMPLE_HTML
        result = parser.parse()
        
        assert isinstance(result, list)
        assert len(result) == 3  # README와 두 개의 디렉토리
        
        # 파일 항목 검증
        assert result[0].filename == "README"
        assert result[0].type == "file"
        assert result[0].size == "270"
        assert result[0].last_modified == "2020-01-27 15:34"
        
        # 디렉토리 항목 검증
        assert result[1].filename == "training-monolingual/"
        assert result[1].type == "directory"
        assert result[1].size == "-"
        
        # URL 확인
        assert result[0].url.endswith("/README")
        assert result[1].url.endswith("/training-monolingual/")

    @pytest.mark.asyncio
    async def test_walk_depth_limit(self, parser):
        """walk 메서드의 깊이 제한 테스트"""
        # 최대 깊이 0으로 설정
        async for _ in parser.walk(max_depth=0):
            pytest.fail("최대 깊이가 0이면 아무 항목도 생성되지 않아야 합니다.")

    @pytest.mark.asyncio
    @patch.object(ApacheHttpServerParser, "parse")
    async def test_walk_with_pattern(self, mock_parse, parser):
        """walk 메서드의 패턴 필터링 테스트"""
        # 모의 결과 설정
        mock_parse.return_value = [
            FileSystemEntry(url="https://example.com/file1.txt", filename="file1.txt", type="file"),
            FileSystemEntry(url="https://example.com/file2.csv", filename="file2.csv", type="file"),
            FileSystemEntry(url="https://example.com/dir/", filename="dir/", type="directory")
        ]
        
        # "*.txt" 패턴으로 필터링
        results = []
        async for entry in parser.walk(glob_pattern="*.txt", max_depth=1):
            results.append(entry)
        
        assert len(results) == 1
        assert results[0].filename == "file1.txt"

    @pytest.mark.asyncio
    async def test_walk_avoid_cycles(self, parser):
        """walk 메서드의 무한 루프 방지 테스트"""
        # 동일한 URL을 두 번 방문하면 두 번째 방문에서는 아무 것도 생성하지 않아야 함
        visited_urls = {parser.url}
        
        async for _ in parser.walk(visited_urls=visited_urls):
            pytest.fail("이미 방문한 URL은 다시 방문하지 않아야 합니다.")


# 통합 테스트
class TestApacheHttpServerParserIntegration:
    """ApacheHttpServerParser 클래스의 통합 테스트"""
    
    @pytest.mark.asyncio
    @patch("httpx.get")
    async def test_walk_integration(self, mock_get, mock_response, mock_monolingual_response):
        """walk 메서드의 통합 테스트 - 재귀적 탐색 테스트"""
        # URL에 따라 다른 응답 반환
        def get_response(url, **kwargs):
            if url == "https://www.statmt.org/europarl/v10/":
                return mock_response
            elif url == "https://www.statmt.org/europarl/v10/training-monolingual/":
                return mock_monolingual_response
            return MagicMock(text="", raise_for_status=MagicMock())
            
        mock_get.side_effect = get_response
        
        parser = ApacheHttpServerParser("https://www.statmt.org/europarl/v10/")
        
        # 모든 파일 수집
        results = []
        async for entry in parser.walk(max_depth=2):
            results.append(entry)
        
        # 기대 결과 확인
        assert len(results) >= 3  # 최소한 README와 두 개의 디렉토리 항목
        
        # 파일타입 확인
        files = [entry for entry in results if entry.type == "file"]
        directories = [entry for entry in results if entry.type == "directory"]
        
        assert len(files) >= 1  # 최소한 README
        assert len(directories) >= 2  # 최소한 두 개의 디렉토리
        
        # 특정 파일 확인
        readme = next((f for f in files if f.filename == "README"), None)
        assert readme is not None
        assert readme.size == "270"

    @pytest.mark.asyncio
    @patch("httpx.get")
    async def test_walk_with_pattern_integration(self, mock_get, mock_response, mock_monolingual_response):
        """특정 패턴을 사용하는 walk 메서드의 통합 테스트"""
        # URL에 따라 다른 응답 반환
        def get_response(url, **kwargs):
            if url == "https://www.statmt.org/europarl/v10/":
                return mock_response
            elif url == "https://www.statmt.org/europarl/v10/training-monolingual/":
                return mock_monolingual_response
            return MagicMock(text="", raise_for_status=MagicMock())
            
        mock_get.side_effect = get_response
        
        parser = ApacheHttpServerParser("https://www.statmt.org/europarl/v10/")
        
        # "*.tsv.gz" 패턴으로 필터링
        results = []
        async for entry in parser.walk(glob_pattern="*.tsv.gz", max_depth=2):
            results.append(entry)
        
        # 결과 검증
        assert len(results) >= 3  # monolingual 디렉토리의 3개 파일
        assert all(entry.filename.endswith(".tsv.gz") for entry in results)
        
        # 특정 파일 존재 확인
        de_file = next((f for f in results if f.filename == "europarl-v10.de.tsv.gz"), None)
        assert de_file is not None
        assert de_file.size == "111M"


# 크롤링 및 표시 함수 테스트
class TestCrawlAndDisplay:
    """crawl_and_display 함수의 테스트"""
    
    @pytest.mark.asyncio
    @patch("httpx.get")
    @patch("rich.console.Console.print")
    @patch("rich.console.Console.status")
    async def test_crawl_and_display(self, mock_status, mock_print, mock_get, mock_response, mock_monolingual_response):
        """crawl_and_display 함수 테스트"""
        # Mock 설정
        mock_context = MagicMock(__enter__=MagicMock(), __exit__=MagicMock())
        mock_status.return_value = mock_context
        
        # URL에 따라 다른 응답 반환
        def get_response(url, **kwargs):
            if url == "https://www.statmt.org/europarl/v10/":
                return mock_response
            elif url == "https://www.statmt.org/europarl/v10/training-monolingual/":
                return mock_monolingual_response
            return MagicMock(text="", raise_for_status=MagicMock())
            
        mock_get.side_effect = get_response
        
        # 함수 실행
        result = await crawl_and_display(
            url="https://www.statmt.org/europarl/v10/",
            pattern="*.tsv.gz",
            max_depth=2,
            max_display=10,
            output_format="list",
            save_to_file=None
        )
        
        # 결과 검증
        assert isinstance(result, dict)
        assert "total_entries" in result
        assert "file_count" in result
        assert "dir_count" in result
        assert "duration" in result
        assert "entries" in result
        
        assert result["total_entries"] >= 3
        assert result["file_count"] >= 3
        assert all(entry.filename.endswith(".tsv.gz") for entry in result["entries"])
        
    @pytest.mark.asyncio
    @patch("httpx.get")
    @patch("rich.console.Console.print")
    @patch("builtins.open", new_callable=MagicMock)
    async def test_crawl_and_display_with_file_saving(self, mock_open, mock_print, mock_get, mock_response, mock_monolingual_response):
        """파일 저장 기능 테스트"""
        # URL에 따라 다른 응답 반환
        def get_response(url, **kwargs):
            if url == "https://www.statmt.org/europarl/v10/":
                return mock_response
            elif url == "https://www.statmt.org/europarl/v10/training-monolingual/":
                return mock_monolingual_response
            return MagicMock(text="", raise_for_status=MagicMock())
            
        mock_get.side_effect = get_response
        
        # Mock 파일 핸들
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # 함수 실행
        result = await crawl_and_display(
            url="https://www.statmt.org/europarl/v10/",
            pattern="*.tsv.gz",
            max_depth=2,
            max_display=10,
            output_format="list",
            save_to_file="test_results.md"
        )
        
        # 파일 저장 검증
        mock_open.assert_called_once_with("test_results.md", 'w', encoding='utf-8')
        assert mock_file.write.call_count > 0
        
        # 결과 검증
        assert result["total_entries"] >= 3
        assert result["file_count"] >= 3


# 결함 테스트 (edge cases)
class TestEdgeCases:
    """경계 조건 및 오류 처리 테스트"""
    
    @pytest.mark.asyncio
    @patch.object(ApacheHttpServerParser, "parse")
    async def test_walk_empty_directory(self, mock_parse, parser):
        """빈 디렉토리 탐색 테스트"""
        mock_parse.return_value = []  # 빈 디렉토리
        
        results = []
        async for entry in parser.walk():
            results.append(entry)
            
        assert len(results) == 0  # 아무 결과도 없어야 함
    
    @pytest.mark.asyncio
    @patch.object(ApacheHttpServerParser, "parse")
    async def test_walk_with_parse_error(self, mock_parse, parser):
        """파싱 오류 발생 시 처리 테스트"""
        mock_parse.side_effect = Exception("파싱 오류")
        
        results = []
        async for entry in parser.walk():
            results.append(entry)
            
        assert len(results) == 0  # 오류 발생 시 아무 결과도 없어야 함


if __name__ == "__main__":
    pytest.main(["-vsx", __file__]) 