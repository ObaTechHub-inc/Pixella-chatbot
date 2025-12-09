# AVOID MODIFYING THIS FILE EXCEPT YOU KNOW WHAT YOU ARE DOING

"""
Pixella CLI Module
Command-line interface for interacting with the Pixella chatbot powered by Google Generative AI

"""

from httpx import get
import typer
import logging
import sys
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table
from rich import box

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from chatbot import (
    chatbot,
    ChatbotError,
    ConfigurationError,
    APIError,
    get_available_chat_models,
    get_current_chat_model,
    set_chat_model,
)
from chromadb_rag import (
    list_available_embedding_models,
    get_current_embedding_model,
    set_embedding_model,
)
from config import get_config, set_config

logger = logging.getLogger(__name__)

app = typer.Typer(help="Pixella - Chatbot CLI powered by Google Generative AI")

# Global console instance, initialized by entrypoint.py
CLI_CONSOLE: Optional[Console] = None

def _get_console_instance() -> Console:
    """Helper to get console instance with color settings."""
    config = get_config()
    disable_colors_flag = config.get("DISABLE_COLORS", "false").lower() == "true"
    return Console(no_color=disable_colors_flag)

def set_cli_console(console_instance: Console):
    global CLI_CONSOLE
    CLI_CONSOLE = console_instance

def get_cli_console() -> Console:
    global CLI_CONSOLE
    if CLI_CONSOLE is None:
        # Initialize if not already set (e.g., when running direct commands)
        CLI_CONSOLE = _get_console_instance()
    return CLI_CONSOLE


def print_rainbow_welcome():
    """Print a rainbow-colored welcome message as if from Pixella"""
    colors = ["red", "yellow", "green", "cyan", "blue", "magenta"]
    message = "Hello, I'm Pixella"
    
    rainbow_text = Text()
    for i, char in enumerate(message):
        color = colors[i % len(colors)]
        rainbow_text.append(char, style=f"bold {color}")
    
    # Display as a bot message, not a header
    welcome_panel = Panel(
        rainbow_text,
        title="[bold cyan]🤖 Pixella[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED
    )
    get_cli_console().print(welcome_panel)


def print_header():
    """Print a styled header."""
    header_text = Text("🤖 PIXELLA CLI", style="bold cyan", justify="center")
    subtitle = Text("Powered by Google Generative AI", style="dim white", justify="center")
    
    panel = Panel(
        header_text + "\n" + subtitle,
        style="cyan",
        border_style="cyan",
        expand=False,
        padding=(1, 2)
    )
    get_cli_console().print(panel)


def handle_error(error: Exception, context: str = "") -> None:
    """
    Handle and display errors in a user-friendly way.
    
    Args:
        error: The exception to handle
        context: Additional context about where the error occurred
    """
    logger.error(f"Error in {context}: {error}")
    
    if isinstance(error, ConfigurationError):
        error_msg = f"Configuration Error:\n{error}\n\nPlease check your .env file."
        error_color = "yellow"
    elif isinstance(error, APIError):
        error_msg = f"API Error:\n{error}\n\nPlease check your internet connection and API key."
        error_color = "red"
    elif isinstance(error, ValueError):
        error_msg = f"Input Error:\n{error}"
        error_color = "yellow"
    else:
        error_msg = f"Unexpected Error:\n{error}"
        error_color = "red"
    
    error_panel = Panel(
        Text(error_msg, style=f"bold {error_color}"),
        title="[bold red]❌ Error[/bold red]",
        border_style=error_color,
        box=box.ROUNDED
    )
    get_cli_console().print(error_panel)


@app.command()
def chat(
    message: str = typer.Argument(..., help="Your message to the chatbot"),
    session: Optional[str] = typer.Option(None, "--session", "-s", help="Session ID to continue a conversation"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
) -> None:
    """
    Send a message to the chatbot and get a response.
    
    Example:
        pixella chat "Tell me about Python"
    """
    print_header()
    
    if not message or not message.strip():
        handle_error(ValueError("Message cannot be empty"), "chat command")
        raise typer.Exit(code=1)
    
    if verbose:
        get_cli_console().print(f"[bold yellow]📤 Sending:[/bold yellow] {message}\n")
    
    if chatbot is None:
        handle_error(ConfigurationError("Chatbot not initialized"), "chat command")
        raise typer.Exit(code=1)
    
    try:
        get_cli_console().print("[bold blue]⏳ Thinking...[/bold blue]")
        
        history = []
        if session:
            from memory import get_memory
            memory = get_memory()
            if memory:
                history = memory.get_conversation_history(session, limit=10)
        
        response = chatbot.chat(message, history=history)
        
        if session and memory:
            memory.add_message("user", message, session)
            memory.add_message("assistant", response, session)

        # Display user message
        user_panel = Panel(
            Text(message, style="white"),
            title="[bold green]👤 You[/bold green]",
            border_style="green",
            box=box.ROUNDED
        )
        get_cli_console().print(user_panel)
        
        # Display bot response
        bot_panel = Panel(
            Text(response, style="cyan"),
            title="[bold cyan]🤖 Pixella[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED
        )
        get_cli_console().print(bot_panel)
        
    except ChatbotError as e:
        handle_error(e, "chat command")
        raise typer.Exit(code=1)
    except Exception as e:
        handle_error(e, "chat command")
        raise typer.Exit(code=1)


@app.command()
def interactive(
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging")
) -> None:
    """
    Start an interactive chat session with the chatbot. 
    
    Slash Commands:
        /exit, /quit     - End the session
        /debug           - Toggle debug logging
        /persona [text]  - Set user persona
        /session         - Manage sessions
        /import [file]   - Import documents for RAG
        /clear           - Clear conversation history
        /model [type] [name] - Switch AI model (e.g., /model chat gemini-2.5-pro)
        /models [type]   - List available models (e.g., /models chat)
        /help            - Show command help
    
    Type 'exit', 'quit', or press Ctrl+C to end the session.
    """
    print_header()
    
    if chatbot is None:
        handle_error(ConfigurationError("Chatbot not initialized"), "interactive mode")
        raise typer.Exit(code=1)
    
    # Initialize memory and RAG
    memory = None
    rag = None
    session = None
    debug_mode = debug # Track debug mode state
    should_exit = False

    try:
        from memory import get_memory
        from chromadb_rag import get_rag
        
        config = get_config()
        memory_path = config.get("MEMORY_PATH", "./data/memory")
        db_path = config.get("DB_PATH", "./db/chroma")

        memory = get_memory()
        rag = get_rag()
        
        # Create a new session
        session = memory.create_session() if memory else None
    except Exception as e:
        logger.warning(f"Could not initialize memory/RAG: {e}")
    
    welcome_text = Text(
        "💬 Welcome to Interactive Mode\nType '/help' for slash commands or 'exit'|'/quit' to end.",
        style="dim cyan"
    )
    welcome_panel = Panel(
        welcome_text,
        style="cyan",
        border_style="cyan",
        expand=False
    )
    get_cli_console().print(welcome_panel)
    
    # Print rainbow welcome after headers
    get_cli_console().print()
    print_rainbow_welcome()
    get_cli_console().print()
    
    message_count = 0
    
    config = get_config()
    user_name = config.get("USER_NAME", "User")
    user_persona = config.get("USER_PERSONA", "")
    
    # Show debug hint
    if not debug_mode:
        get_cli_console().print("[dim]Tip: Use '/debug' to toggle debug mode, '/help' for commands[/dim]\n")
    
    # API Quota Warning Note
    quota_warning = Panel(
        Text("Note: Make sure to know and follow the limit of your API quota for models to avoid exceeding limits.", style="yellow"),
        border_style="yellow",
        box=box.ROUNDED,
        title="[bold yellow]API Quota Warning[/bold yellow]"
    )
    get_cli_console().print(quota_warning)
    get_cli_console().print()
    
    try:
        while not should_exit:
            try:
                user_input = Prompt.ask(
                    f"[bold green]{user_name} ({session.session_id if session else 'no session'})[/bold green]",
                    console=get_cli_console()
                )
                
                # Handle slash commands
                if user_input.startswith("/"):
                    command_parts = user_input.split(None, 1)
                    command = command_parts[0].lower()
                    args = command_parts[1] if len(command_parts) > 1 else ""
                    
                    # Debug command
                    if command in ["/debug", "/d"]:
                        debug_mode = not debug_mode
                        if debug_mode:
                            logging.disable(logging.NOTSET)
                            logging.getLogger().setLevel(logging.DEBUG)
                            logging.getLogger("langchain").setLevel(logging.DEBUG)
                            logging.getLogger("langchain_google_genai").setLevel(logging.DEBUG)
                            get_cli_console().print("[yellow]🔍 Debug mode: ON[/yellow]\n")
                        else:
                            logging.disable(logging.CRITICAL)
                            logging.getLogger().setLevel(logging.CRITICAL)
                            logging.getLogger("langchain").setLevel(logging.CRITICAL)
                            get_cli_console().print("[yellow]🔍 Debug mode: OFF[/yellow]\n")
                        continue
                    
                    # Persona command
                    elif command in ["/persona", "/p"]:
                        if args:
                            user_persona = args
                            set_config("USER_PERSONA", user_persona)
                            get_cli_console().print(f"[cyan]👤 Persona set and saved to config: '{user_persona}'[/cyan]\n")
                        else:
                            get_cli_console().print(f"[dim]Current persona: {user_persona or 'None'}[/dim]\n")
                        continue
                    
                    # Session command
                    elif command in ["/session", "/s"]:
                        if memory:
                            session_command_parts = args.split(None, 2) # Split into 3 parts for rename
                            subcommand = session_command_parts[0].lower() if session_command_parts else "list"
                
                            if subcommand == "new":
                               new_session_id = session_command_parts[1] if len(session_command_parts) > 1 else None
                               session = memory.create_session(session_id=new_session_id)
                               config = get_config()
                               user_name = config.get("USER_NAME", "User")
                               user_persona = config.get("USER_PERSONA", "")
                               message_count = 0
                               get_cli_console().print(f"[green]✓ New session created: {session.session_id}[/green]\n")
                            elif subcommand == "name":
                                if len(session_command_parts) > 1:
                                    new_name = session_command_parts[1]
                                    if session and session.session_id.startswith("session_"): # Only rename temporary session
                                        if memory.rename_session(session.session_id, new_name):
                                           session.session_id = new_name
                                           get_cli_console().print(f"[green]✓ Session named '{new_name}'[/green]\n")
                                        else:
                                           get_cli_console().print(f"[red]Failed to name session. The name might already exist.[/red]\n")
                                    else:
                                        get_cli_console().print("[yellow]Error: '/session name' is only for naming temporary sessions. Use '/session rename' to rename existing sessions.[/yellow]\n")
                                else:
                                    get_cli_console().print("[yellow]Usage: /session name <new_session_name>[/yellow]\n")
                            elif subcommand == "rename":
                                if len(session_command_parts) == 3:
                                   old_name = session_command_parts[1]
                                   new_name = session_command_parts[2]
                                   if memory.rename_session(old_name, new_name):
                                        if session and session.session_id == old_name:
                                           session.session_id = new_name
                                           get_cli_console().print(f"[green]✓ Session '{old_name}' renamed to '{new_name}'[/green]\n")
                                        else:
                                           get_cli_console().print(f"[red]Failed to rename session '{old_name}'. The new name might already exist or the old session might not exist.[/red]\n")
                                   else:
                                       get_cli_console().print("[yellow]Usage: /session rename <old_session_name> <new_session_name>[/yellow]\n")
                            elif subcommand == "delete":
                                if len(session_command_parts) > 1:
                                   session_id_to_delete = session_command_parts[1]
                                   if memory.delete_session(session_id_to_delete):
                                       get_cli_console().print(f"[green]✓ Session '{session_id_to_delete}' deleted.[/green]\n")
                                       if session and session.session_id == session_id_to_delete:
                                          session = memory.create_session() # Start a new temporary session
                                          get_cli_console().print(f"[yellow]Current session deleted. New temporary session '{session.session_id}' created.[/yellow]\n")
                                       else:
                                          get_cli_console().print(f"[red]Failed to delete session '{session_id_to_delete}'. It might not exist.[/red]\n")
                                   else:
                                       get_cli_console().print("[yellow]Usage: /session delete <session_id>[/yellow]\n")
                            elif subcommand == "load":
                                if len(session_command_parts) > 1:
                                    session_id_to_load = session_command_parts[1]
                                    loaded_session = memory.get_session(session_id_to_load)
                                    if loaded_session:
                                       session = loaded_session
                                       config = get_config()
                                       user_name = config.get("USER_NAME", "User")
                                       user_persona = config.get("USER_PERSONA", "")
                                       message_count = len(session.messages)
                                       get_cli_console().print(f"[green]✓ Session loaded: {session.session_id}[/green]\n")
                                    else:
                                       get_cli_console().print(f"[red]Session not found: {session_id_to_load}[/red]\n")
                                else:
                                   get_cli_console().print("[yellow]Usage: /session load <session_id>[/yellow]\n")
                            elif subcommand == "list":
                                sessions = memory.get_all_sessions()
                                if sessions:
                                   table = Table(title="📋 Saved Sessions", box=box.ROUNDED, border_style="blue")
                                   table.add_column("Session ID", style="cyan")
                                   table.add_column("User Name", style="yellow")
                                   table.add_column("Messages", style="green")
                                   for s in sessions[:15]:
                                       table.add_row(s['session_id'], s['user_name'], str(s['message_count']))
                                       get_cli_console().print(table)
                                else:
                                    get_cli_console().print("[dim]No sessions found[/dim]\n")
                            elif subcommand == "current":
                                if session:
                                   get_cli_console().print(f"[cyan]Current session: {session.session_id}[/cyan]\n")
                                else:
                                   get_cli_console().print("[yellow]No active session.[/yellow]\n")
                            else:
                                get_cli_console().print(f"[red]Unknown session command: {subcommand}[/red]\n[dim]Usage: /session [new|name|rename|load|list|current|delete][/dim]\n")
                        else:
                           get_cli_console().print("[yellow]Memory not available[/yellow]\n")
                           continue                    
                    # Import command
                    elif command in ["/import", "/i"]:
                        import_parts = args.split(None, 1)
                        if len(import_parts) == 2:
                            import_type, file_path_raw = import_parts
                            
                            # Clean up file_path_raw for common user input issues
                            file_path_str = file_path_raw
                            # 1. Remove surrounding quotes if present
                            if file_path_str.startswith('"') and file_path_str.endswith('"'):
                                file_path_str = file_path_str[1:-1]
                            elif file_path_str.startswith("'") and file_path_str.endswith("'"):
                                file_path_str = file_path_str[1:-1]
                            
                            # 2. Unescape spaces (e.g., "doc\ path.doc" -> "doc path.doc")
                            file_path_str = file_path_str.replace('\\ ', ' ')

                            file_path = Path(file_path_str).expanduser()
                            
                            if not file_path.exists():
                                get_cli_console().print(f"[red]File not found: {file_path_str}[/red]\n")
                                continue
                            
                            if import_type.lower() == "rag":
                                if rag:
                                    try:
                                        count = rag.add_file(str(file_path))
                                        get_cli_console().print(f"[green]✓ Imported {count} chunks from {file_path.name} to RAG.[/green]\n")
                                    except Exception as e:
                                        get_cli_console().print(f"[red]RAG import error: {e}[/red]\n")
                                else:
                                    get_cli_console().print("[yellow]RAG not available for import.[/yellow]\n")
                            elif import_type.lower() == "doc":
                                if chatbot:
                                    try:
                                        char_count = chatbot.import_document_for_chat(str(file_path), session_id=session.session_id if session else None)
                                        get_cli_console().print(f"[green]✓ Imported {char_count} characters from {file_path.name} permanently.[/green]\n")
                                    except Exception as e:
                                        get_cli_console().print(f"[red]Document import error: {e}[/red]\n")
                                else:
                                    get_cli_console().print("[yellow]Chatbot not available for document import.[/yellow]\n")
                            else:
                                get_cli_console().print("[red]Invalid import type. Use 'rag' or 'doc'.[/red]\n")
                        else:
                            get_cli_console().print("[yellow]Usage: /import [rag|doc] <file_path>[/yellow]\n")
                        continue
                    
                    # Name command (for user_name)
                    elif command in ["/name", "/n"]:
                        if args:
                            user_name = args
                            set_config("USER_NAME", user_name)
                            get_cli_console().print(f"[cyan]👤 Name set to: {args}[/cyan]\n")
                        else:
                            get_cli_console().print(f"[dim]Current name: {user_name}[/dim]\n")
                        continue
                    
                    # RAG info command
                    elif command in ["/rag", "/ra"]:
                        if rag:
                            info = rag.get_collection_info()
                            rag_panel = Panel(
                                f"[cyan]Collection:[/cyan] {info.get('name', 'unknown')}\n"
                                f"[cyan]Documents:[/cyan] {info.get('count', 0)}\n"
                                f"[cyan]Path:[/cyan] {info.get('db_path', 'unknown')}",
                                title="📚 RAG Status",
                                border_style="blue"
                            )
                            get_cli_console().print(rag_panel)
                        else:
                            get_cli_console().print("[yellow]RAG not available[/yellow]\n")
                        continue
                    
                    # Models command
                    elif command in ["/models"]:
                        model_type = args.lower() or "all"
                        
                        if model_type in ["all", "chat"]:
                            chat_models = get_available_chat_models()
                            current_chat_model = get_current_chat_model()
                            get_cli_console().print(f"\n[cyan]Current Chat Model: {current_chat_model}[/cyan]\n")
                            get_cli_console().print("[bold cyan]Available Chat Models:[/bold cyan]")
                            for model_name, description in chat_models.items():
                                marker = "→" if model_name == current_chat_model else " "
                                get_cli_console().print(f"  {marker} [yellow]{model_name}[/yellow]: {description}")
                            get_cli_console().print()

                        if model_type in ["all", "embedding"]:
                            embedding_models = list_available_embedding_models()
                            current_embedding_model = get_current_embedding_model()
                            get_cli_console().print(f"\n[cyan]Current Embedding Model: {current_embedding_model}[/cyan]\n")
                            get_cli_console().print("[bold cyan]Available Embedding Models (Reference):[/bold cyan]")
                            for model_name, description in embedding_models.items():
                                marker = "→" if model_name == current_embedding_model else " "
                                get_cli_console().print(f"  {marker} [yellow]{model_name}[/yellow]: {description}")
                            get_cli_console().print()
                        
                        if model_type not in ["all", "chat", "embedding"]:
                            get_cli_console().print(f"[red]Unknown model type: {model_type}[/red]\n[dim]Usage: /models [chat|embedding][/dim]\n")
                        
                        continue

                    # Model command
                    elif command in ["/model", "/m"]:
                        model_parts = args.split(None, 1)
                        if len(model_parts) == 2:
                            model_type, model_name = model_parts
                            model_type = model_type.lower()
                            
                            if model_type == "chat":
                                try:
                                    set_chat_model(model_name)
                                    get_cli_console().print(f"[cyan]🤖 Chat model set to: {model_name}[/cyan]\n")
                                except Exception as e:
                                    handle_error(e, "model switch")
                            elif model_type == "embedding":
                                try:
                                    set_embedding_model(model_name)
                                    get_cli_console().print(f"[cyan]🧬 Embedding model set to: {model_name}[/cyan]\n")
                                except Exception as e:
                                    handle_error(e, "model switch")
                            else:
                                get_cli_console().print(f"[red]Unknown model type: {model_type}[/red]\n[dim]Usage: /model [chat|embedding] <model_name>[/dim]\n")
                        else:
                            get_cli_console().print(f"[dim]Current chat model: {get_current_chat_model()}[/dim]")
                            get_cli_console().print(f"[dim]Current embedding model: {get_current_embedding_model()}[/dim]\n")
                        continue

                    # Export command
                    elif command in ["/export", "/ex"]:
                        if args:
                            try:
                                if rag:
                                    rag.export_collection(args)
                                    get_cli_console().print(f"[green]✓ RAG exported to {args}[/green]\n")
                                else:
                                    get_cli_console().print("[yellow]RAG not available[/yellow]\n")
                            except Exception as e:
                                get_cli_console().print(f"[red]Export error: {e}[/red]\n")
                        else:
                            get_cli_console().print("[yellow]Usage: /export <file_path>[/yellow]\n")
                        continue
                    
                    # Stats command
                    elif command in ["/stats", "/st"]:
                        if session:
                            stats = {
                                "Session ID": session.session_id,
                                "User Name": user_name,
                                "User Persona": user_persona if user_persona else "None",
                                "AI Model": get_current_chat_model(),
                                "Messages": len([m for m in session.messages if m.role == "user"]),
                                "Responses": len([m for m in session.messages if m.role == "assistant"]),
                                "Debug Mode": debug_mode,
                            }
                            stats_panel = Panel(
                                "\n".join([f"[cyan]{k}:[/cyan] {v}" for k, v in stats.items()]),
                                title="📊 Session Stats",
                                border_style="blue"
                            )
                            get_cli_console().print(stats_panel)
                        else:
                            get_cli_console().print("[yellow]No active session or memory not available[/yellow]\n")
                        continue
                    
                    # Clear command
                    elif command in ["/clear", "/c"]:
                        if session and memory:
                            if memory.clear_session_messages(session.session_id):
                                get_cli_console().print("[green]✓ Conversation cleared[/green]\n")
                            else:
                                get_cli_console().print("[red]Failed to clear conversation.[/red]\n")
                        else:
                            get_cli_console().print("[yellow]Memory not available[/yellow]\n")
                        continue
                    
                    # Exit/quit commands
                    elif command in ["/exit", "/quit", "/q", "/x"]:
                        should_exit = True
                        continue
                    
                    # Help command
                    elif command in ["/help", "/h", "/?"]:
                        help_text = """
[bold cyan]═════════════════════════════════════════[/bold cyan]
[bold cyan]User Management[/bold cyan]
[yellow]/name, /n [text][/yellow]      - Set your name
[yellow]/persona, /p [text][/yellow]  - Set your persona

[bold cyan]Chat Management[/bold cyan]
[yellow]/clear, /c[/yellow]           - Clear current conversation history
[yellow]/stats, /st[/yellow]          - Show session statistics
[yellow]/session [cmd][/yellow]       - Manage sessions (new, name, load, list, current, delete)

[bold cyan]RAG & Documents[/bold cyan]
[yellow]/rag, /ra[/yellow]            - Show RAG status
[yellow]/import, /i [type] [file][/yellow] - Import documents (type: rag, doc)
[yellow]/export, /ex [file][/yellow]  - Export RAG data

[bold cyan]System[/bold cyan]
[yellow]/debug, /d[/yellow]           - Toggle debug mode
[yellow]/models [type][/yellow]       - List models (e.g., /models chat)
        [yellow]/model [type] [name][/yellow] - Switch AI model (e.g., /model chat gemini-2.5-pro)[yellow]/exit, /quit, /q, /x[/yellow] - End session
[yellow]/help, /h, /?[/yellow]        - Show this help
[bold cyan]═════════════════════════════════════════[/bold cyan]
"""
                        help_panel = Panel(
                            help_text,
                            title="📖 Slash Commands",
                            border_style="cyan",
                            expand=False
                        )
                        get_cli_console().print(help_panel)
                        continue
                    
                    # Unknown command
                    else:
                        get_cli_console().print(f"[red]Unknown command: {command}[/red]\n[dim]Type '/help' for commands[/dim]\n")
                        continue
                
                if not user_input.strip():
                    continue
                
                message_count += 1
                get_cli_console().print("[bold blue]⏳ Thinking...[/bold blue]")
                
                try:
                    # Get RAG context if available
                    rag_context = ""
                    if rag:
                        results = rag.query(user_input, top_k=2)
                        if results:
                            rag_context = rag.query_with_context(user_input, top_k=2)
                    
                    # Get conversation history
                    history = []
                    if memory and session:
                        history = memory.get_conversation_history(session.session_id, limit=10)

                    # Add user message to memory
                    if memory and session:
                        memory.add_message("user", user_input, session.session_id)
                    
                    # Get response from chatbot (can be enhanced with RAG context)
                    response = chatbot.chat(
                        user_input,
                        user_name=user_name,
                        user_persona=user_persona,
                        history=history,
                        rag_context=rag_context
                    )
                    
                    # Add assistant message to memory
                    if memory and session:
                        memory.add_message("assistant", response, session.session_id)
                    
                    # Display user message
                    user_panel = Panel(
                        Text(user_input, style="white"),
                        title=f"[bold green]👤 {user_name} (Message #{message_count})[/bold green]",
                        border_style="green",
                        box=box.ROUNDED
                    )
                    get_cli_console().print(user_panel)
                    
                    # Display bot response
                    bot_panel = Panel(
                        Text(response, style="cyan"),
                        title="[bold cyan]🤖 Pixella[/bold cyan]",
                        border_style="cyan",
                        box=box.ROUNDED
                    )
                    get_cli_console().print(bot_panel)
                    get_cli_console().print()

                except ChatbotError as e:
                    handle_error(e, f"message #{message_count}")
                    get_cli_console().print()
                except Exception as e:
                    handle_error(e, f"message #{message_count}")
                    get_cli_console().print()

            except KeyboardInterrupt:
                should_exit = True
                get_cli_console().print("\n")

    finally:
        # This block runs on normal exit or interrupt
        if session and memory and session.messages and session.session_id.startswith("session_"):
            save_prompt = Prompt.ask("[yellow]Do you want to save this temporary session? (yes/no)[/yellow]", default="no")
            if save_prompt.lower() == "yes":
                new_name = Prompt.ask("[yellow]Enter a name for this session[/yellow]")
                if new_name:
                    if memory.rename_session(session.session_id, new_name):
                        get_cli_console().print(f"[green]✓ Session saved as '{new_name}'[/green]")
                    else:
                        get_cli_console().print(f"[red]Could not save session. Name might already exist.[/red]")
                else:
                    get_cli_console().print("[yellow]Session not saved. No name provided.[/yellow]")
            else:
                # Add the "are you sure" prompt here
                confirm_discard = Prompt.ask("[yellow]Are you sure you want to discard this temporary session? (yes/no)[/yellow]", default="no")
                if confirm_discard.lower() == "yes":
                    # Optionally delete the temporary session from memory if it persisted somehow
                    if memory.delete_session(session.session_id):
                        get_cli_console().print("[yellow]Temporary session discarded.[/yellow]")
                    else:
                        get_cli_console().print("[red]Could not discard temporary session.[/red]")
                else:
                    get_cli_console().print("[yellow]Discard cancelled. Session not saved or discarded.[/yellow]") # User changed mind, don't do anything
        
        goodbye_panel = Panel(
            Text("👋 Thanks for chatting! Goodbye!", style="bold yellow"),
            border_style="yellow",
            box=box.ROUNDED
        )
        get_cli_console().print(goodbye_panel)


@app.command()
def version() -> None:
    """Show version information."""
    version_panel = Panel(
        Text("Pixella v1.0.0\nPowered by Google Generative AI", style="bold cyan"),
        title="[bold cyan]ℹ️ Version[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED
    )
    get_cli_console().print(version_panel)


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        get_cli_console().print("\n[bold yellow]👋 Interrupted by user[/bold yellow]")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        get_cli_console().print(f"\n[bold red]Fatal Error: {e}[/bold red]")
        sys.exit(1)