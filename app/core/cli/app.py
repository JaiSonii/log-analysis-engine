import argparse
import os
import sys
import asyncio
from dotenv import load_dotenv

# Rich imports for a clean CLI interface
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# LangChain/LangGraph imports
from langchain_core.messages import HumanMessage

# --- Add app root to sys.path ---
# This allows the script to be run from anywhere and still find core modules
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(APP_ROOT)

try:
    from core.agent.builder import build_workflow
    from core.agent.model_provider import ModelProvider
    from core.agent.tools import ToolMaker
    from core.agent.helpers import create_log_flow
    from core.agent.state import AgentInputSchema
except ImportError:
    print("Error: Failed to import core modules. Ensure you are in the correct directory and venv.")
    print(f"Attempted to add {APP_ROOT} to sys.path")
    sys.exit(1)

async def chat_loop(app, state : AgentInputSchema, console: Console):
    """
    Main interactive chat loop.
    Uses Rich for input and output.
    """
    console.print("\n[bold green]SRE Agent is ready! Type 'exit' or 'quit' to end.[/bold green]")
    while True:
        try:
            # Get user input
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
            
            if user_input.lower() in ['exit', 'quit']:
                console.print("[yellow]Goodbye![/yellow]")
                break

            # Stream the agent's response
            with console.status("[spinner]Thinking...[/spinner]"):
                # Use ainvoke for the async graph
                state['messages'].append(HumanMessage(content=user_input))
                response = await app.ainvoke(state)
                
                # The final response is the last message in the state
                ai_message = response['messages'][-1]
                content = ai_message.content

            # Print the AI's response in a formatted panel
            console.print(Panel(content, title="[bold magenta]SRE Agent[/bold magenta]", border_style="magenta"))

        except EOFError:
            # User pressed Ctrl+D
            break
        except KeyboardInterrupt:
            # User pressed Ctrl+C
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]An error occurred during agent invocation:[/bold red] {e}")
            console.print_exception(show_locals=True)


async def main():
    """
    Main async function to parse args, set up, and run the CLI app.
    """
    # Load .env file for API keys
    load_dotenv()
    
    console = Console()
    console.print("[bold blue]Starting SRE Log Analysis Agent CLI...[/bold blue]")

    # --- Argument Parsing ---
    # parser = argparse.ArgumentParser(description="SRE Log Analysis Agent CLI")
    # parser.add_argument("--log-file", required=True, help="Path to the full log file (e.g., data/python.log)")
    # parser.add_argument("--repomix-file", required=True, help="Path to the repomix-output.xml file")
    # parser.add_argument("--provider", default="openai", help="Model provider (default: openai)")
    # parser.add_argument("--model-name", default="gpt-4o-mini", help="Model name (default: gpt-4o-mini)")
    # parser.add_argument("--db-type", default="memory", choices=['memory', 'persistent'], help="Vector DB type (default: memory)")
    # parser.add_argument("--faiss-path", help="Path to faiss.index (required for persistent db)")
    # parser.add_argument("--store-path", help="Path to store.pkl (required for persistent db)")
    # parser.add_argument("--log-start", help="Log start token for repomix extraction (e.g., 'logger')")

    # args = parser.parse_args()

    # --- Interactive Inputs ---
    console.print("\n[bold]Welcome! Let's set up the SRE Agent.[/bold]")

    # 1. Get Log File
    log_file = ""
    while not log_file:
        log_file_input = Prompt.ask("[cyan]1.[/cyan] [yellow]Enter path to the log file[/yellow]", default="data/python.log")
        if not os.path.exists(log_file_input):
            console.print(f"[bold red]Error: Log file not found at {log_file_input}[/bold red]")
        else:
            log_file = log_file_input

    # 2. Get Repomix File
    repomix_file = ""
    while not repomix_file:
        repomix_file_input = Prompt.ask("[cyan]2.[/cyan] [yellow]Enter path to the repomix-output.xml file[/yellow]", default="repomix-output.xml")
        if not os.path.exists(repomix_file_input):
            console.print(f"[bold red]Error: Repomix file not found at {repomix_file_input}[/bold red]")
        else:
            repomix_file = repomix_file_input

    # 3. Get Model Provider
    provider_name = Prompt.ask("[cyan]3.[/cyan] [yellow]Enter model provider[/yellow]", choices=["openai", "openrouter","googleai"], default="openai")

    # 4. Get Model Name
    model_name = Prompt.ask("[cyan]4.[/cyan] [yellow]Enter model name[/yellow]", default="gpt-4.1-mini")

    # 5. Get DB Type
    db_type = Prompt.ask("[cyan]5.[/cyan] [yellow]Select vector DB type[/yellow]", choices=["memory", "persistent"], default="memory")

    # 6. Conditional DB Paths
    faiss_path = None
    store_path = None
    if db_type == 'persistent':
        faiss_path = Prompt.ask("  [yellow]Enter path to faiss.index[/yellow]", default="data/faiss.index")
        store_path = Prompt.ask("  [yellow]Enter path to store.pkl[/yellow]", default="data/store.pkl")
        if not os.path.exists(faiss_path) or not os.path.exists(store_path):
             console.print(f"[bold yellow]Warning: faiss/store path not found. Will attempt to load, but may fail if files are missing.[/bold yellow]")
    
    # 7. Get Log Start (Optional)
    log_start = Prompt.ask("[cyan]6.[/cyan] [yellow]Enter log start token (optional, e.g., 'logger', press Enter to skip)[/yellow]", default="")
    if log_start == "":
        log_start = None

    # --- Validations --- (Handled interactively above)
    # if not os.path.exists(args.log_file):
    #     console.print(f"[bold red]Error: Log file not found at {args.log_file}[/bold red]")
    #     sys.exit(1)
    # if not os.path.exists(args.repomix_file):
    #     console.print(f"[bold red]Error: Repomix file not found at {args.repomix_file}[/bold red]")
    #     sys.exit(1)
    
    # if args.db_type == 'persistent':
    #     if not args.faiss_path or not args.store_path:
    #         console.print("[bold red]Error: For 'persistent' db, --faiss-path and --store-path are required.[/bold red]")
    #         sys.exit(1)
    #     if not os.path.exists(args.faiss_path) or not os.path.exists(args.store_path):
    #          console.print(f"[bold yellow]Warning: faiss/store path not found. Will attempt to load, but may fail if files are missing.[/bold yellow]")

    try:
        # --- Initialization ---
        console.print("\n[yellow]Initializing components...[/yellow]")
        
        # 1. Initialize Model Provider
        provider = ModelProvider(provider=provider_name, model_name=model_name)
        provider.build()
        
        # 2. Initialize Tool Maker
        tool_maker = ToolMaker(
            db_type=db_type,
            # Only pass log_file_path to ToolMaker if db_type is 'memory' for indexing
            log_file_path=log_file if db_type == 'memory' else None,
            faiss_path=faiss_path,
            store_path=store_path
        )

        # 3. Load Repomix Context and extract logs
        console.print(f"[green]Loading repomix context from {repomix_file}...[/green]")
        with open(repomix_file, 'r', encoding='utf-8') as f:
            repomix_context = f.read()

        log_list = create_log_flow(repomix_context, log_start)
        console.print(f"Extracted [bold]{len(log_list)}[/bold] log statements from code context.")

        # 4. Build Agent Workflow
        console.print("[yellow]Building agent workflow...[/yellow]")
        log_file_abs_path = os.path.abspath(log_file)
        
        workflow = await build_workflow(
            provider=provider, 
            tool_maker=tool_maker, 
            log_list=log_list, 
            log_file_path=log_file_abs_path # Pass full absolute path for the agent
        )
        
        state = AgentInputSchema(log_list=log_list, log_file_path=log_file_abs_path,messages=[])
        # 5. Compile the graph
        app = workflow.compile()

        # --- Run Chat Loop ---
        await chat_loop(app, state, console)

    except Exception as e:
        console.print(f"[bold red]Failed to initialize agent:[/bold red] {e}")
        console.print_exception(show_locals=True)
        sys.exit(1)

if __name__ == "__main__":
    # Use asyncio.run() to execute the main async function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCLI shutdown.")

