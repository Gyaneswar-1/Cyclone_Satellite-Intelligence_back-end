from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Payload for user interaction with Cyra AI Agent."""
    message: str = Field(..., json_schema_extra={"example": "Is this cyclone strengthening?"})
    storm_id: Optional[str] = Field(None, json_schema_extra={"example": "storm-001"})


class CitationSource(BaseModel):
    """Metadata for retrieved official source citations."""
    title: str
    source: str
    url_or_path: str
    publication_date: Optional[str] = None
    section: Optional[str] = None
    snippet: Optional[str] = None


class ChatResponse(BaseModel):
    """Response payload from Cyra AI Agent."""
    answer: str
    sources: List[CitationSource] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    storm_id: Optional[str] = None
    disclaimer: str = "StormSense AI inferences are research outputs and do not replace official IMD bulletins."
