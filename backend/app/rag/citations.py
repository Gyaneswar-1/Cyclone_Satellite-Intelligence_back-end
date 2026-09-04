from typing import List, Optional
from backend.app.schemas.chat import CitationSource


def format_citations(sources: List[CitationSource]) -> str:
    """Format citation sources into a clean markdown reference list."""
    if not sources:
        return ""

    lines = ["\n\n**Official Sources & References:**"]
    for idx, src in enumerate(sources, 1):
        date_str = f" ({src.publication_date})" if src.publication_date else ""
        lines.append(f"{idx}. [{src.title}]({src.url_or_path}){date_str} - *{src.source}*")
    return "\n".join(lines)
