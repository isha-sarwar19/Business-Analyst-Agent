"""
BA Agent — Beautiful CLI Runner
Run this to chat with Azura via the terminal.
"""
import os
import sys

# Check for 'rich' (optional but recommended)
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.markdown import Markdown
    from rich.rule import Rule
    from rich.prompt import Prompt
    from rich import print as rprint
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from langchain_core.messages import HumanMessage, AIMessage
from agent.graph import graph

os.environ["ANONYMIZED_TELEMETRY"] = "False"

console = Console() if HAS_RICH else None


def print_banner():
    if HAS_RICH:
        banner = Text()
        banner.append("  🕵️‍♂️  AI Business Analyst", style="bold cyan")
        console.print(Panel(banner, subtitle="[dim]Powered by Azura · Type 'exit' to quit[/dim]",
                            border_style="cyan", padding=(1, 4)))
        console.print()
    else:
        print("\n" + "="*60)
        print("  🕵️‍♂️  AI Business Analyst")
        print("  Powered by Azura · Type 'exit' to quit")
        print("="*60 + "\n")


def print_agent(content: str):
    """Print agent message with formatting."""
    if HAS_RICH:
        console.print(Rule(style="dim"))
        console.print(Panel(
            Markdown(content),
            title="[bold green]🤖 Azura[/bold green]",
            border_style="green",
            padding=(0, 2)
        ))
        console.print()
    else:
        print(f"\n🤖 Azura:\n{content}\n")


def print_user(content: str):
    """Echo the user message with formatting."""
    if HAS_RICH:
        console.print(f"[bold blue]  You:[/bold blue] [white]{content}[/white]")
    else:
        print(f"\n  You: {content}")


def print_success(msg: str):
    if HAS_RICH:
        console.print(f"\n[bold green]✅  {msg}[/bold green]\n")
    else:
        print(f"\n✅  {msg}\n")


def print_error(msg: str):
    if HAS_RICH:
        console.print(f"\n[bold red]❌  {msg}[/bold red]\n")
    else:
        print(f"\n❌  {msg}\n")


def print_thinking():
    if HAS_RICH:
        console.print("[dim italic]  Thinking...[/dim italic]")


def main():
    print_banner()

    if HAS_RICH:
        console.print("[dim]  Hello! Chat Naturally! or tell Azura you want to create a PRD.[/dim]\n")
    else:
        print("  Chat naturally, or tell Azura you want to create a PRD.\n")

    # Initial state
    state = {
        "messages":          [],
        "phase":             "chat",
        "structured_output": None,
        "prd_json":          None,
        "pdf_output_path":   "",
        "error":             None
    }

    # Opening greeting
    greeting = "👋 Hi! I'm Azura, your AI Business Analyst. How can I help you today?"
    print_agent(greeting)
    state["messages"].append(AIMessage(content=greeting))

    while True:
        try:
            # Get user input
            if HAS_RICH:
                user_input = Prompt.ask("[bold blue]  You[/bold blue]").strip()
            else:
                user_input = input("  You: ").strip()

            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q", "bye"):
                if HAS_RICH:
                    console.print("\n[bold cyan]  👋 Goodbye! Have a great day.[/bold cyan]\n")
                else:
                    print("\n  👋 Goodbye!\n")
                break

            # Add to state
            state["messages"].append(HumanMessage(content=user_input))

            # Run graph
            print_thinking()
            result = graph.invoke(state)
            state = result

            # Get the last AI message
            last_msg = state["messages"][-1]
            response_content = last_msg.content if hasattr(last_msg, "content") else ""

            # Handle signals
            if "CONFIRM_GENERATE" in response_content:
                print_success("Generating your PRD, please wait...")
                pdf_path = state.get("pdf_output_path", "")
                if pdf_path and os.path.exists(pdf_path):
                    print_success(f"PRD generated successfully!\n  📄 Saved to: {os.path.abspath(pdf_path)}")
                else:
                    print_error("PDF generation failed. Please try again.")
            else:
                clean = response_content.replace("SWITCH_INTERVIEW", "").strip()
                print_agent(clean)

        except KeyboardInterrupt:
            if HAS_RICH:
                console.print("\n\n[bold cyan]  👋 Interrupted. Goodbye![/bold cyan]\n")
            else:
                print("\n\n  👋 Interrupted. Goodbye!\n")
            break
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            break


if __name__ == "__main__":
    main()
