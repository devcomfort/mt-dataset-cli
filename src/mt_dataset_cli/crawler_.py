"""
StatMT 크롤러 - 데이터셋 정보를 크롤링하기 위한 전략 패턴 구현
"""

import os
import re
import abc
import logging
from typing import Dict, List, Optional, Union
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class CrawlerStrategy(abc.ABC):
    """
    데이터셋 크롤링을 위한 전략 인터페이스
    """
    
    @abc.abstractmethod
    def get_dataset_urls(self, **kwargs) -> List[Dict[str, str]]:
        """
        데이터셋 URL 목록 가져오기
        
        Returns:
            URL 정보 목록 (예: [{"url": "http://...", "filename": "data.tgz", "description": "..."}])
        """
        pass

class EuroparlCrawler(CrawlerStrategy):
    """Europarl 데이터셋을 위한 크롤러 전략"""
    
    BASE_URL = "http://statmt.org/europarl/"
    
    def __init__(self, version: str = "v7"):
        self.version = version
        self.base_url = f"{self.BASE_URL}{version}/"
    
    def get_dataset_urls(self, language_pair: Optional[str] = None, **kwargs) -> List[Dict[str, str]]:
        """
        유로파를 데이터셋 URL 목록 가져오기
        
        Args:
            language_pair: 언어 쌍 (예: "de-en")
            
        Returns:
            URL 정보 목록
        """
        # 메인 페이지 크롤링
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            
            urls = []
            
            # 링크 찾기
            for link in soup.find_all("a"):
                href = link.get("href")
                if not href:
                    continue
                
                # 특정 언어 쌍이 지정된 경우 필터링
                if language_pair and language_pair not in href:
                    continue
                
                if href.endswith(".tgz") and "-train" in href:
                    # 예: fr-en-train.tgz
                    lp = href.split("-train")[0]
                    urls.append({
                        "url": f"{self.base_url}{href}",
                        "filename": href,
                        "language_pair": lp,
                        "description": f"Europarl {self.version} {lp} 말뭉치"
                    })
            
            return urls
            
        except Exception as e:
            logger.error(f"Europarl 데이터셋 크롤링 중 오류 발생: {e}")
            return []

class NewsCommentaryCrawler(CrawlerStrategy):
    """News Commentary 데이터셋을 위한 크롤러 전략"""
    
    BASE_URL = "http://data.statmt.org/news-commentary/"
    
    def __init__(self, version: str = "v15"):
        self.version = version
        self.base_url = f"{self.BASE_URL}{version}/training/"
    
    def get_dataset_urls(self, language_pair: Optional[str] = None, **kwargs) -> List[Dict[str, str]]:
        """
        News Commentary 데이터셋 URL 목록 가져오기
        
        Args:
            language_pair: 언어 쌍 (예: "de-en")
            
        Returns:
            URL 정보 목록
        """
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            
            urls = []
            
            # 링크 찾기
            for link in soup.find_all("a"):
                href = link.get("href")
                if not href:
                    continue
                
                if not href.startswith(f"news-commentary-{self.version}"):
                    continue
                
                if href.endswith(".tsv.gz") or href.endswith(".tsv"):
                    # 파일명에서 언어 쌍 추출
                    match = re.search(r'\.([a-z]{2}-[a-z]{2})\.(tsv|tsv\.gz)$', href)
                    if match:
                        lp = match.group(1)
                        
                        # 특정 언어 쌍이 지정된 경우 필터링
                        if language_pair and language_pair != lp:
                            continue
                        
                        urls.append({
                            "url": f"{self.base_url}{href}",
                            "filename": href,
                            "language_pair": lp,
                            "description": f"News Commentary {self.version} {lp} 말뭉치"
                        })
            
            return urls
            
        except Exception as e:
            logger.error(f"News Commentary 데이터셋 크롤링 중 오류 발생: {e}")
            return []

class WMTCrawler(CrawlerStrategy):
    """WMT 데이터셋을 위한 크롤러 전략"""
    
    BASE_URL = "http://statmt.org/wmt{year}/"
    
    def __init__(self, year: str = "14"):
        self.year = year
        self.base_url = self.BASE_URL.format(year=year)
    
    def get_dataset_urls(self, category: Optional[str] = None, **kwargs) -> List[Dict[str, str]]:
        """
        WMT 데이터셋 URL 목록 가져오기
        
        Args:
            category: 데이터셋 카테고리 (예: "training-parallel", "test")
            
        Returns:
            URL 정보 목록
        """
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            
            urls = []
            
            # 먼저 카테고리 링크 찾기
            category_links = {}
            for link in soup.find_all("a"):
                href = link.get("href")
                if not href:
                    continue
                
                # 카테고리 링크 확인
                if category and category in href:
                    category_links[category] = f"{self.base_url}{href}"
                elif not category and any(x in href for x in ["training", "test", "dev"]):
                    cat = href.rstrip("/")
                    category_links[cat] = f"{self.base_url}{href}"
            
            # 각 카테고리 페이지에서 데이터셋 파일 링크 찾기
            for cat, cat_url in category_links.items():
                try:
                    cat_response = requests.get(cat_url)
                    cat_response.raise_for_status()
                    cat_soup = BeautifulSoup(cat_response.text, "lxml")
                    
                    for link in cat_soup.find_all("a"):
                        href = link.get("href")
                        if not href:
                            continue
                        
                        if href.endswith((".tgz", ".gz", ".tar.gz", ".zip")):
                            urls.append({
                                "url": f"{cat_url.rstrip('/')}/{href}",
                                "filename": href,
                                "category": cat,
                                "description": f"WMT{self.year} {cat} 데이터셋 - {href}"
                            })
                
                except Exception as e:
                    logger.warning(f"WMT{self.year} {cat} 카테고리 크롤링 중 오류 발생: {e}")
            
            return urls
            
        except Exception as e:
            logger.error(f"WMT{self.year} 데이터셋 크롤링 중 오류 발생: {e}")
            return []

class UNCrawler(CrawlerStrategy):
    """UN 병렬 코퍼스를 위한 크롤러 전략"""
    
    BASE_URL = "http://statmt.org/wmt13/training-parallel-un-v1.0.tgz"
    
    def get_dataset_urls(self, **kwargs) -> List[Dict[str, str]]:
        """
        UN 병렬 코퍼스 URL 가져오기
        
        Returns:
            URL 정보 목록
        """
        return [{
            "url": self.BASE_URL,
            "filename": "training-parallel-un-v1.0.tgz",
            "description": "UN 병렬 코퍼스 v1.0"
        }]

class CrawlerFactory:
    """크롤러 전략 팩토리"""
    
    CRAWLERS = {
        "europarl": EuroparlCrawler,
        "news-commentary": NewsCommentaryCrawler,
        "wmt": WMTCrawler,
        "un-corpus": UNCrawler
    }
    
    @classmethod
    def get_crawler(cls, dataset_id: str) -> CrawlerStrategy:
        """
        데이터셋 ID에 맞는 크롤러 전략 인스턴스 반환
        
        Args:
            dataset_id: 데이터셋 ID (예: "europarl-v7", "wmt14")
            
        Returns:
            크롤러 전략 인스턴스
        """
        for prefix, crawler_class in cls.CRAWLERS.items():
            if dataset_id.startswith(prefix):
                # 버전 또는 연도 추출
                version_match = re.search(r'[vV]?(\d+)$', dataset_id)
                year_match = re.search(r'(\d+)$', dataset_id)
                
                if version_match and prefix != "wmt":
                    version = f"v{version_match.group(1)}"
                    return crawler_class(version=version)
                elif year_match and prefix == "wmt":
                    year = year_match.group(1)
                    return crawler_class(year=year)
                else:
                    return crawler_class()
        
        raise ValueError(f"지원되지 않는 데이터셋 ID: {dataset_id}") 