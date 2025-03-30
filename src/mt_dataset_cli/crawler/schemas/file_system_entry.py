from dataclasses import dataclass

@dataclass
class FileSystemEntry:
    """웹 크롤링된 파일/디렉토리 요소를 나타내는 데이터 클래스
    
    Attributes:
        url: 파일/디렉토리의 URL
        size: 파일 크기 (문자열 형태, 예: "1.2MB")
        filename: 파일/디렉토리 이름
        last_modified: 마지막 수정 일자 (문자열 형태, 예: "2023-01-01 12:00:00")
        description: 파일/디렉토리 설명
    """
    url: str
    size: str 
    filename: str
    last_modified: str
    description: str