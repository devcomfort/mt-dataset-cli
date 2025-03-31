"""
Apache HTTP Server API 테스트 모듈

pytest를 사용하여 Apache HTTP Server API 함수들을 테스트합니다.
"""
import pytest
import os
import sys
import asyncio
from unittest.mock import MagicMock, patch

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.mt_dataset_downloader.crawler.apache_http_server_api import (
    crawl_apache_http_server,
    crawl_apache_http_server_sync
)

# 테스트 클래스
class TestApacheHttpServerApi:
    """Apache HTTP Server API 함수들의 단위 테스트"""

    @pytest.mark.asyncio
    async def test_crawl_apache_http_server_invalid_format(self):
        """유효하지 않은 출력 형식으로 크롤링 함수 테스트"""
        with pytest.raises(ValueError) as excinfo:
            await crawl_apache_http_server(output_format="invalid")
        
        # 오류 메시지 확인
        assert "유효하지 않은 출력 형식" in str(excinfo.value)
        assert "invalid" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_crawl_apache_http_server_invalid_depth(self):
        """유효하지 않은 최대 깊이로 크롤링 함수 테스트"""
        with pytest.raises(ValueError) as excinfo:
            await crawl_apache_http_server(max_depth=11)
        
        # 오류 메시지 확인
        assert "유효하지 않은 최대 깊이" in str(excinfo.value)
        assert "11" in str(excinfo.value)

    @pytest.mark.asyncio
    @patch("src.mt_dataset_downloader.crawler.apache_http_server_api.crawl_and_display")
    async def test_crawl_apache_http_server_parameters(self, mock_crawl_and_display):
        """crawl_apache_http_server 함수의 매개변수 테스트"""
        # 모의 반환 값 설정
        mock_result = {
            "total_entries": 10,
            "file_count": 8,
            "dir_count": 2,
            "duration": 1.5,
            "entries": []
        }
        mock_crawl_and_display.return_value = mock_result
        
        # 함수 호출
        result = await crawl_apache_http_server(
            url="https://example.com",
            pattern="*.txt",
            max_depth=3,
            max_display=20,
            output_format="list",
            save_to_file="output.md"
        )
        
        # 매개변수가 올바르게 전달되었는지 확인
        mock_crawl_and_display.assert_called_once_with(
            url="https://example.com",
            pattern="*.txt",
            max_depth=3,
            max_display=20,
            output_format="list",
            save_to_file="output.md"
        )
        
        # 반환 값 확인
        assert result == mock_result

    @patch("asyncio.run")
    def test_crawl_apache_http_server_sync(self, mock_run):
        """crawl_apache_http_server_sync 함수 테스트"""
        # 모의 반환 값 설정
        mock_result = {
            "total_entries": 10,
            "file_count": 8,
            "dir_count": 2,
            "duration": 1.5,
            "entries": []
        }
        mock_run.return_value = mock_result
        
        # 함수 호출
        result = crawl_apache_http_server_sync(
            url="https://example.com",
            pattern="*.txt",
            max_depth=3,
            max_display=20,
            output_format="list",
            save_to_file="output.md"
        )
        
        # asyncio.run이 올바른 매개변수로 호출되었는지 확인
        args, kwargs = mock_run.call_args
        assert len(args) == 1
        
        # 반환 값 확인
        assert result == mock_result 