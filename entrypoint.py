# AVOID MODIFYING THIS FILE EXCEPT YOU KNOW WHAT YOU ARE DOING

"""
Pixella Entrypoint Module
Pixella - Chatbot with CLI and Web UI interfaces

Entrypoint script using Typer to provide CLI commands for Pixella.
Used by the `pixella` command(/bin/pixella) after installation.

"""

import sys
import typer
import subprocess
import os
import signal
import json
import logging
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from config import get_config, load_env, set_config, set_config_console # Import set_config_console
from cli import set_cli_console # Import the setter function
from typing import Dict, Optional


# Fix sys.argv[0] to show 'pixella' instead of 'entrypoint.py'
sys.argv[0] = "pixella"

def get_version_from_file():
    """Read version from the version file"""
    try:
        with open(os.path.join(os.path.dirname(__file__), "version"), "r") as f:
            for line in f:
                if line.startswith("version"):
                    return line.split(" ")[1].strip()
    except FileNotFoundError:
        return "0.0.0" # Default if file not found
    return "0.0.0" # Default if version not found

# Version
__version__ = get_version_from_file()

def version_callback(value: bool):
    if value:
        console.print(f"Pixella Version: [green]{__version__}[/green]")
        raise typer.Exit()

# Create main Typer app for entrypoint
app = typer.Typer(
    help="Pixella - Chatbot with CLI and Web UI interfaces",
    invoke_without_command=True,
    pretty_exceptions_enable=False,
    no_args_is_help=True
)
console = Console()

# PID file for tracking background UI process
PID_FILE = os.path.expanduser("~/.pixella_ui.pid")

# Initial config load for console colors
_initial_config = get_config()
if _initial_config.get("DISABLE_COLORS", "false").lower() == "true":
    console.no_color = True

# Pass the configured console to the cli module
set_cli_console(console)
# Pass the configured console to the config module
set_config_console(console)

def _setup_logging(debug_enabled: bool):
    """Centralized logging setup function."""
    if debug_enabled:
        logging.disable(logging.NOTSET)
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        logging.getLogger("langchain").setLevel(logging.DEBUG)
        logging.getLogger("langchain_google_genai").setLevel(logging.DEBUG)
        logging.getLogger("google").setLevel(logging.DEBUG)
        logging.getLogger("urllib3").setLevel(logging.DEBUG)
        logging.getLogger("grpc").setLevel(logging.DEBUG)
        console.print("[yellow]🔍 Debug logging enabled.[/yellow]")
    else:
        logging.disable(logging.CRITICAL) # Suppress all logging
        # If not disabled, basicConfig would apply critical level
        # This basicConfig will not be active if logging.disable is called
        logging.basicConfig(level=logging.CRITICAL, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        logging.getLogger("langchain").setLevel(logging.CRITICAL)
        logging.getLogger("langchain_google_genai").setLevel(logging.CRITICAL)
        logging.getLogger("google").setLevel(logging.CRITICAL)
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)
        logging.getLogger("grpc").setLevel(logging.CRITICAL)


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        help="Show version and exit"
    ),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging for the current command call"),
):
    """Pixella - Chatbot with CLI and Web UI interfaces"""
    # Determine final debug status
    config_debug = get_config().get("ALWAYS_DEBUG", "false").lower() == "true"
    final_debug_status = debug or config_debug # CLI --debug takes precedence if provided

    _setup_logging(final_debug_status)

    if debug and not final_debug_status: # User passed --debug, but config disabled it
        console.print("[yellow]Warning: Debug logging disabled by 'ALWAYS_DEBUG=false' in config, ignoring --debug flag.[/yellow]")
    elif config_debug and not debug: # Config debug is true, but no --debug flag
        console.print("[yellow]Debug logging enabled by 'ALWAYS_DEBUG=true' in config.[/yellow]")


@app.command()
def cli(
    message: str = typer.Argument(None, help="Message to send to the chatbot"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Start interactive mode"),
    session: Optional[str] = typer.Option(None, "--session", "-s", help="Session ID to continue a conversation (for chat mode)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
):
    """
    Launch the CLI chatbot interface
    """
    try:
        from cli import app as cli_app
        
        sys.argv = ["pixella"] # Reset argv for Typer to parse cli_app properly
        
        # Check if global debug logging is active (set by main callback)
        global_debug_active = logging.getLogger().isEnabledFor(logging.DEBUG)

        if interactive or not message: # Default to interactive if no message provided
            sys.argv.append("interactive")
            if global_debug_active: # Pass --debug to interactive subcommand if global debug is active
                sys.argv.append("--debug")
            if verbose:
                sys.argv.append("--verbose")
            # If a session is provided but interactive mode is chosen, warn the user
            if session:
                console.print("[yellow]Warning: --session is ignored in interactive mode.[/yellow]")
        else: # Otherwise, go to chat mode
            sys.argv.append("chat")
            if message:
                sys.argv.append(message)
            # Pass --session to chat mode if provided
            if session:
                sys.argv.append("--session")
                sys.argv.append(session) # Typer will handle quoting if necessary
            # Do NOT pass --debug to chat mode, as per user's instruction
            if verbose:
                sys.argv.append("--verbose")
        
        cli_app(obj=console)
    except KeyboardInterrupt:
        console.print("\n[yellow]Chat interrupted by user[/yellow]")
        sys.exit(0)
    except SystemExit as e:
        # Re-raise SystemExit from Typer
        raise e
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        sys.exit(1)


@app.command()
def ui(
    background: bool = typer.Option(False, "--background", "-bg", help="Run UI in background"),
    end: bool = typer.Option(False, "--end", "--exit", "-e", help="Stop background UI"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging"), # This debug is now handled by main callback
    log: bool = typer.Option(False, "--log", help="Show background UI logs"),
):
    """
    Launch the Web UI (Streamlit) - optionally in background mode
    """
    # Debug status is now handled by the main callback and _setup_logging
    # `debug` here reflects if the user explicitly passed `--debug` to `pixella ui`
    # The global logging levels are already set.

    log_file = os.path.expanduser("~/.pixella_ui.log")

    if log:
        if os.path.exists(log_file):
            try:
                console.print(f"--- Tailing log file: {log_file} ---")
                subprocess.run(["tail", "-f", log_file])
            except KeyboardInterrupt:
                console.print("\n--- Log tailing stopped ---")
        else:
            console.print(f"[yellow]Log file not found: {log_file}[/yellow]")
        return

    # Handle stopping background UI
    if end:
        stop_background_ui()
        return
    
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    
    # Set environment variable for debug mode based on final_debug_status
    config_debug = get_config().get("ALWAYS_DEBUG", "false").lower() == "true"
    final_debug_for_ui = debug or config_debug # CLI --debug takes precedence
    
    env = os.environ.copy()
    env["PIXELLA_DEBUG"] = "1" if final_debug_for_ui else "0"
    
    try:
        if background:
            launch_background_ui(app_path, env, final_debug_for_ui)
        else:
            # Launch in foreground (blocking)
            subprocess.run(
                ["streamlit", "run", app_path],
                env=env
            )
            sys.exit(0)
    except KeyboardInterrupt:
        console.print("\n[yellow]Web UI stopped by user[/yellow]")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        console.print(
            Panel(
                f"[red]Failed to launch web UI: {str(e)}[/red]",
                title="Error",
                border_style="red"
            )
        )
        sys.exit(1)
    except FileNotFoundError:
        console.print(
            Panel(
                "[red]Streamlit not found. Please install it: pip install streamlit[/red]",
                title="Error",
                border_style="red"
            )
        )
        sys.exit(1)


def launch_background_ui(app_path: str, env: dict = load_env(), debug_enabled_for_ui: bool = False):
    """Launch Streamlit UI in background and save PID"""
    if env is None:
        env = os.environ.copy()

    log_file = os.path.expanduser("~/.pixella_ui.log")

    with open(log_file, "wb") as log:
        process = subprocess.Popen(
            ["streamlit", "run", app_path],
            stdout=log,
            stderr=log,
            preexec_fn=os.setsid,  # Create new process group
            env=env
        )

    # Save PID to file
    with open(PID_FILE, "w") as f:
        json.dump({"pid": process.pid}, f)

    # Poll log file for network URL
    network_url = "http://localhost:8501" # Default
    for _ in range(20): # Try for 10 seconds
        with open(log_file, "r") as f:
            log_content = f.read()
            if "Network URL: " in log_content:
                network_url = log_content.split("Network URL: ")[1].split("\n")[0].strip()
                break
        import time
        time.sleep(0.5)

    debug_status_text = "[green]ON[/green]" if debug_enabled_for_ui else "[red]OFF[/red]"
    console.print(
        Panel(
            f"[green]✓ Web UI started in background[/green]\n"
            f"[cyan]PID: {process.pid}[/cyan]\n"
            f"[cyan]URL: {network_url}[/cyan]\n"
            f"[cyan]Debug mode: {debug_status_text}[/cyan]\n\n"
            f"To stop: [yellow]pixella ui --end[/yellow]\n"
            f"To view logs: [yellow]pixella ui --log[/yellow]\n",
            title="🚀 Web UI Started",
            border_style="green"
        )
    )

def stop_background_ui():
    """Stop background Streamlit UI process"""
    if not os.path.exists(PID_FILE):
        console.print(
            Panel(
                "[yellow]No background UI process found[/yellow]",
                title="ℹ️ Info",
                border_style="yellow"
            )
        )
        return

    try:
        with open(PID_FILE, "r") as f:
            data = json.load(f)
            pid = data.get("pid")

        if pid:
            try:
                # Try SIGTERM first
                os.killpg(os.getpgid(pid), signal.SIGTERM)
                import time
                time.sleep(0.5)
            except ProcessLookupError:
                pass

            try:
                # Force kill with SIGKILL if still running
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except ProcessLookupError:
                pass

            os.remove(PID_FILE)
            
            # Clean up log file
            log_file = os.path.expanduser("~/.pixella_ui.log")
            if os.path.exists(log_file):
                os.remove(log_file)

            console.print(
                Panel(
                    f"[green]✓ Web UI stopped[/green]\n"
                    f"[cyan]PID: {pid}[/cyan]",
                    title="🛑 Stopped",
                    border_style="green"
                )
            )
    except (FileNotFoundError, json.JSONDecodeError) as e:
        console.print(
            Panel(
                f"[red]Failed to stop UI: {str(e)}[/red]",
                title="Error",
                border_style="red"
            )
        )
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        sys.exit(1)


@app.command()
def test():
    """
    Run tests from test.py
    """
    app_path = os.path.join(os.path.dirname(__file__), "test.py")
    
    try:
        result = subprocess.run(
            [sys.executable, app_path],
            capture_output=False
        )
        if result.returncode != 0:
            console.print(
                Panel(
                    f"[yellow]Tests completed with exit code {result.returncode}[/yellow]",
                    title="⚠️ Test Completed",
                    border_style="yellow"
                )
            )
        else:
            console.print(
                Panel(
                    "[green]All tests passed![/green]",
                    title="✅ Test Passed",
                    border_style="green"
                )
            )
    except FileNotFoundError:
        console.print(
            Panel(
                f"[red]Test file not found: {app_path}[/red]",
                title="Error",
                border_style="red"
            )
        )
        sys.exit(1)


@app.command()
def config(
    init: bool = typer.Option(False, "--init", help="Initialize config interactively"),
    show: bool = typer.Option(False, "--show", help="Display current configuration"),
    reset: bool = typer.Option(False, "--reset", help="Reset configuration to defaults"),
    export: str = typer.Option(None, "--export", help="Export config to file"),
    google_api_key: str = typer.Option(None, "--google-api-key", help="Set Google API key"),
    google_model: str = typer.Option(None, "--google-model", help="Set Google AI model"),
    db_path: str = typer.Option(None, "--db-path", help="Set database path"),
    user_name: str = typer.Option(None, "--user-name", help="Set user name"),
    user_persona: str = typer.Option(None, "--user-persona", help="Set user persona"),
    always_debug: bool = typer.Option(False, "--always-debug", help="Always enable debug mode"),
    self_debug: bool = typer.Option(False, "--self-debug", help="Disable always debug mode"),
    disable_colors: bool = typer.Option(False, "--disable-colors", help="Disable colored output"),
    enable_colors: bool = typer.Option(False, "--enable-colors", help="Enable colored output"),
    restore: bool = typer.Option(False, "--restore", help="Restore configuration from backup"),
):
    """
    Manage Pixella configuration (.env settings)
    """
    try:
        from config import (
            init_config,
            show_config,
            reset_config,
            export_config,
            load_env,
            save_env,
            restore_config,
            get_cli_value,
        )
        
        # Handle different config operations
        if init:
            init_config(overrides={})
        elif show:
            show_config()
        elif reset:
            reset_config()
        elif export:
            export_config(export)
        elif restore:
            restore_config()
        elif disable_colors:
            set_config("DISABLE_COLORS", "true")
            console.print("[yellow]Colored output disabled.[/yellow]")
        elif enable_colors:
            set_config("DISABLE_COLORS", "false")
            console.print("[green]Colored output enabled.[/green]")
        elif always_debug:
            set_config("ALWAYS_DEBUG", "true")
            console.print("[green]Always debug mode enabled.[/green]")
        elif self_debug:
            set_config("ALWAYS_DEBUG", "false")
            console.print("[yellow]Always debug mode disabled.[/yellow]")
        elif any([
            google_api_key,
            google_model,
            db_path,
            user_name,
            user_persona,
        ]):
            # Update specific settings
            current_env = load_env()
            
            # Build updates dict with only provided values
            updates: Dict[str, str] = dict()
            if google_api_key:
                updates["GOOGLE_API_KEY"] = google_api_key
            if google_model:
                updates["GOOGLE_AI_MODEL"] = google_model
            if db_path:
                updates["CHROMA_DB_PATH"] = db_path
            if user_name:
                updates["USER_NAME"] = user_name
            if user_persona:
                updates["USER_PERSONA"] = user_persona
            
            # Merge and save
            current_env.update(updates)
            save_env(current_env)
            
            console.print(
                Panel(
                    "[green]✓ Configuration updated successfully[/green]",
                    title="Config",
                    border_style="green"
                )
            )
            show_config()
        else:
            # No operation specified - show help
            console.print(
                Panel(
                    "[cyan]Use one of:[/cyan]\n"
                    "[yellow]--init[/yellow]           - Interactive setup\n"
                    "[yellow]--show[/yellow]           - Display configuration\n"
                    "[yellow]--reset[/yellow]          - Reset to defaults\n"
                    "[yellow]--restore[/yellow]        - Restore config\n"
                    "[yellow]--export[/yellow] PATH    - Export to file\n"
                    "[yellow]--disable-colors[/yellow]  - Disable colors\n"
                    "[yellow]--enable-colors[/yellow]   - Enable colors\n"
                    "[yellow]--always-debug[/yellow]    - Always enable debug mode\n"
                    "[yellow]--self-debug[/yellow]      - Disable always debug mode\n"
                    "[yellow]--google-api-key[/yellow]  VALUE\n"
                    "[yellow]--google-model[/yellow]    VALUE\n"
                    "[yellow]--db-path[/yellow]        PATH\n"
                    "[yellow]--user-name[/yellow]      NAME\n"
                    "[yellow]--user-persona[/yellow]   TEXT",
                    title="Config Options",
                    border_style="cyan"
                )
            )
    except ImportError as e:
        console.print(
            Panel(
                f"[red]Error importing config module: {str(e)}[/red]",
                title="Error",
                border_style="red"
            )
        )
        sys.exit(1)
    except Exception as e:
        console.print(
            Panel(
                f"[red]Configuration error: {str(e)}[/red]",
                title="Error",
                border_style="red"
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    app()
