#!/usr/bin/env python3
"""
Pixella Configuration Management
Handles .env file creation, editing, and backup
"""

import os
import shutil
from pathlib import Path
from typing import Dict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Global console instance, initialized directly
CONFIG_CONSOLE: Console = Console()


def get_project_root() -> Path:
    """
    Finds the project root directory by looking for a .git folder,
    README.md, or pyproject.toml in parent directories.
    """
    current_path = Path(__file__).parent
    while current_path != current_path.parent: # Stop at filesystem root
        if (current_path / ".git").is_dir() or \
           (current_path / "README.md").is_file() or \
           (current_path / "pyproject.toml").is_file():
            return current_path
        current_path = current_path.parent
    return Path(__file__).parent # Fallback to current file's parent if no root found



def set_config_console(console_instance: Console):
    global CONFIG_CONSOLE
    CONFIG_CONSOLE = console_instance

def get_config_console() -> Console:
    return CONFIG_CONSOLE

ENV_PATH = Path(__file__).parent / ".env"
ENV_BAK_PATH = Path(__file__).parent / ".env.bak"
ENV_TEMPLATE_PATH = Path(__file__).parent / ".env.template"

# Template with default values and descriptions
CONFIG_TEMPLATE = {
    "google_api_key": {
        "env_name": "GOOGLE_API_KEY",
        "description": "Your Google Generative AI API key",
        "default": "",
        "required": True
    },
    "google_model": {
        "env_name": "GOOGLE_AI_MODEL",
        "description": "Google AI model to use (Note: Langchain's legacy google-generativeai might not support all new models)",
        "default": "gemini-2.5-flash",
        "required": False
    },
    "db_path": {
        "env_name": "DB_PATH",
        "description": "ChromaDB database path",
        "default": str(get_project_root() / "db" / "chroma"),
        "required": False
    },
    "user_name": {
        "env_name": "USER_NAME",
        "description": "Your name for personalized responses",
        "default": "User",
        "required": False
    },
    "user_persona": {
        "env_name": "USER_PERSONA",
        "description": "Your persona/profile description",
        "default": "",
        "required": False
    },
    "memory_path": {
        "env_name": "MEMORY_PATH",
        "description": "Session memory storage path",
        "default": str(get_project_root() / "data" / "memory"),
        "required": False
    },
    "embedding_model": {
        "env_name": "EMBEDDING_MODEL",
        "description": "Embedding model for RAG (Google Generative AI)",
        "default": "models/embedding-001",
        "required": False
    },
    "always_debug": {
        "env_name": "ALWAYS_DEBUG",
        "description": "Always show debug logs",
        "default": "false",
        "required": False
    },
    "disable_colors": {
        "env_name": "DISABLE_COLORS",
        "description": "Disable colored output",
        "default": "false",
        "required": False
    }
}


def load_env() -> Dict[str, str]:
    """Load current .env file as dictionary"""
    if not ENV_PATH.exists():
        return {}
    
    env_dict = {}
    with open(ENV_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_dict[key.strip()] = value.strip()
    
    return env_dict


def get_config() -> Dict[str, str]:
    """Get current configuration as a dictionary, resolving paths against project root."""
    config_dict = load_env()
    project_root = get_project_root()

    # Resolve DB_PATH and MEMORY_PATH against project_root if they are relative
    for key_name, template_info in CONFIG_TEMPLATE.items():
        env_name = template_info["env_name"]
        if env_name in ["DB_PATH", "MEMORY_PATH"]:
            # Get the value from loaded config or its default
            current_value = config_dict.get(env_name, template_info["default"])
            
            resolved_path: Path
            if not Path(str(current_value)).is_absolute():
                # If the path is relative, resolve it against the project root
                resolved_path = project_root / Path(str(current_value))
            else:
                # If the path is already absolute, use it as is
                resolved_path = Path(str(current_value))
            
            # Ensure the directory exists
            resolved_path.mkdir(parents=True, exist_ok=True)
            config_dict[env_name] = str(resolved_path)
    
    return config_dict
def set_config(key: str, value: str) -> None:
    """Set a specific configuration value and save it."""
    env_dict = load_env()
    env_dict[key] = value
    save_env(env_dict)



def save_env(env_dict: Dict[str, str]) -> None:
    """Save environment variables to .env file"""
    console = get_config_console()
    # Write new .env
    with open(ENV_PATH, "w") as f:
        f.write("# Pixella Configuration\n")
        f.write("# Generated by pixella config command\n\n")
        
        for key, value in sorted(env_dict.items()):
            f.write(f"{key}={value}\n")
    
    # Create backup if .env exists
    if ENV_PATH.exists():
        shutil.copy2(ENV_PATH, ENV_BAK_PATH)
        console.print(f"[dim]Backup created: {ENV_BAK_PATH}[/dim]")
    
    
    console.print(f"[green]✓ Configuration saved to {ENV_PATH}[/green]")

def get_cli_value(key: str, config: Dict) -> str:
    """Get value from command line argument or prompt user"""
    template = CONFIG_TEMPLATE.get(key.lower())
    
    if not template:
        return ""
    
    # Check if already in config
    env_name = template["env_name"]
    if env_name in config:
        return config[env_name]
    
    # Use default or prompt
    if template["default"]:
        return template["default"]
    
    return ""

def init_config(overrides: Dict[str, str]) -> None:
    """Initialize or update configuration interactively"""
    console = get_config_console()
    console.print(Panel("[bold cyan]Pixella Interactive Configuration[/bold cyan]", border_style="cyan"))
    env_dict = load_env()

    # Apply any overrides from command line
    for cli_key, value in overrides.items():
        if cli_key in CONFIG_TEMPLATE:
            template = CONFIG_TEMPLATE[cli_key]
            env_dict[template["env_name"]] = value

    # Interactive session for all settings
    for key, template in CONFIG_TEMPLATE.items():
        env_name = template["env_name"]
        description = template["description"]
        default = template.get("default", "")
        current_value = env_dict.get(env_name, "")

        # Hide sensitive values in prompt
        display_value = current_value
        if "key" in key.lower() and current_value:
            display_value = current_value[:4] + "***" + current_value[-4:]
        
        prompt_text = f"[yellow]Enter {key}[/yellow] [dim](current: {display_value or 'Not set'})[/dim]: "
        if not current_value and default:
            prompt_text = f"[yellow]Enter {key}[/yellow] [dim](default: {default})[/dim]: "
        
        console.print(f"\n[cyan]{description}[/cyan]")
        
        if template.get("readonly"):
            console.print(f"[dim]  (read-only, will be set to default: {default})[/dim]")
            env_dict[env_name] = default
            continue

        new_value = console.input(prompt_text)

        # If user entered a value, use it
        if new_value:
            env_dict[env_name] = new_value
        # If user did not enter a value, but there was a current value, keep it
        elif current_value:
            env_dict[env_name] = current_value
        # If no new value and no current value, use the default
        else:
            env_dict[env_name] = default

        # Handle required fields that are still empty
        if template.get("required") and not env_dict.get(env_name):
            while not env_dict.get(env_name):
                required_prompt = f"[bold yellow]Enter {key} (required)[/bold yellow]: "
                env_dict[env_name] = console.input(required_prompt)

    save_env(env_dict)
    console.print("\n[bold green]Configuration saved![/bold green]")
    show_config()

def show_config() -> None:
    """Display current configuration"""
    console = get_config_console()
    env_dict = load_env()
    
    table = Table(title="[bold cyan]Pixella Configuration[/bold cyan]")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Description", style="dim")
    
    for key, template in CONFIG_TEMPLATE.items():
        env_name = template["env_name"]
        value = env_dict.get(env_name, template["default"] or "[not set]")
        
        # Hide sensitive values
        if "key" in key.lower() and value and value != "[not set]":
            value = value[:10] + "***"
        
        table.add_row(env_name, value, template["description"])
    
    console.print(table)

def reset_config() -> None:
    """Reset configuration to defaults/empty"""
    console = get_config_console()
    if console.input("[yellow]Are you sure? This will reset all settings. (yes/no): [/yellow]") != "yes":
        console.print("[dim]Cancelled[/dim]")
        return

    # Create backup
    if ENV_PATH.exists():
        shutil.copy2(ENV_PATH, ENV_BAK_PATH)
        console.print(f"[dim]Backup created: {ENV_BAK_PATH}[/dim]")

    env_dict = {}
    for key, template in CONFIG_TEMPLATE.items():
        env_dict[template["env_name"]] = template["default"]
    
    save_env(env_dict)

    console.print("[green]✓ Configuration reset to defaults[/green]")

def restore_config():
    """Restore config from backup"""
    console = get_config_console()
    if not ENV_BAK_PATH.exists():
        console.print("[red]✗ No backup file found to restore.[/red]")
        return

    try:
        shutil.copy2(ENV_BAK_PATH, ENV_PATH)
        console.print(f"[green]✓ Config restored from backup: {ENV_BAK_PATH}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Error restoring config: {e}[/red]")
        


def generate_env_template() -> None:
    """Generate .env.template file with all available options"""
    console = get_config_console()
    template_content = "# Pixella Configuration Template\n"
    template_content += "# Copy this file to .env and fill in your values\n"
    template_content += "# Required fields are marked with [REQUIRED]\n\n"
    
    for key, config in CONFIG_TEMPLATE.items():
        env_name = config["env_name"]
        description = config["description"]
        default = config["default"]
        required = "[REQUIRED]" if config.get("required") else "[OPTIONAL]"
        readonly = " [READ-ONLY]" if config.get("readonly") else ""
        
        template_content += f"# {description} {required}{readonly}\n"
        template_content += f"# Default: {default}\n"
        
        if config.get("readonly"):
            template_content += f"# {env_name}={default}\n\n"
        else:
            template_content += f"{env_name}={default}\n\n"
    
    with open(ENV_TEMPLATE_PATH, "w") as f:
        f.write(template_content)
    
    console.print(f"[green]✓ Template generated: {ENV_TEMPLATE_PATH}[/green]")

def export_config(filename: str) -> None:
    """Export configuration to file"""
    console = get_config_console()
    env_dict = load_env()
    export_path = Path(filename)
    
    with open(export_path, "w") as f:
        f.write("# Pixella Configuration Export\n")
        for key, value in sorted(env_dict.items()):
            # Don't export sensitive keys
            if "key" in key.lower():
                f.write(f"# {key}=<your_key_here>\n")
            else:
                f.write(f"{key}={value}\n")
    
    console.print(f"[green]✓ Configuration exported to {export_path}[/green]")

def list_config_options() -> None:
    """Display all available configuration options"""
    console = get_config_console()
    console.print("\n[bold cyan]Available Configuration Options:[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="yellow")
    table.add_column("Description", style="white")
    table.add_column("Default", style="dim")
    table.add_column("Type", style="blue")
    
    for key, config in CONFIG_TEMPLATE.items():
        setting = config["env_name"]
        description = config["description"]
        default = config["default"]
        req_type = "REQUIRED" if config.get("required") else "OPTIONAL"
        if config.get("readonly"):
            req_type += " (R/O)"
        
        table.add_row(setting, description, default, req_type)
    
    console.print(table)
    console.print()