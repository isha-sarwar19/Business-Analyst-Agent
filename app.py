"""
Streamlit frontend.

Session lifecycle:
  1. On first load: init_db(), create ChatSession in DB, store UUID in session_state
  2. Every user message: graph.invoke() → update DB session phase
  3. After PDF generation: sidebar shows version history from DB
  4. User can upload a PDF via the inline uploader above chat input
"""
import streamlit as st
import os
from agent.graph import graph
from langchain_core.messages import HumanMessage, AIMessage
from core.logging_config import setup_logging, get_logger
from db.database import init_db, get_db
from db import repository as repo
from services import prd_service, doc_service

# ── Bootstrap ─────────────────────────────────────────────────────────────────
setup_logging()
init_db()
logger = get_logger(__name__)

os.environ["ANONYMIZED_TELEMETRY"] = "False"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Business Analyst", page_icon="🕵️‍♂️", layout="wide")

# ── Global sleek dark aesthetic & inline uploader CSS ─────────────────────────
st.markdown("""
<style>
/* ── Overrides for main container to feel darker/sleeker ── */
.stApp {
    background-color: #0e1117;
    color: #fafafa;
}

/* ── Custom Upload Button — right side inside the chat input bar ── */
div[data-testid="stFileUploader"] {
    position: fixed !important;
    bottom: 68px !important;     /* vertically centered inside the chat input bar        */
    right: 30px !important;      /* sits just to the left of the send (↑) button        */
    z-index: 99999 !important;
    width: 42px !important;
    height: 42px !important;
}

/* ── Hide the Label ── */
div[data-testid="stFileUploader"] label {
    display: none !important;
}

/* ── The Visual Fake Button (Underneath) ── */
div[data-testid="stFileUploader"]::before {
    content: "📎";
    position: absolute;
    top: 0; left: 0;
    width: 42px;
    height: 42px;
    background: linear-gradient(135deg, #8B5CF6, #D946EF);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    color: white;
    box-shadow: 0 4px 14px rgba(217, 70, 239, 0.3);
    z-index: 1; /* Below the invisible dropzone */
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    pointer-events: none; /* Crucial: Let clicks pass through to the real uploader */
}
/* Hover effect for the fake button */
div[data-testid="stFileUploader"]:hover::before {
    transform: translateY(-2px) scale(1.05);
    background: linear-gradient(135deg, #7C3AED, #C026D3);
    box-shadow: 0 6px 20px rgba(217, 70, 239, 0.5);
}
div[data-testid="stFileUploader"]:active::before {
    transform: translateY(0px) scale(0.95);
}

/* ── The Real Uploader (Invisible but Clickable, Above the Fake Button) ── */
div[data-testid="stFileUploader"] section {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 42px !important;
    height: 42px !important;
    padding: 0 !important;
    margin: 0 !important;
    opacity: 0 !important; /* Completely invisible */
    z-index: 2 !important; /* Above the fake button */
    cursor: pointer !important;
}

/* ── Nuke everything inside the uploader — only keep the invisible section ── */
div[data-testid="stFileUploader"] > * {
    display: none !important;   /* hide label, file chip, ul — everything */
}
div[data-testid="stFileUploader"] > section {
    display: block !important;  /* re-show only the invisible clickable section */
}

/* ── Uploaded-file badge (moves above chat input when active) ── */
.custom-file-badge {
    position: fixed;
    bottom: 100px;
    left: 50%;
    transform: translateX(-350px);
    z-index: 99999;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar — Version History ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🕵️‍♂️ AI Business Analyst")
    st.markdown("*Powered by Azura · Vaival Technologies*")
    st.divider()
    st.markdown("### 📄 PRD Version History")

    session_id_for_sidebar = st.session_state.get("session_id")
    if session_id_for_sidebar:
        with get_db() as db:
            versions = prd_service.get_version_history(db, session_id_for_sidebar)
        if versions:
            for v in versions:
                with st.expander(f"v{v['version']} — {v['project']} ({v['created_at']})"):
                    pdf_path = v["pdf_path"]
                    if pdf_path and os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label=f"📥 Download v{v['version']}",
                                data=f,
                                file_name=os.path.basename(pdf_path),
                                mime="application/pdf",
                                key=f"sidebar_dl_{v['version']}_{pdf_path}",
                            )
                    else:
                        st.caption("PDF file not available.")
        else:
            st.caption("No PRDs generated yet.")
    else:
        st.caption("Start chatting to begin a session.")

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("🕵️‍♂️ AI Business Analyst")
st.markdown("Your intelligent assistant for PRD generation. Chat freely!")

# ── Session State Init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    # Create a DB session row on first load
    with get_db() as db:
        db_session = repo.create_session(db, "chat")
        session_id = db_session.id

    st.session_state["session_id"] = session_id
    st.session_state["messages"] = []
    st.session_state["agent_state"] = {
        "messages":             [],
        "phase":                "chat",
        "structured_output":    None,
        "prd_json":             None,
        "pdf_output_path":      "",
        "error":                None,
        "session_id":           session_id,
        "prd_version":          0,
        "uploaded_doc_context": None,
        "uploaded_doc_name":    None,
    }
    st.session_state["generated_pdfs"] = []

    greeting = "👋 Hi! I'm Azura. How can I help you?\n\n"
    st.session_state["messages"].append({"role": "assistant", "content": greeting})
    st.session_state["agent_state"]["messages"].append(AIMessage(content=greeting))
    logger.info("New Streamlit session | db_session_id=%s", session_id)

# ── Display chat history ──────────────────────────────────────────────────────
for msg in st.session_state["messages"]:
    role    = msg["role"]
    content = msg["content"]
    with st.chat_message(role):
        st.write(content)
        if msg.get("pdf_path") and os.path.exists(msg["pdf_path"]):
            path = msg["pdf_path"]
            with open(path, "rb") as f:
                st.download_button(
                    label=f"📥 Download {os.path.basename(path)}",
                    data=f,
                    file_name=os.path.basename(path),
                    mime="application/pdf",
                    key=f"dl_{path}",
                )

# ── Inline PDF uploader — sits just above the chat input ─────────────────────
current_doc_name = st.session_state["agent_state"].get("uploaded_doc_name")

# ── Inline PDF uploader — sits firmly inside the chat input styling ─────────────
current_doc_name = st.session_state["agent_state"].get("uploaded_doc_name")

# We always render the uploader widget. 
# Our CSS automatically moves it to the appropriate spot inside the ChatInput box!
uploaded_file = st.file_uploader(
    "📎 Attach PDF",
    type=["pdf"],
    key="pdf_uploader",
    label_visibility="collapsed",
)

if uploaded_file is not None:
    # Guard against re-processing on every rerun (Streamlit keeps the widget value
    # across reruns, so without this check the upload handler fires in an infinite loop)
    last_processed = st.session_state.get("last_processed_doc")
    if last_processed != uploaded_file.name:
        with st.spinner(f"📖 Reading '{uploaded_file.name}'..."):
            try:
                extracted_text = doc_service.extract_pdf_text(
                    uploaded_file.read(), uploaded_file.name
                )
                
                # Add to long-term memory (Vector DB)
                from services import memory_service
                memory_service.add_to_memory(extracted_text, source_name=uploaded_file.name)

                st.session_state["agent_state"]["uploaded_doc_context"] = extracted_text
                st.session_state["agent_state"]["uploaded_doc_name"]    = uploaded_file.name
                st.session_state["last_processed_doc"] = uploaded_file.name  # mark as done

                # Show a system note in the chat
                notice = f"📎 **Document uploaded:** `{uploaded_file.name}` — I've read it! You can ask me anything about it."
                st.session_state["messages"].append({"role": "assistant", "content": notice})
                st.session_state["agent_state"]["messages"].append(AIMessage(content=notice))
                logger.info("Document attached | file=%s | chars=%d", uploaded_file.name, len(extracted_text))
                st.rerun()

            except ValueError as e:
                st.error(str(e))

# ── Handle user input ─────────────────────────────────────────────────────────
if prompt := st.chat_input("Type your message here..."):
    st.chat_message("user").write(prompt)
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.session_state["agent_state"]["messages"].append(HumanMessage(content=prompt))

    with st.spinner("Thinking..."):
        result = graph.invoke(st.session_state["agent_state"])
        st.session_state["agent_state"] = result

        # ── Sync DB phase with agent state ────────────────────────
        new_phase = result.get("phase", "chat")
        has_error = bool(result.get("error"))
        session_id = st.session_state.get("session_id")
        if session_id and not has_error:
            try:
                with get_db() as db:
                    repo.update_session_phase(db, session_id, new_phase)
            except Exception as e:
                logger.error("DB phase sync failed (non-fatal) | error=%s", e)
        elif has_error:
            logger.warning(
                "DB phase sync skipped — agent returned error | error=%s", result.get("error")
            )

        # ── Extract response content ───────────────────────────────
        last_msg = result["messages"][-1]
        response_content = last_msg.content if hasattr(last_msg, "content") else ""
        if isinstance(response_content, list):
            parts = [p if isinstance(p, str) else p.get("text", "") for p in response_content]
            response_content = "".join(parts)

        clean_content = response_content.replace("SWITCH_INTERVIEW", "").strip()
        pdf_path      = result.get("pdf_output_path", "")
        prd_version   = result.get("prd_version", 0)

        msg_obj = {"role": "assistant", "content": clean_content}

        if "CONFIRM_GENERATE" in response_content and pdf_path and os.path.exists(pdf_path):
            msg_obj["pdf_path"] = pdf_path
            msg_obj["content"]  = (
                f"✅ **PRD v{prd_version} generated successfully!** Click below to download."
            )

        st.session_state["messages"].append(msg_obj)

        # ── Render response ────────────────────────────────────────
        with st.chat_message("assistant"):
            st.write(msg_obj["content"])
            if msg_obj.get("pdf_path"):
                with open(msg_obj["pdf_path"], "rb") as f:
                    st.download_button(
                        label=f"📥 Download {os.path.basename(msg_obj['pdf_path'])}",
                        data=f,
                        file_name=os.path.basename(msg_obj["pdf_path"]),
                        mime="application/pdf",
                        key=f"dl_new_{msg_obj['pdf_path']}",
                    )
                st.rerun()   # refresh sidebar version history
