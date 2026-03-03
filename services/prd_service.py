"""
services/prd_service.py — PRD business logic: structuring, persisting, versioning.

Orchestrates LLM structuring call + DB persistence. Keeps nodes.py clean.
"""
import json
import re
from datetime import datetime
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage
from services import llm_service
from db import repository as repo
from db.models import PRDVersion
from core.logging_config import get_logger
from core.config import settings

logger = get_logger(__name__)


def _extract_content_string(response) -> str:
    """Safely extract a plain string from an LLM response (handles list content)."""
    content = response.content
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
        return "".join(parts).strip()
    return str(content).strip()


# ── Structure prompt ──────────────────────────────────────────────────────────

_STRUCTURE_PROMPT_TEMPLATE = """You are a Senior Business Analyst system that ONLY outputs raw JSON.
You must take the following interview transcript and map it into the exact JSON structure provided beneath.
Enrich and expand the content to be professional, detailed, and standard. Fill in reasonable defaults where information is missing.

CRITICAL INSTRUCTION: You MUST NOT generate a Markdown document. You MUST NOT generate conversational text.
Your entire response MUST be a single, valid JSON object starting with {{ and ending with }}.

TRANSCRIPT:
{conversation_text}

TODAY'S DATE: {today}
{modification_context}

OUTPUT STRUCTURE (return ONLY valid JSON, do NOT use markdown code blocks):
{{
  "project_name": "Full project name",
  "version": "V1.0",
  "date": "{today}",
  "introduction": "A professional 2-3 sentence introduction paragraph.",
  "project_overview": {{
    "brief": "Detailed project brief",
    "outcomes": ["Outcome 1"],
    "stakeholders": ["Project Manager", "Development Team"],
    "timeline_start": "DD-Mon-YYYY",
    "timeline_end": "DD-Mon-YYYY",
    "milestones": [
      {{"name": "Milestone 1", "start_date": "DD-Mon-YYYY", "end_date": "DD-Mon-YYYY", "acceptance_criteria": ["Criterion 1"]}}
    ]
  }},
  "deliverables": {{
    "software_modules": ["Module 1"],
    "documentation": ["System Design Document"],
    "training_materials": ["User training guides"],
    "user_manuals": ["Step-by-step instructions"],
    "other": ["API documentation"]
  }},
  "functional_requirements": {{
    "user_roles_permissions": ["Admin: Full access"],
    "ui_ux_specifications": ["Responsive web UI"],
    "data_management": ["Real-time data updates"],
    "integrations": ["REST APIs"]
  }},
  "non_functional_requirements": {{
    "performance": ["Handles 10,000 concurrent users"],
    "reliability": ["99.9% uptime"],
    "usability": ["Intuitive UI"],
    "compatibility": ["Responsive design", "iOS", "Android"],
    "compliance": ["GDPR compliant"],
    "scalability": ["Horizontal scaling"],
    "maintainability": ["Modular architecture"]
  }},
  "technical_requirements": {{
    "languages_frameworks": ["Python", "ReactJS"],
    "database": ["PostgreSQL"],
    "hosting": ["AWS EC2"],
    "security": ["Role-based access", "SSL"],
    "perf_scalability": ["Load balancing", "Caching"]
  }},
  "service_provider": {{"name": "", "address": "", "contact": "", "email": "", "company_name": "Vaival Technologies", "company_address": "", "company_reg_number": ""}},
  "client": {{"name": "", "address": "", "contact": "", "email": "", "company_name": "", "company_address": "", "company_reg_number": ""}},
  "user_stories": [
    {{
      "id": "US-01",
      "role": "role who benefits (e.g. Admin, End User, Manager)",
      "action": "what they want to do",
      "benefit": "why they want to do it (the business value)",
      "acceptance_criteria": ["Criterion 1", "Criterion 2"]
    }}
  ]
}}

IMPORTANT: Generate a comprehensive list of user stories (at least 5-10) based on the functional requirements gathered. Each story MUST follow the exact JSON format above.
"""



def _clean_raw_json(raw: str) -> str:
    """Strip markdown fences and extract the outermost JSON object."""
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)
    raw = raw.strip()
    # Extract outermost { ... } block (handles leading/trailing text)
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        raw = json_match.group()
    return raw


def structure_prd(conversation_text: str, existing_prd: dict | None = None) -> dict:
    """
    Call the LLM to convert raw conversation text into a structured PRD dict.
    Retries up to MAX_RETRIES times if the LLM returns malformed JSON.
    Each retry informs the LLM exactly what was wrong.
    """
    today = datetime.now().strftime("%d-%b-%Y")

    modification_context = ""
    if existing_prd:
        modification_context = (
            f"\nEXISTING PRD (apply modifications from the conversation to this):\n"
            f"{json.dumps(existing_prd, indent=2)}\n\n"
            "Apply any changes requested in the conversation to produce the updated PRD JSON."
        )

    prompt = _STRUCTURE_PROMPT_TEMPLATE.format(
        conversation_text=conversation_text,
        today=today,
        modification_context=modification_context,
    )

    logger.info("Structuring PRD from conversation (%d chars)", len(conversation_text))

    last_error: Exception | None = None
    last_raw: str = ""

    for attempt in range(1, settings.MAX_RETRIES + 1):
        try:
            # On retry, append a repair instruction so the LLM knows what went wrong
            if attempt > 1:
                repair_hint = (
                    f"\n\nYour previous response was not valid JSON. "
                    f"The parse error was: {last_error}. "
                    f"Problematic snippet: {last_raw[:300]!r}\n"
                    "Please return ONLY a valid JSON object this time, with no extra text."
                )
                current_prompt = prompt + repair_hint
            else:
                current_prompt = prompt

            response = llm_service.invoke_llm(
                [HumanMessage(content=current_prompt)]
            )
            raw = _extract_content_string(response)
            last_raw = raw  # save for error reporting on next attempt

            cleaned = _clean_raw_json(raw)
            data = json.loads(cleaned)

            logger.info(
                "PRD structured successfully | attempt=%d | project=%s",
                attempt, data.get("project_name", "unknown")
            )
            
            # Save generated PRD content to long-term memory
            from services import memory_service
            memory_service.add_to_memory(
                text=json.dumps(data, indent=2),
                source_name=f"PRD: {data.get('project_name', 'Unknown')}"
            )

            return data

        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(
                "Malformed JSON from LLM | attempt=%d/%d | error=%s | raw_snippet=%r",
                attempt, settings.MAX_RETRIES, e, last_raw[:200]
            )
            if attempt == settings.MAX_RETRIES:
                logger.error(
                    "All %d structuring attempts failed | last_raw=%r",
                    settings.MAX_RETRIES, last_raw[:500]
                )
                raise ValueError(
                    f"LLM returned malformed JSON after {settings.MAX_RETRIES} attempts. "
                    f"Last error: {e}. Raw snippet: {last_raw[:300]!r}"
                ) from e



def save_prd(
    db: Session,
    session_id: str,
    prd_json: dict,
    pdf_path: str,
    project_name: str,
) -> PRDVersion:
    """Persist a new PRD version to the database and return the version row."""
    return repo.save_prd_version(db, session_id, prd_json, pdf_path, project_name)


def get_version_history(db: Session, session_id: str) -> list[dict]:
    """Return a list of dicts summarising each version for display in the sidebar."""
    versions = repo.get_prd_versions(db, session_id)
    return [
        {
            "version": v.version_number,
            "project": v.project_name,
            "pdf_path": v.pdf_path,
            "created_at": v.created_at.strftime("%Y-%m-%d %H:%M") if v.created_at else "",
        }
        for v in versions
    ]
