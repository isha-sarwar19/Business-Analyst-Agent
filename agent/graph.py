from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import chat_node, structure_node, generate_pdf_node
from langchain_core.messages import AIMessage


def should_generate(state: AgentState) -> str:
    """Check last AI message for CONFIRM_GENERATE signal."""
    messages = state.get("messages", [])
    if not messages:
        return END

    last_msg = messages[-1]
    raw_content = last_msg.content if hasattr(last_msg, "content") else ""
    
    if isinstance(raw_content, str):
        content = raw_content.strip()
    elif isinstance(raw_content, list):
        parts = []
        for part in raw_content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
        content = "".join(parts).strip()
    else:
        content = str(raw_content).strip()

    if "CONFIRM_GENERATE" in content:
        return "structure"
    return END  # Stay in conversation loop


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("chat",         chat_node)
    workflow.add_node("structure",    structure_node)
    workflow.add_node("generate_pdf", generate_pdf_node)

    workflow.set_entry_point("chat")

    # After chat: check if user confirmed generation
    workflow.add_conditional_edges(
        "chat", should_generate,
        {
            "structure": "structure",
            END: END
        }
    )

    # Structure → PDF → END (phase is set to "review" inside generate_pdf_node)
    workflow.add_edge("structure", "generate_pdf")
    workflow.add_edge("generate_pdf", END)

    return workflow.compile()


graph = build_graph()