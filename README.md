# statmt-downloader

statmt.org에 호스팅된 다양한 기계 번역 데이터셋을 쉽게 다운로드할 수 있는 파이썬 라이브러리입니다.

## 특징

- 전략 패턴을 사용한 데이터셋별 크롤링 전략
- 다중 파일 동시 다운로드 지원
- 캐싱 및 메타데이터 관리
- 다양한 데이터셋 지원 (Europarl, News Commentary, UN Corpus, WMT 등)
- 명령줄 인터페이스 제공

## 설치 방법

```bash
pip install statmt-downloader
```

## 사용 방법

### Python API

#### 단일 데이터셋 다운로드

```python
from statmt_downloader import StatMTDownloader

# 다운로더 인스턴스 생성
downloader = StatMTDownloader()

# 사용 가능한 데이터셋 목록 보기
datasets = downloader.list_datasets()
print(datasets)

# 특정 데이터셋 다운로드
downloader.download(
    dataset_id='europarl-v7', 
    language_pair='de-en',
    target_dir='./data'
)
```

#### 여러 데이터셋 동시 다운로드

```python
from statmt_downloader import StatMTDownloader

# 다운로더 인스턴스 생성 (최대 8개의 파일을 동시에 다운로드)
downloader = StatMTDownloader(max_workers=8)

# 여러 데이터셋 구성
datasets = [
    {
        "dataset_id": "europarl-v7",
        "language_pair": "de-en",
        "target_dir": "europarl/de-en"
    },
    {
        "dataset_id": "news-commentary-v15",
        "language_pair": "de-en",
        "target_dir": "news-commentary/de-en"
    }
]

# 여러 데이터셋 동시 다운로드
results = downloader.download_multiple(
    dataset_configs=datasets,
    parent_dir='./data',
    auto_extract=True
)

# 결과 출력
for dataset_id, files in results.items():
    print(f"{dataset_id}: {len(files)}개 파일 다운로드됨")
```

### 명령줄 인터페이스

#### 데이터셋 목록 보기

```bash
statmt-downloader list
```

#### 단일 데이터셋 다운로드

```bash
# Europarl 데이터셋 다운로드
statmt-downloader download europarl-v7 --language-pair de-en --output-dir ./data

# WMT 데이터셋의 특정 카테고리 다운로드
statmt-downloader download wmt14 --category training-parallel --output-dir ./data

# 다운로드 후 자동 압축 해제
statmt-downloader download un-corpus-v1.0 --output-dir ./data --extract
```

#### 여러 데이터셋 배치 다운로드

배치 구성 파일 예시 (JSON):

```json
{
  "datasets": [
    {
      "dataset_id": "europarl-v7",
      "language_pair": "de-en",
      "target_dir": "europarl/de-en"
    },
    {
      "dataset_id": "news-commentary-v15",
      "language_pair": "de-en",
      "target_dir": "news-commentary/de-en"
    }
  ]
}
```

배치 다운로드 실행:

```bash
statmt-downloader batch config.json --output-dir ./data --extract
```

#### 캐시 관리

```bash
# 캐시 정보 표시
statmt-downloader cache --show
```

## 지원하는 데이터셋

- **Europarl**: 유럽 의회 병렬 코퍼스 (v7)
- **News Commentary**: 뉴스 주석 병렬 코퍼스 (v15)
- **UN Parallel Corpus**: 유엔 병렬 코퍼스 (v1.0)
- **WMT 데이터셋**: 각 연도별 WMT 데이터셋 (기본값: WMT14)

## 확장하기

새로운 데이터셋 크롤러를 추가하려면 `CrawlerStrategy` 인터페이스를 구현하고 `CrawlerFactory`에 등록하면 됩니다:

```python
from statmt_downloader.crawler import CrawlerStrategy

class MyCustomCrawler(CrawlerStrategy):
    def get_dataset_urls(self, **kwargs):
        # 사용자 정의 크롤링 로직
        return [
            {"url": "http://example.com/data.tgz", "filename": "data.tgz"}
        ]

# CrawlerFactory에 등록
from statmt_downloader.crawler import CrawlerFactory
CrawlerFactory.CRAWLERS["my-dataset"] = MyCustomCrawler
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 다운로드된 각 데이터셋은 원본 데이터셋의 라이선스를 따릅니다.
