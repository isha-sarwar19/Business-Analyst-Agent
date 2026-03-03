"""
agent/state.py — LangGraph AgentState with session tracking and version fields.
"""
from typing import TypedDict, Optional, List, Annotated
from langchain_core.messages import BaseMessage
import operator
from schemas.output_schema import AnalysisReport


class AgentState(TypedDict):
    messages:               Annotated[List[BaseMessage], operator.add]
    phase:                  str                     # "chat" | "interview" | "review"
    structured_output:      Optional[AnalysisReport]
    prd_json:               Optional[dict]          # Raw PRD dict for modifications
    pdf_output_path:        str
    error:                  Optional[str]

    # ── Production additions ───────────────────────────────────────
    session_id:             Optional[str]           # UUID of the ChatSession DB row
    prd_version:            int                     # Current PRD version number (0 = none yet)

    # ── Document upload ───────────────────────────────────────────
    uploaded_doc_context:   Optional[str]           # Extracted text from user-uploaded PDF
    uploaded_doc_name:      Optional[str]           # Original filename of the uploaded PDF