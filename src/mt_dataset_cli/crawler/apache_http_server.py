"""
Apache HTTP 서버 웹 페이지 파싱을 위한
모듈
"""

import httpx
import asyncio
import fnmatch
import time
import sys
import os
from functools import lru_cache
from bs4 import BeautifulSoup
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.tree import Tree
from rich import print as rprint

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.mt_dataset_cli.crawler.schemas import WebParser, FileSystemEntry

# Rich 콘솔 객체 생성
console = Console()

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

                type_ = "directory" if url.endswith('/') else "file"
                last_modified = cols[2].text.strip()
                size = cols[3].text.strip()
                description = cols[4].text.strip()
                
                element = FileSystemEntry(
                    url=url,
                    filename=filename,
                    last_modified=last_modified,
                    size=size,
                    description=description,
                    type=type_
                )
                elements.append(element)
                
        return elements

    async def walk(self, glob_pattern: str = None, visited_urls=None, depth=0, max_depth=5):
        """
        웹 페이지를 재귀적으로 탐색하여 모든 파일과 디렉토리를 반환합니다.
        
        Args:
            glob_pattern: 파일명 필터링을 위한 glob 패턴 (예: "*.txt", "data-*.tgz")
            visited_urls: 이미 방문한 URL 집합 (무한 루프 방지)
            depth: 현재 탐색 깊이
            max_depth: 최대 탐색 깊이
            
        Returns:
            비동기 제너레이터: 발견된 파일 또는 디렉토리 항목을 생성하는 비동기 제너레이터
        """
        # 방문한 URL 관리 (무한 루프 방지)
        if visited_urls is None:
            visited_urls = set()
        
        # 최대 깊이 제한 확인
        if depth > max_depth:
            return
            
        # 이미 방문한 URL 확인
        if self.url in visited_urls:
            return
            
        # 현재 URL 방문 처리
        visited_urls.add(self.url)
        
        try:
            # 현재 디렉토리에서 모든 요소 파싱
            elements = self.parse()
            
            # 필터링 함수
            def matches_pattern(filename):
                if not glob_pattern:
                    return True
                return fnmatch.fnmatch(filename, glob_pattern)
            
            # 일단 디렉토리를 한 번에 모아서 나중에 처리 (동시성 확보)
            directories = []
            
            # 파일 먼저 처리
            for element in elements:
                # 파일만 먼저 처리하고 매칭되는 것만 반환
                if element.type == "file" and matches_pattern(element.filename):
                    yield element
                elif element.type == "directory":
                    # 디렉토리 자체가 패턴에 매칭되면 반환
                    if matches_pattern(element.filename):
                        yield element
                    directories.append(element)
            
            # 디렉토리를 비동기적으로 병렬 처리
            if directories:
                tasks = []
                for dir_element in directories:
                    # 하위 디렉토리 탐색 작업 생성
                    parser = ApacheHttpServerParser(dir_element.url, max_retries=self.max_retries, retry_delay=self.retry_delay)
                    tasks.append(parser.walk(
                        glob_pattern=glob_pattern,
                        visited_urls=visited_urls,
                        depth=depth+1,
                        max_depth=max_depth
                    ))
                
                # 병렬로 모든 하위 디렉토리 탐색 (gather 사용)
                if tasks:
                    async_generators = await asyncio.gather(*[anext(task, None) for task in tasks])
                    
                    # 모든 제너레이터에서 항목 가져오기
                    for i, task in enumerate(tasks):
                        # 첫 번째 항목이 있으면 반환
                        if async_generators[i] is not None:
                            yield async_generators[i]
                        
                        # 나머지 항목들 반환
                        try:
                            async for item in task:
                                yield item
                        except Exception as e:
                            console.print(f"[bold red][오류][/] 하위 디렉토리 탐색 중 오류 발생: {e}")
                    
        except Exception as e:
            console.print(f"[bold red][오류][/] URL '{self.url}' 탐색 중 오류 발생: {e}")

# Typer 앱 생성
app = typer.Typer(
    help="Apache HTTP Server 디렉토리 크롤러",
    add_completion=False,
)

async def crawl_and_display(url: str, pattern: str, max_depth: int, max_display: int, 
                            output_format: str, save_to_file: Optional[str] = None):
    """크롤링 및 결과 표시 함수"""
    # 크롤러 인스턴스 생성
    http_parser = ApacheHttpServerParser(url)
    
    # 루트 링크 가져오기
    with console.status("[bold green]루트 디렉토리 분석 중...[/]", spinner="dots"):
        links = http_parser.parse()
    
    # 루트 링크 표시
    console.print(Panel(
        f"[bold]루트 디렉토리에서 발견된 링크 수: {len(links)}[/]", 
        title="[green]루트 디렉토리[/]", 
        border_style="green"
    ))
    
    # 링크 테이블 생성
    table = Table(title="루트 디렉토리 항목")
    table.add_column("파일/디렉토리", style="cyan")
    table.add_column("타입", style="magenta")
    table.add_column("크기", style="blue")
    table.add_column("수정일", style="green")
    
    # 테이블에 데이터 추가
    for link in links[:5]:
        type_style = "[bold blue]디렉토리[/]" if link.type == "directory" else "[yellow]파일[/]"
        table.add_row(
            link.filename, 
            type_style,
            link.size if link.size else "N/A",
            link.last_modified if link.last_modified else "N/A"
        )
        
    console.print(table)
    
    if len(links) > 5:
        console.print(f"[dim]... 그 외 {len(links) - 5}개 항목이 더 있습니다.[/]")
    
    # 진행 상황을 표시할 Progress 컨텍스트 생성
    progress_text = f"[bold green]패턴 '{pattern}'으로 파일 검색 중...[/]"
    
    # 모든 결과를 저장할 리스트
    all_entries = []
    
    # 크롤링 진행 상태 표시 및 결과 수집
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        expand=True
    ) as progress:
        task = progress.add_task(progress_text, total=None)
        
        start_time = time.time()
        
        # 모든 항목 수집 (최대 깊이 설정)
        async for entry in http_parser.walk(
            glob_pattern=pattern,
            max_depth=max_depth
        ):
            all_entries.append(entry)
            # 항목 발견시마다 진행 상태 업데이트
            progress.update(task, description=f"[bold green]검색 중...[/] {len(all_entries)}개 항목 발견")
        
        # 완료 상태로 표시
        progress.update(task, completed=True, description=f"[bold green]검색 완료![/] {len(all_entries)}개 항목 발견")
    
    # 결과 출력
    end_time = time.time()
    duration = end_time - start_time
    
    # 타입별 통계
    file_count = sum(1 for entry in all_entries if entry.type == "file")
    dir_count = sum(1 for entry in all_entries if entry.type == "directory")
    
    # 요약 정보 패널
    summary_panel = Panel(
        f"""[bold]총 {len(all_entries)}개의 항목을 찾았습니다.[/] (소요 시간: {duration:.2f}초)
[cyan]파일:[/] {file_count}개, [magenta]디렉토리:[/] {dir_count}개
[dim]검색 패턴:[/] {pattern}, [dim]최대 깊이:[/] {max_depth}""",
        title="[bold green]검색 결과 요약[/]", 
        border_style="green"
    )
    console.print(summary_panel)
    
    # 출력 포맷에 따라 결과 표시
    if output_format == "table":
        # 테이블 형식으로 결과 표시
        result_table = Table(title=f"검색 결과 (최대 {max_display}개 표시)")
        result_table.add_column("번호", style="dim")
        result_table.add_column("파일/디렉토리", style="cyan")
        result_table.add_column("타입", style="magenta")
        result_table.add_column("크기", style="blue")
        result_table.add_column("수정일", style="green")
        
        max_display_count = min(max_display, len(all_entries))
        for i, entry in enumerate(all_entries[:max_display_count]):
            type_icon = "📁" if entry.type == "directory" else "📄"
            type_style = "[bold blue]디렉토리[/]" if entry.type == "directory" else "[yellow]파일[/]"
            result_table.add_row(
                str(i+1),
                f"{type_icon} {entry.filename}", 
                type_style,
                entry.size if entry.size and entry.size != '-' else "N/A",
                entry.last_modified if entry.last_modified else "N/A"
            )
        
        console.print(result_table)
    
    elif output_format == "tree":
        # 트리 형식으로 결과 표시
        tree = Tree("[bold green]검색 결과[/]")
        
        # URL별로 항목 그룹화
        entries_by_url = {}
        for entry in all_entries:
            base_url = '/'.join(entry.url.split('/')[:-1]) + '/'
            if base_url not in entries_by_url:
                entries_by_url[base_url] = []
            entries_by_url[base_url].append(entry)
        
        # 트리 구성
        count = 0
        max_display_count = min(max_display, len(all_entries))
        
        for url, entries in entries_by_url.items():
            # URL 경로를 짧게 표시
            short_url = url.replace("https://", "").replace("http://", "")
            url_node = tree.add(f"[bold blue]{short_url}[/]")
            
            for entry in entries:
                if count >= max_display_count:
                    break
                    
                icon = "📁" if entry.type == "directory" else "📄"
                entry_info = f"{icon} [cyan]{entry.filename}[/]"
                
                if entry.size and entry.size != '-':
                    entry_info += f" ([blue]{entry.size}[/])"
                    
                url_node.add(entry_info)
                count += 1
        
        console.print(tree)
    
    else:  # list 포맷
        # 리스트 형식으로 결과 표시
        console.print("[bold green]검색 결과:[/]")
        
        max_display_count = min(max_display, len(all_entries))
        for i, entry in enumerate(all_entries[:max_display_count]):
            icon = "📁" if entry.type == "directory" else "📄"
            console.print(f"{i+1}. {icon} [cyan]{entry.filename}[/] ([magenta]{entry.type}[/])")
            console.print(f"   URL: [dim]{entry.url}[/]")
            
            if entry.size and entry.size != '-':
                console.print(f"   크기: [blue]{entry.size}[/]")
                
            if entry.last_modified:
                console.print(f"   수정일: [green]{entry.last_modified}[/]")
                
            console.print()
    
    # 나머지 항목이 있다면 메시지 출력
    if len(all_entries) > max_display:
        console.print(f"[dim]... 그 외 {len(all_entries) - max_display}개 항목이 더 있습니다.[/]")
    
    # 결과를 파일에 저장
    if save_to_file:
        with open(save_to_file, 'w', encoding='utf-8') as f:
            f.write(f"# 검색 결과\n")
            f.write(f"URL: {url}\n")
            f.write(f"패턴: {pattern}\n")
            f.write(f"최대 깊이: {max_depth}\n")
            f.write(f"총 항목 수: {len(all_entries)} (파일: {file_count}, 디렉토리: {dir_count})\n")
            f.write(f"소요 시간: {duration:.2f}초\n\n")
            
            f.write("## 발견된 항목 목록\n\n")
            for i, entry in enumerate(all_entries):
                f.write(f"{i+1}. {entry.filename} ({entry.type})\n")
                f.write(f"   URL: {entry.url}\n")
                if entry.size and entry.size != '-':
                    f.write(f"   크기: {entry.size}\n")
                if entry.last_modified:
                    f.write(f"   수정일: {entry.last_modified}\n")
                f.write("\n")
        
        console.print(f"[bold green]결과가 '{save_to_file}' 파일에 저장되었습니다.[/]")

@app.command()
def crawl(
    url: str = typer.Option("https://www.statmt.org/europarl/v10/", "--url", "-u", help="크롤링할 URL"),
    pattern: str = typer.Option("*.tsv.gz", "--pattern", "-p", help="파일 필터링 패턴 (예: *.txt, *.tsv.gz)"),
    max_depth: int = typer.Option(3, "--max-depth", "-d", min=1, max=10, help="최대 탐색 깊이"),
    max_display: int = typer.Option(20, "--max-display", "-m", help="화면에 표시할 최대 항목 수"),
    output_format: str = typer.Option("list", "--format", "-f", help="출력 형식 (list, table, tree)"),
    save_to_file: Optional[str] = typer.Option(None, "--output", "-o", help="결과를 저장할 파일 경로")
):
    """
    Apache HTTP 서버 디렉토리 페이지를 크롤링하여 파일과 디렉토리 목록을 검색합니다.
    """
    # 출력 형식 검증
    valid_formats = ["list", "table", "tree"]
    if output_format not in valid_formats:
        console.print(f"[bold red]오류:[/] 유효하지 않은 출력 형식 '{output_format}'. 다음 중 하나를 선택하세요: {', '.join(valid_formats)}")
        raise typer.Exit(1)
    
    try:
        # 비동기 함수 실행
        asyncio.run(crawl_and_display(url, pattern, max_depth, max_display, output_format, save_to_file))
    except Exception as e:
        console.print(f"[bold red]오류:[/] {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
