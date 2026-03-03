"""
Each node is a pure orchestrator:
  - reads from AgentState
  - delegates to service layer (llm_service, prd_service, pdf_service)
  - returns a partial state update dict

LLM calls, structuring logic, and PDF generation are NOT inline here.
"""
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from agent.state import AgentState
from services import llm_service, prd_service, pdf_service
from core.config import settings
from core.logging_config import get_logger
from datetime import datetime
import os

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────
# Content extraction helper
# ─────────────────────────────────────────────────────────────────

def _get_content_string(resp_content) -> str:
    """Safely extract a plain string from LLM response content (str or list)."""
    if isinstance(resp_content, str):
        return resp_content.strip()
    if isinstance(resp_content, list):
        parts = []
        for part in resp_content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
        return "".join(parts).strip()
    return str(resp_content).strip()


# ─────────────────────────────────────────────────────────────────
# System Prompts (phase-aware)
# ─────────────────────────────────────────────────────────────────

CHAT_SYSTEM_PROMPT = """You are a friendly, helpful AI assistant named Azura who also specializes in business analysis.

You have two modes:
1. **General Assistant** — For casual conversation, greetings, general questions about software, business, or anything else.
2. **PRD Creator** — When the user clearly says they want to create a PRD (Product Requirements Document), you shift to interview mode.

RIGHT NOW you are in GENERAL ASSISTANT mode.

**Rules:**
- If the user says hello, hi, how are you, or chats casually — respond in a warm, conversational way. Do NOT ask about their project.
- If the user asks general questions (e.g. what can you do, who are you, explain something) — answer helpfully and conversationally.
- If the user clearly expresses intent to create a PRD, Business Requirement Document, or wants to document their project requirements — reply with: "SWITCH_INTERVIEW" on a line by itself, followed by a brief message asking what project they want to build.
- NEVER ask about their project unless they bring it up themselves or explicitly say they want PRD generation.

Keep responses concise and friendly."""


INTERVIEW_SYSTEM_PROMPT = """You are Azura, an expert Senior Business Analyst at Vaival Technologies.
The user wants to create a professional PRD (Product Requirements Document). Your job is to gather requirements through a natural conversation.

You MUST gather information covering ALL of these sections:

1. **Project Overview**
   - Project name and brief (what problem it solves)
   - Expected outcomes/deliverables
   - Stakeholders involved
   - Project timeline (start & end dates)
   - Milestones (3-5): name, start date, end date, acceptance criteria

2. **Project Deliverables**
   - Software modules, documentation, training materials, user manuals, other

3. **Functional Requirements**
   - User roles and permissions, UI/UX specs, data management, integrations

4. **Non-Functional Requirements**
   - Performance, Reliability, Usability, Compatibility, Compliance, Scalability, Maintainability

5. **Technical Requirements**
   - Languages & frameworks, Database, Hosting, Security, Performance/Scalability

6. **Service Provider & Client Info** (optional, ask at the end)

**Interview Rules:**
- Ask 1-2 focused questions at a time. Be professional but conversational.
- If the user gives vague answers, gently ask for specifics.
- When you have covered ALL sections, say:
  "I now have all the information I need to create your PRD. **Shall I go ahead and generate the report now?**"
- WAIT for the user to explicitly confirm (e.g. "yes", "go ahead", "generate it").

**CRITICAL — GENERATION SIGNAL:**
- YOU MUST NEVER WRITE THE ACTUAL PRD TEXT IN THIS CHAT. You are only the interviewer. The backend system creates the PDF document.
- When the user confirms they want the PRD generated, your ONLY output should be the exact word: CONFIRM_GENERATE
- Do NOT output CONFIRM_GENERATE unless the user explicitly says yes/generate/proceed.
- If the user gives new info or changes something, incorporate it and re-confirm before generating.
- If user says "wait", "change this", or adds info → acknowledge and do NOT output CONFIRM_GENERATE.
- Remember: NEVER write sections like 'Project Overview' or 'Deliverables' in the chat. Just output CONFIRM_GENERATE when ready."""


REVIEW_SYSTEM_PROMPT = """You are Azura, a helpful AI Business Analyst at Vaival Technologies.
You have already generated a PRD (Product Requirements Document) for the user.

The current PRD JSON data is shown in the conversation context below.

**Your capabilities in this phase:**
1. **Answer questions** — If user asks about PRD content (timeline, modules, etc.), answer from the PRD data.
2. **Handle modifications** — If user asks to change something:
   a. Clearly describe the specific change you will apply.
   b. Then ask: "I've noted the change. **Shall I regenerate the PRD with this update?**"
   c. WAIT for user to explicitly confirm before continuing.
3. **General conversation** — For greetings, thanks, compliments, or off-topic questions, respond naturally. Do NOT mention regenerating.

**STRICT RULES for CONFIRM_GENERATE signal:**
- YOU MUST NEVER WRITE THE ACTUAL PRD TEXT IN THIS CHAT. You are only the interviewer/reviewer. The backend system creates the PDF.
- NEVER output CONFIRM_GENERATE in response to: compliments, thanks, praise, greetings, or casual comments.
- NEVER output CONFIRM_GENERATE unless ALL THREE conditions are met:
  1. The user explicitly asked to change something in the PRD.
  2. YOU already asked "Shall I regenerate?" in your PREVIOUS reply.
  3. The user's current message clearly confirms ("yes", "go ahead", "do it", "regenerate").
- Output CONFIRM_GENERATE ONLY as a standalone token when the above 3 conditions are all met."""


# ─────────────────────────────────────────────────────────────────
# Node 1: Chat (phase-aware conversation)
# ─────────────────────────────────────────────────────────────────

def chat_node(state: AgentState) -> AgentState:
    phase = state.get("phase", "chat")
    logger.info("chat_node | phase=%s | session=%s", phase, state.get("session_id"))

    # Choose system prompt
    if phase == "interview":
        system_prompt = INTERVIEW_SYSTEM_PROMPT
    elif phase == "review":
        import json
        prd_json = state.get("prd_json")
        prd_context = ""
        if prd_json:
            prd_context = f"\n\n**Current PRD Data (for reference):**\n```json\n{json.dumps(prd_json, indent=2)}\n```"
        system_prompt = REVIEW_SYSTEM_PROMPT + prd_context
    else:
        system_prompt = CHAT_SYSTEM_PROMPT
        phase = "chat"

    # ── Inject uploaded document context if available ──────────────
    doc_context = state.get("uploaded_doc_context")
    doc_name    = state.get("uploaded_doc_name", "Uploaded Document")
    if doc_context:
        system_prompt += (
            f"\n\n---\n"
            f"**UPLOADED DOCUMENT: '{doc_name}'**\n"
            f"The user has uploaded a document. Its full extracted text is below.\n"
            f"You can reference this document to answer questions OR, if the user asks you "
            f"to add something from it into the PRD, extract the relevant information "
            f"and incorporate it naturally into the ongoing interview.\n\n"
            f"DOCUMENT CONTENT:\n{doc_context[:6000]}\n---"
        )
        
    # ── Inject long-term memory (RAG) ──────────────
    from services import memory_service
    # We use the latest user message to search memory
    user_query = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_query = msg.content
            break
            
    if user_query:
        past_context = memory_service.search_memory(user_query, k=4)
        if past_context:
            system_prompt += (
                f"\n\n---\n"
                f"**PAST KNOWLEDGE & MEMORY (Vector DB)**\n"
                f"The following context was retrieved from your long-term memory (past documents or PRDs).\n"
                f"Use this to answer questions if relevant to the user's current prompt:\n\n"
                f"{past_context}\n---"
            )

    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm_service.invoke_llm(messages)
    content = _get_content_string(response.content)

    # Phase switch: chat → interview
    if phase == "chat" and "SWITCH_INTERVIEW" in content:
        clean = content.replace("SWITCH_INTERVIEW", "").strip()
        if not clean:
            clean = "Great! Let's get started. Could you tell me the name of your project and briefly what problem it aims to solve?"
        logger.info("Phase transition: chat → interview | session=%s", state.get("session_id"))
        return {"messages": [AIMessage(content=clean)], "phase": "interview"}

    # Phase switch: review → interview (new project)
    if phase == "review" and "SWITCH_INTERVIEW" in content:
        clean = content.replace("SWITCH_INTERVIEW", "").strip()
        if not clean:
            clean = "Sure! Let's create a new PRD. Tell me about this new project — what's it called and what problem does it solve?"
        logger.info("Phase transition: review → interview | session=%s", state.get("session_id"))
        return {
            "messages": [AIMessage(content=clean)],
            "phase": "interview",
            "prd_json": None,
        }

    return {"messages": [response]}


# ─────────────────────────────────────────────────────────────────
# Node 2: Structure (conversation → PRD JSON)
# ─────────────────────────────────────────────────────────────────

def structure_node(state: AgentState) -> AgentState:
    logger.info("structure_node | session=%s", state.get("session_id"))
    print("📊 Structuring collected information...")

    # Build conversation text from history
    conversation_text = ""
    for msg in state["messages"]:
        role = "User" if isinstance(msg, HumanMessage) else "BA Agent"
        if isinstance(msg, (HumanMessage, AIMessage)) and msg.content:
            conversation_text += f"{role}: {msg.content}\n"

    existing_prd = state.get("prd_json")

    try:
        data = prd_service.structure_prd(conversation_text, existing_prd)
        report = pdf_service.build_report(data)
        return {"structured_output": report, "prd_json": data}
    except Exception as e:
        logger.error("structure_node failed | error=%s | session=%s", e, state.get("session_id"))
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────
# Node 3: PDF Generation + DB persistence
# ─────────────────────────────────────────────────────────────────

def _slugify(text: str, max_len: int = 40) -> str:
    import re as _re
    slug = text.lower().strip()
    slug = _re.sub(r"[^\w\s-]", "", slug)
    slug = _re.sub(r"[\s]+", "_", slug)
    slug = _re.sub(r"-+", "_", slug)
    return slug[:max_len].strip("_") or "prd"


def generate_pdf_node(state: AgentState) -> AgentState:
    logger.info("generate_pdf_node | session=%s", state.get("session_id"))
    print("📝 Generating PDF report...")
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    project_name = "prd"
    if state.get("structured_output"):
        project_name = _slugify(state["structured_output"].project_name)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{project_name}_{timestamp}.pdf"
    output_path = os.path.join(settings.OUTPUT_DIR, filename)

    new_version = state.get("prd_version", 0) + 1

    if state.get("structured_output"):
        try:
            pdf_service.generate_pdf(state["structured_output"], output_path)
            print(f"✅ PDF saved: {output_path}")
        except Exception as e:
            logger.error("PDF generation failed | error=%s | session=%s", e, state.get("session_id"))
            return {"error": str(e), "phase": "review"}

        # Persist to DB if session is tracked
        session_id = state.get("session_id")
        if session_id:
            try:
                from db.database import get_db
                from services import prd_service as _ps
                with get_db() as db:
                    _ps.save_prd(
                        db,
                        session_id=session_id,
                        prd_json=state.get("prd_json", {}),
                        pdf_path=output_path,
                        project_name=state["structured_output"].project_name,
                    )
            except Exception as e:
                # DB errors must not break the user-facing PDF flow
                logger.error("DB persist failed (non-fatal) | error=%s | session=%s", e, session_id)
    else:
        print("❌ No structured output to generate PDF from.")
        logger.warning("generate_pdf_node: no structured_output found | session=%s", state.get("session_id"))

    return {
        "pdf_output_path": output_path,
        "phase": "review",
        "prd_version": new_version,
    }