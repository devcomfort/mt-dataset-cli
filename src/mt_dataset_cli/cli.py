"""
StatMT 다운로더 명령줄 인터페이스
"""

import os
import sys
import json
import argparse
import logging
from typing import List, Optional, Dict

from .downloader import StatMTDownloader
from .utils import extract_archive

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    명령줄 인수 파싱
    
    Args:
        args: 명령줄 인수 (기본값: sys.argv[1:])
    
    Returns:
        파싱된 인수 객체
    """
    parser = argparse.ArgumentParser(
        description="statmt.org에서 기계 번역 데이터셋 다운로드",
        epilog="예시: mt-dataset-cli download europarl-v7 --language-pair de-en --output-dir ./data"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="명령")
    
    # 데이터셋 목록 서브커맨드
    list_parser = subparsers.add_parser("list", help="사용 가능한 데이터셋 목록 표시")
    
    # 다운로드 서브커맨드
    download_parser = subparsers.add_parser("download", help="데이터셋 다운로드")
    download_parser.add_argument("dataset_id", help="다운로드할 데이터셋 ID")
    download_parser.add_argument("--language-pair", "-l", help="언어 쌍 (예: de-en)")
    download_parser.add_argument("--category", "-c", help="데이터 카테고리 (WMT 데이터셋용)")
    download_parser.add_argument("--output-dir", "-o", default="./data", help="출력 디렉토리 (기본값: ./data)")
    download_parser.add_argument("--force", "-f", action="store_true", help="기존 파일 덮어쓰기")
    download_parser.add_argument("--extract", "-e", action="store_true", help="다운로드 후 자동 압축 해제")
    download_parser.add_argument("--max-workers", "-w", type=int, default=4, help="최대 동시 다운로드 수 (기본값: 4)")
    
    # 여러 데이터셋 다운로드 서브커맨드
    batch_parser = subparsers.add_parser("batch", help="설정 파일을 사용하여 여러 데이터셋 다운로드")
    batch_parser.add_argument("config_file", help="데이터셋 구성 JSON 파일 경로")
    batch_parser.add_argument("--output-dir", "-o", default="./data", help="출력 디렉토리 (기본값: ./data)")
    batch_parser.add_argument("--force", "-f", action="store_true", help="기존 파일 덮어쓰기")
    batch_parser.add_argument("--extract", "-e", action="store_true", help="다운로드 후 자동 압축 해제")
    batch_parser.add_argument("--max-workers", "-w", type=int, default=4, help="최대 동시 다운로드 수 (기본값: 4)")
    
    # 캐시 관리 서브커맨드
    cache_parser = subparsers.add_parser("cache", help="캐시 관리")
    cache_parser.add_argument("--clear", action="store_true", help="캐시 비우기")
    cache_parser.add_argument("--show", action="store_true", help="캐시 정보 표시")
    
    return parser.parse_args(args)

def load_batch_config(config_path: str) -> List[Dict]:
    """
    배치 구성 파일 로드
    
    Args:
        config_path: 구성 파일 경로
        
    Returns:
        배치 구성 목록
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if isinstance(config, list):
            return config
        elif isinstance(config, dict) and "datasets" in config:
            return config["datasets"]
        else:
            raise ValueError("구성 파일은 데이터셋 배열 또는 'datasets' 키를 포함하는 객체여야 합니다.")
    
    except json.JSONDecodeError:
        raise ValueError("유효하지 않은 JSON 파일입니다.")
    except Exception as e:
        raise ValueError(f"구성 파일 로드 중 오류 발생: {e}")

def main(args: Optional[List[str]] = None) -> int:
    """
    메인 진입점
    
    Args:
        args: 명령줄 인수 (기본값: sys.argv[1:])
    
    Returns:
        종료 코드
    """
    parsed_args = parse_args(args)
    
    if not parsed_args.command:
        print("명령어를 지정해주세요. 사용 가능한 명령어: list, download, batch, cache")
        return 1
    
    # 명령어에 따른 동작 수행
    if parsed_args.command == "list":
        # 다운로더 인스턴스 생성
        downloader = StatMTDownloader()
        datasets = downloader.list_datasets()
        
        print("\n사용 가능한 데이터셋:")
        print("=" * 80)
        
        for dataset in datasets:
            print(f"ID: {dataset['id']}")
            print(f"설명: {dataset.get('description', '설명 없음')}")
            
            if "language_pairs" in dataset:
                print(f"지원하는 언어 쌍: {', '.join(dataset['language_pairs'])}")
            
            if "categories" in dataset:
                print(f"지원하는 카테고리: {', '.join(dataset['categories'])}")
            
            print("-" * 80)
        
        return 0
    
    elif parsed_args.command == "download":
        try:
            # 다운로더 인스턴스 생성
            downloader = StatMTDownloader(max_workers=parsed_args.max_workers)
            
            # 데이터셋 다운로드
            result = downloader.download(
                dataset_id=parsed_args.dataset_id,
                target_dir=parsed_args.output_dir,
                language_pair=parsed_args.language_pair,
                category=parsed_args.category,
                auto_extract=parsed_args.extract,
                force=parsed_args.force
            )
            
            if isinstance(result, list):
                print(f"\n다운로드 완료: {len(result)}개 파일")
                for file_path in result:
                    print(f"  - {file_path}")
            else:
                print(f"\n다운로드 완료: {result}")
            
            return 0
        
        except Exception as e:
            logger.error(f"다운로드 중 오류 발생: {e}")
            return 1
    
    elif parsed_args.command == "batch":
        try:
            # 배치 구성 로드
            batch_config = load_batch_config(parsed_args.config_file)
            
            if not batch_config:
                logger.error("구성 파일에 데이터셋이 정의되지 않았습니다.")
                return 1
            
            # 다운로더 인스턴스 생성
            downloader = StatMTDownloader(max_workers=parsed_args.max_workers)
            
            # 여러 데이터셋 다운로드
            results = downloader.download_multiple(
                dataset_configs=batch_config,
                parent_dir=parsed_args.output_dir,
                auto_extract=parsed_args.extract,
                force=parsed_args.force
            )
            
            print("\n다운로드 완료 요약:")
            print("=" * 80)
            
            total_files = 0
            for dataset_id, files in results.items():
                print(f"{dataset_id}: {len(files)}개 파일")
                total_files += len(files)
            
            print("-" * 80)
            print(f"총계: {len(results)}개 데이터셋, {total_files}개 파일")
            
            return 0
            
        except Exception as e:
            logger.error(f"배치 다운로드 중 오류 발생: {e}")
            return 1
    
    elif parsed_args.command == "cache":
        # 다운로더 인스턴스 생성
        downloader = StatMTDownloader()
        
        if parsed_args.clear:
            # 캐시 비우기 로직 (구현 필요)
            print("캐시 비우기 기능은 아직 구현되지 않았습니다.")
            return 1
        
        elif parsed_args.show:
            # 캐시 정보 표시
            print(f"캐시 디렉토리: {downloader.downloader.cache_dir}")
            
            # 다운로드 정보 표시
            if "downloads" in downloader.metadata:
                downloads = downloader.metadata["downloads"]
                print(f"캐시된 다운로드: {len(downloads)}개")
                
                if downloads:
                    print("\n최근 다운로드:")
                    for i, (url, info) in enumerate(list(downloads.items())[:5]):
                        print(f"{i+1}. {os.path.basename(info['path'])} (URL: {url})")
            
            return 0
    
    # 명령어가 없거나 잘못된 경우
    print("명령어를 지정해주세요. 사용 가능한 명령어: list, download, batch, cache")
    return 1

if __name__ == "__main__":
    sys.exit(main()) 