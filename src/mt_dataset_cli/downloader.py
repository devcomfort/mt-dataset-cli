"""
StatMT 다운로더 - statmt.org의 데이터셋을 다운로드하기 위한 기능 제공
"""

import os
import json
import logging
import threading
import concurrent.futures
from typing import Dict, List, Optional, Set, Tuple, Union, Callable
from pathlib import Path

import requests
from tqdm import tqdm

from .crawler import CrawlerFactory, CrawlerStrategy
from .utils import extract_archive

logger = logging.getLogger(__name__)

class Downloader:
    """파일 다운로드 클래스"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Downloader 초기화
        
        Args:
            cache_dir: 다운로드된 파일을 캐싱하는 디렉토리 (기본값: ~/.mt_dataset_cli/cache)
        """
        self.cache_dir = cache_dir or os.path.expanduser("~/.mt_dataset_cli/cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 메타데이터 캐시 파일 경로
        self.metadata_cache_file = os.path.join(self.cache_dir, "metadata.json")
        
        # 메타데이터 로드 또는 초기화
        self.metadata = self._load_metadata()
        
        # 스레드 Lock
        self.lock = threading.Lock()
    
    def _load_metadata(self) -> Dict:
        """메타데이터 캐시 파일에서 메타데이터 로드"""
        if os.path.exists(self.metadata_cache_file):
            try:
                with open(self.metadata_cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"메타데이터 로드 중 오류 발생: {e}")
                return {"downloads": {}, "datasets": {}}
        return {"downloads": {}, "datasets": {}}
    
    def _save_metadata(self):
        """메타데이터를 캐시 파일에 저장"""
        try:
            with self.lock:
                with open(self.metadata_cache_file, "w", encoding="utf-8") as f:
                    json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"메타데이터 저장 중 오류 발생: {e}")
    
    def download_file(self, url: str, target_dir: str, 
                    filename: Optional[str] = None, force: bool = False,
                    on_progress: Optional[Callable[[int, int], None]] = None) -> str:
        """
        단일 파일 다운로드
        
        Args:
            url: 다운로드할 파일 URL
            target_dir: 다운로드 대상 디렉토리
            filename: 저장할 파일명 (None인 경우 URL에서 추출)
            force: 이미 존재하는 파일도 강제로 다시 다운로드할지 여부
            on_progress: 진행률 콜백 함수 (current_size, total_size)
            
        Returns:
            다운로드된 파일 경로
        """
        # 파일명이 지정되지 않은 경우 URL에서 추출
        if filename is None:
            filename = os.path.basename(url)
        
        output_path = os.path.join(target_dir, filename)
        
        # 이미 파일이 존재하는 경우
        if os.path.exists(output_path) and not force:
            logger.info(f"파일이 이미 존재합니다: {output_path}")
            return output_path
        
        # 디렉토리 생성
        os.makedirs(target_dir, exist_ok=True)
        
        logger.info(f"다운로드 중: {url} -> {output_path}")
        
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))
                
                with open(output_path, "wb") as f, tqdm(
                    total=total_size, unit="B", unit_scale=True, desc=filename
                ) as progress_bar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            progress_bar.update(len(chunk))
                            
                            if on_progress:
                                on_progress(progress_bar.n, total_size)
            
            logger.info(f"다운로드 완료: {output_path}")
            
            # 메타데이터 업데이트
            with self.lock:
                if "downloads" not in self.metadata:
                    self.metadata["downloads"] = {}
                
                self.metadata["downloads"][url] = {
                    "path": output_path,
                    "timestamp": int(os.path.getmtime(output_path))
                }
                self._save_metadata()
            
            return output_path
            
        except Exception as e:
            logger.error(f"다운로드 중 오류 발생: {url} - {e}")
            # 다운로드 실패 시 부분적으로 다운로드된 파일 삭제
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            raise

class MultiDownloader:
    """여러 파일을 동시에 다운로드하기 위한 클래스"""
    
    def __init__(self, downloader: Downloader, max_workers: int = 4):
        """
        MultiDownloader 초기화
        
        Args:
            downloader: 다운로더 인스턴스
            max_workers: 최대 동시 다운로드 수
        """
        self.downloader = downloader
        self.max_workers = max_workers
    
    def download_all(self, download_list: List[Dict], parent_dir: str,
                    auto_extract: bool = False, force: bool = False) -> List[str]:
        """
        여러 파일 동시 다운로드
        
        Args:
            download_list: 다운로드할 파일 정보 목록 
                           [{"url": "...", "filename": "...", "target_dir": "..."}]
            parent_dir: 상위 다운로드 디렉토리
            auto_extract: 다운로드 후 자동 압축 해제 여부
            force: 이미 존재하는 파일도 강제 다운로드할지 여부
        
        Returns:
            다운로드된 파일 경로 목록
        """
        results = []
        completed_count = 0
        total_count = len(download_list)
        
        # 프로그레스 바 설정
        progress_bar = tqdm(total=total_count, desc="전체 다운로드 진행률")
        
        # 파일별 진행률 추적을 위한 딕셔너리
        file_progress = {}
        
        def update_progress(url, current, total):
            with self.downloader.lock:
                file_progress[url] = (current, total)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 다운로드 작업 제출
            future_to_url = {}
            
            for item in download_list:
                url = item["url"]
                filename = item.get("filename")
                
                # 디렉토리 경로 설정
                if "target_dir" in item and item["target_dir"]:
                    # 항목에 지정된 대상 디렉토리가 있는 경우
                    target_dir = os.path.join(parent_dir, item["target_dir"])
                else:
                    # 카테고리 또는 데이터셋 유형에 따라 디렉토리 구성
                    subdir = None
                    if "category" in item:
                        subdir = item["category"]
                    elif "language_pair" in item:
                        subdir = f"parallel/{item['language_pair']}"
                    else:
                        # 기본값: 파일명에서 확장자 제거한 값
                        subdir = os.path.splitext(filename)[0] if filename else ""
                    
                    target_dir = os.path.join(parent_dir, subdir)
                
                # 다운로드 작업 제출
                future = executor.submit(
                    self.downloader.download_file,
                    url=url,
                    target_dir=target_dir,
                    filename=filename,
                    force=force,
                    on_progress=lambda current, total, u=url: update_progress(u, current, total)
                )
                future_to_url[future] = (url, target_dir, filename)
            
            # 완료된 다운로드 처리
            for future in concurrent.futures.as_completed(future_to_url):
                url, target_dir, filename = future_to_url[future]
                
                try:
                    file_path = future.result()
                    results.append(file_path)
                    
                    # 압축 해제
                    if auto_extract and file_path.endswith((".tgz", ".gz", ".tar.gz", ".zip")):
                        try:
                            extract_dir = extract_archive(file_path, extract_dir=target_dir)
                            logger.info(f"압축 해제 완료: {file_path} -> {extract_dir}")
                        except Exception as e:
                            logger.error(f"압축 해제 중 오류 발생: {file_path} - {e}")
                    
                except Exception as e:
                    logger.error(f"다운로드 실패: {url} - {e}")
                
                completed_count += 1
                progress_bar.update(1)
        
        progress_bar.close()
        logger.info(f"총 {total_count}개 파일 중 {completed_count}개 다운로드 완료")
        
        return results

class StatMTDownloader:
    """statmt.org에서 데이터셋을 다운로드하기 위한 클래스"""
    
    def __init__(self, cache_dir: Optional[str] = None, max_workers: int = 4):
        """
        StatMTDownloader 초기화
        
        Args:
            cache_dir: 다운로드된 파일을 캐싱하는 디렉토리 (기본값: ~/.mt_dataset_cli/cache)
            max_workers: 최대 동시 다운로드 수
        """
        self.downloader = Downloader(cache_dir)
        self.multi_downloader = MultiDownloader(self.downloader, max_workers)
        
        # 메타데이터 캐시 참조
        self.metadata = self.downloader.metadata
    
    def list_datasets(self) -> List[Dict[str, str]]:
        """
        사용 가능한 데이터셋 목록 반환
        
        Returns:
            데이터셋 정보 리스트
        """
        return [
            {
                "id": "europarl-v7",
                "description": "Europarl v7 병렬 말뭉치",
                "language_pairs": ["de-en", "fr-en", "es-en", "en-fi", "en-cs"]
            },
            {
                "id": "news-commentary-v15",
                "description": "News Commentary v15",
                "language_pairs": ["de-en", "zh-en", "ru-en", "fr-en"]
            },
            {
                "id": "un-corpus-v1.0",
                "description": "UN 병렬 코퍼스 v1.0"
            },
            {
                "id": "wmt14",
                "description": "WMT14 데이터셋",
                "categories": ["training-monolingual", "training-parallel", "test"]
            },
            # 추가 데이터셋은 필요에 따라 확장 가능
        ]
    
    def download(self, dataset_id: str, target_dir: Optional[str] = None, 
                language_pair: Optional[str] = None, category: Optional[str] = None, 
                auto_extract: bool = False, force: bool = False) -> Union[str, List[str]]:
        """
        지정된 데이터셋 다운로드
        
        Args:
            dataset_id: 다운로드할 데이터셋 ID
            target_dir: 다운로드 대상 디렉토리 (기본값: 현재 디렉토리)
            language_pair: 언어 쌍 (예: de-en)
            category: 데이터 카테고리 (WMT 데이터셋용)
            auto_extract: 다운로드 후 자동 압축 해제 여부
            force: 이미 존재하는 파일도 강제 다운로드할지 여부
            
        Returns:
            다운로드된 파일 또는 파일 목록
        """
        # 기본 디렉토리 설정
        target_dir = target_dir or os.getcwd()
        os.makedirs(target_dir, exist_ok=True)
        
        # 크롤러 인스턴스 가져오기
        crawler = CrawlerFactory.get_crawler(dataset_id)
        
        # 데이터셋 URL 목록 가져오기
        kwargs = {}
        if language_pair:
            kwargs["language_pair"] = language_pair
        if category:
            kwargs["category"] = category
        
        dataset_urls = crawler.get_dataset_urls(**kwargs)
        
        if not dataset_urls:
            raise ValueError(f"다운로드할 URL을 찾을 수 없습니다: {dataset_id}")
        
        if len(dataset_urls) == 1:
            # 단일 파일인 경우
            url_info = dataset_urls[0]
            return self.downloader.download_file(
                url=url_info["url"],
                target_dir=target_dir,
                filename=url_info.get("filename"),
                force=force
            )
        else:
            # 여러 파일인 경우
            return self.multi_downloader.download_all(
                download_list=dataset_urls,
                parent_dir=target_dir,
                auto_extract=auto_extract,
                force=force
            )
    
    def download_multiple(self, dataset_configs: List[Dict], 
                         parent_dir: Optional[str] = None,
                         auto_extract: bool = False, 
                         force: bool = False) -> Dict[str, List[str]]:
        """
        여러 데이터셋 동시 다운로드
        
        Args:
            dataset_configs: 데이터셋 구성 목록
                [
                    {"dataset_id": "europarl-v7", "language_pair": "de-en"},
                    {"dataset_id": "wmt14", "category": "training-parallel"}
                ]
            parent_dir: 상위 다운로드 디렉토리 (기본값: 현재 디렉토리)
            auto_extract: 다운로드 후 자동 압축 해제 여부
            force: 이미 존재하는 파일도 강제 다운로드할지 여부
            
        Returns:
            데이터셋별 다운로드된 파일 목록 딕셔너리
        """
        # 기본 디렉토리 설정
        parent_dir = parent_dir or os.getcwd()
        os.makedirs(parent_dir, exist_ok=True)
        
        # 모든 데이터셋의 URL 수집
        all_urls = []
        dataset_to_urls = {}
        
        for config in dataset_configs:
            dataset_id = config["dataset_id"]
            crawler = CrawlerFactory.get_crawler(dataset_id)
            
            # 데이터셋별 특수 매개변수 처리
            kwargs = {k: v for k, v in config.items() if k not in ["dataset_id", "target_dir"]}
            
            # URL 목록 가져오기
            dataset_urls = crawler.get_dataset_urls(**kwargs)
            
            if dataset_urls:
                # 대상 디렉토리 처리
                target_subdir = config.get("target_dir", dataset_id)
                
                # URL 정보에 대상 디렉토리 추가
                for url_info in dataset_urls:
                    url_info["target_dir"] = target_subdir
                
                all_urls.extend(dataset_urls)
                dataset_to_urls[dataset_id] = dataset_urls
            else:
                logger.warning(f"다운로드할 URL을 찾을 수 없습니다: {dataset_id}")
        
        if not all_urls:
            raise ValueError("다운로드할 URL이 없습니다.")
        
        # 모든 URL 동시 다운로드
        downloaded_files = self.multi_downloader.download_all(
            download_list=all_urls,
            parent_dir=parent_dir,
            auto_extract=auto_extract,
            force=force
        )
        
        # 결과를 데이터셋별로 정리
        result = {}
        for dataset_id, urls in dataset_to_urls.items():
            url_set = {url_info["url"] for url_info in urls}
            result[dataset_id] = [
                f for f in downloaded_files
                if any(url in f for url in url_set)
            ]
        
        return result 