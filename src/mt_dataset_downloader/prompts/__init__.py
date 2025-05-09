from phoenix.otel import register
import os

from .prompt_explain_page import PromptExplainPage
from .prompt_extract_corpora_sources import PromptExtractCorporaSources

# Tracer provider 등록
tracer_provider = register(
    project_name=os.getenv("PHOENIX_PROJECT_NAME"),
    endpoint=f"{os.environ['PHOENIX_COLLECTOR_ENDPOINT']}/v1/traces",
    auto_instrument=True,
)

__all__ = ["PromptExplainPage", "PromptExtractCorporaSources"]
