"""
유틸리티 함수 - statmt 데이터셋 다운로드 및 처리를 위한 유틸리티 함수
"""

import os
import gzip
import shutil
import tarfile
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

def extract_archive(archive_path: str, extract_dir: Optional[str] = None) -> str:
    """
    아카이브 파일(tar.gz, tgz, gz 등) 압축 해제
    
    Args:
        archive_path: 압축 파일 경로
        extract_dir: 압축 해제 디렉토리 (기본값: 압축 파일과 동일한 디렉토리)
    
    Returns:
        압축 해제된 디렉토리 경로
    """
    if not os.path.exists(archive_path):
        raise FileNotFoundError(f"파일을 찾을 수 없음: {archive_path}")
    
    # 압축 해제 디렉토리 결정
    if extract_dir is None:
        extract_dir = os.path.dirname(archive_path)
    
    os.makedirs(extract_dir, exist_ok=True)
    
    # 파일 확장자에 따라 다른 압축 해제 메서드 사용
    filename = os.path.basename(archive_path)
    
    logger.info(f"압축 해제 중: {archive_path} -> {extract_dir}")
    
    if filename.endswith(".tar.gz") or filename.endswith(".tgz"):
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=extract_dir)
    
    elif filename.endswith(".gz"):
        # .gz 파일은 단일 파일을 압축한 형식
        output_filename = os.path.splitext(filename)[0]
        output_path = os.path.join(extract_dir, output_filename)
        
        with gzip.open(archive_path, "rb") as f_in:
            with open(output_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    else:
        raise ValueError(f"지원되지 않는 아카이브 형식: {filename}")
    
    logger.info(f"압축 해제 완료: {extract_dir}")
    return extract_dir

def get_language_pairs(dataset_id: str, metadata: Dict) -> List[str]:
    """
    지정된 데이터셋에서 사용 가능한 언어 쌍 목록 가져오기
    
    Args:
        dataset_id: 데이터셋 ID
        metadata: 데이터셋 메타데이터
    
    Returns:
        언어 쌍 목록 (예: ["de-en", "fr-en"])
    """
    if dataset_id not in metadata["datasets"]:
        return []
    
    dataset_info = metadata["datasets"][dataset_id]
    return dataset_info.get("language_pairs", [])

def list_files_in_directory(directory: str, pattern: Optional[str] = None) -> List[str]:
    """
    디렉토리 내 파일 목록 반환
    
    Args:
        directory: 대상 디렉토리
        pattern: 검색 패턴 (선택 사항)
    
    Returns:
        파일 경로 목록
    """
    if not os.path.exists(directory):
        return []
    
    path = Path(directory)
    
    if pattern:
        return [str(f) for f in path.glob(pattern)]
    else:
        return [str(f) for f in path.glob("*") if f.is_file()]

def compute_file_checksum(file_path: str) -> str:
    """
    파일의 체크섬(MD5) 계산
    
    Args:
        file_path: 파일 경로
    
    Returns:
        MD5 체크섬 문자열
    """
    import hashlib
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없음: {file_path}")
    
    md5 = hashlib.md5()
    
    with open(file_path, "rb") as f:
        # 대용량 파일을 위한 청크 단위 읽기
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    
    return md5.hexdigest() 