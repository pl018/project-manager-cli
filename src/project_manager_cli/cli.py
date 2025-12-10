#!/usr/bin/env python3
"""Command-line interface for the project manager CLI."""

import os
import sys
from pathlib import Path
import click
import yaml
from typing import Dict, Any
from rich.console import Console
from rich import print as rprint

from .config import Config, ConfigManager
from .app import Application
from .rich_help import RichGroup, RichCommand

# Initialize Rich console
console = Console()

# Safe emoji printing for Windows
def safe_emoji(emoji: str, fallback: str = "") -> str:
    """Return emoji if supported, otherwise return fallback."""
    try:
        # Test if emoji can be encoded
        emoji.encode(sys.stdout.encoding or 'utf-8')
        return emoji
    except (UnicodeEncodeError, AttributeError):
        return fallback


@click.group(cls=RichGroup)
@click.version_option()
def cli():
    """Manage your project metadata and Cursor integration."""
    pass


@cli.command(cls=RichCommand)
@click.option('--db-path', type=click.Path(), help='Path to store the SQLite database')
@click.option('--projects-file', type=click.Path(), help='Path to Cursor projects.json file')
@click.option('--openai-api-key', help='OpenAI API key for AI tagging')
@click.option('--force', is_flag=True, help='Overwrite existing configuration')
def init(db_path, projects_file, openai_api_key, force):
    """Initialize the project manager CLI configuration.
    
    Sets up the database path, Cursor projects file location, and optional OpenAI API key.
    If options are not provided, you'll be prompted interactively.
    
    Examples:
    
    # Interactive setup (recommended for first time)
    $ pm-cli init
    
    # Set all options at once
    $ pm-cli init --db-path ~/.myaibs/projects.db --projects-file ~/cursor/projects.json --openai-api-key sk-...
    
    # Force reconfiguration
    $ pm-cli init --force
    
    # Set only database path (will prompt for others)
    $ pm-cli init --db-path ~/my-projects.db
    """
    console.print("[bold cyan]>>> Initializing Project Manager CLI...[/bold cyan]")
    
    config_manager = ConfigManager()
    
    # Check if config already exists
    if config_manager.config_exists() and not force:
        console.print("[yellow]! Configuration already exists![/yellow]")
        if not click.confirm("Do you want to reconfigure?"):
            console.print("[dim]Configuration unchanged.[/dim]")
            return
    
    # Get database path
    if not db_path:
        default_db_path = config_manager.get_default_db_path()
        db_path = click.prompt(
            f'Database path', 
            default=str(default_db_path),
            type=click.Path()
        )
    
    # Get projects file path
    if not projects_file:
        default_projects_file = config_manager.get_default_projects_file()
        projects_file = click.prompt(
            f'Cursor projects.json path',
            default=str(default_projects_file),
            type=click.Path()
        )
    
    # Get OpenAI API key
    if not openai_api_key:
        openai_api_key = click.prompt(
            'OpenAI API Key (optional, for AI tagging)',
            default='',
            hide_input=True,
            show_default=False
        )
    
    # Create configuration
    config_data = {
        'db_path': str(Path(db_path).resolve()),
        'projects_file': str(Path(projects_file).resolve()),
        'openai_api_key': openai_api_key if openai_api_key else None,
        'default_tag': 'app',
        'max_files_to_analyze': 10,
        'max_content_length': 10000,
        'exclude_dirs': [
            'node_modules', 'venv', '.git', '__pycache__', 
            'dist', 'build', 'target', '.docs', '.vscode'
        ],
        'important_extensions': [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', 
            '.rs', '.c', '.cpp', '.h', '.cs', '.php', '.rb', 
            '.md', '.html', '.css', '.json', '.yml', '.yaml'
        ]
    }
    
    # Save configuration
    try:
        config_manager.save_config(config_data)
        console.print(f"[green]√ Configuration saved to:[/green] [cyan]{config_manager.config_file}[/cyan]")
        console.print(f"[green]  Database will be stored at:[/green] [cyan]{config_data['db_path']}[/cyan]")
        console.print(f"[green]  Projects file:[/green] [cyan]{config_data['projects_file']}[/cyan]")
        
        # Create database directory if it doesn't exist
        Path(config_data['db_path']).parent.mkdir(parents=True, exist_ok=True)
        
        console.print("\n[bold green]>>> Project Manager CLI is ready to use![/bold green]")
        console.print("[dim]Run 'pm-cli --help' to see available commands.[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]ERROR: Saving configuration failed:[/bold red] {e}")
        sys.exit(1)


@cli.command(cls=RichCommand)
@click.option('--test', is_flag=True, help='Run in test mode (no changes saved)')
@click.argument('directory', type=click.Path(exists=True), default='.')
def run(test, directory):
    """Run the project manager on a directory.
    
    Analyzes the specified directory, extracts project metadata, and updates the database.
    Uses AI tagging if OpenAI API key is configured.
    
    Examples:
    
    # Run on current directory
    $ pm-cli run
    
    # Run on specific directory
    $ pm-cli run /path/to/my-project
    
    # Test mode - analyze without saving changes
    $ pm-cli run --test
    
    # Test specific project
    $ pm-cli run --test ~/projects/my-app
    """
    try:
        config_manager = ConfigManager()
        if not config_manager.config_exists():
            console.print("[red]ERROR: Configuration not found.[/red] Run [cyan]'pm-cli init'[/cyan] first.")
            sys.exit(1)
        
        # Change to the target directory
        original_dir = os.getcwd()
        os.chdir(directory)
        
        try:
            app = Application(test_mode=test)
            app.run()
        finally:
            os.chdir(original_dir)
            
    except Exception as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
        sys.exit(1)


@cli.command(cls=RichCommand)
def config():
    """Show current configuration.
    
    Displays all configuration settings including database path, projects file,
    and other settings. API keys are masked for security.
    
    Examples:
    
    # View current configuration
    $ pm-cli config
    """
    config_manager = ConfigManager()
    
    if not config_manager.config_exists():
        console.print("[red]Configuration not found.[/red] Run [cyan]'pm-cli init'[/cyan] first.")
        return
    
    config_data = config_manager.load_config()
    
    from rich.table import Table
    
    console.print("\n[bold cyan]Current Configuration[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold yellow", box=None)
    table.add_column("Setting", style="cyan", width=25)
    table.add_column("Value", style="white")
    
    for key, value in config_data.items():
        if key == 'openai_api_key' and value:
            value = '[dim]***hidden***[/dim]'
        table.add_row(key, str(value))
    
    console.print(table)
    console.print()


@cli.command(cls=RichCommand)
@click.confirmation_option(prompt='Are you sure you want to reset the configuration?')
def reset():
    """Reset configuration to defaults.
    
    Removes the configuration file. You'll need to run 'init' again to reconfigure.
    This does NOT delete your project database.
    
    Examples:
    
    # Reset configuration (will prompt for confirmation)
    $ pm-cli reset
    """
    config_manager = ConfigManager()
    
    if config_manager.config_exists():
        config_manager.config_file.unlink()
        console.print("[green]√ Configuration reset.[/green] Run [cyan]'pm-cli init'[/cyan] to reconfigure.")
    else:
        console.print("[dim]INFO: No configuration found to reset.[/dim]")


@cli.command(cls=RichCommand)
def tui():
    """Launch the interactive TUI (Terminal User Interface).
    
    Opens a full-screen interactive interface for browsing and managing projects.
    Navigate with arrow keys, search with '/', and press '?' for help.
    
    Examples:
    
    # Launch interactive UI
    $ pm-cli tui
    
    Navigation:
    - Arrow keys: Navigate through projects
    - Enter: View project details
    - /: Search projects
    - f: Toggle favorites filter
    - q: Quit
    """
    try:
        # Import here to avoid loading TUI dependencies for other commands
        from ui.app import run_tui
        
        console.print("[bold cyan]>>> Launching Project Manager TUI...[/bold cyan]")
        run_tui()
        
    except ImportError as e:
        console.print(f"[red]ERROR: Failed to import TUI module:[/red] {e}")
        console.print("[yellow]Make sure textual is installed:[/yellow] [cyan]pip install textual[/cyan]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n\n[bold]Goodbye![/bold]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]ERROR: Launching TUI failed:[/bold red] {e}")
        sys.exit(1)


@cli.command(name='list', cls=RichCommand)
@click.option('--favorites', '-f', is_flag=True, help='Show only favorite projects')
@click.option('--tag', '-t', multiple=True, help='Filter by tag (can be used multiple times)')
@click.option('--search', '-s', help='Search projects by name or path')
def list_projects(favorites, tag, search):
    """List all projects in a formatted table.
    
    Displays projects with their names, paths, tags, and other metadata.
    Supports filtering by favorites, tags, and search terms.
    
    Examples:
    
    # List all projects
    $ pm-cli list
    
    # List only favorite projects
    $ pm-cli list --favorites
    $ pm-cli list -f
    
    # Filter by single tag
    $ pm-cli list --tag python
    $ pm-cli list -t python
    
    # Filter by multiple tags (AND logic)
    $ pm-cli list --tag python --tag web
    $ pm-cli list -t python -t web
    
    # Search by name or path
    $ pm-cli list --search "my-app"
    $ pm-cli list -s backend
    
    # Combine filters
    $ pm-cli list --favorites --tag python --search "api"
    $ pm-cli list -f -t python -s api
    """
    try:
        from core.database import DatabaseManager
        from .formatters import ProjectTableFormatter
        
        # Get database path from config
        config_manager = ConfigManager()
        if not config_manager.config_exists():
            console.print("[red]ERROR: Configuration not found.[/red] Run [cyan]'pm-cli init'[/cyan] first.")
            sys.exit(1)
        
        config_data = config_manager.load_config()
        db_path = config_data.get('db_path')
        
        if not db_path:
            console.print("[red]ERROR: Database path not configured.[/red]")
            sys.exit(1)
        
        # Connect to database and fetch projects
        db = DatabaseManager(db_path=db_path)
        db.connect()
        
        try:
            # Use search with filters
            if search or tag or favorites:
                projects = db.search_projects(
                    query=search or "",
                    tags=list(tag) if tag else None,
                    favorites_only=favorites
                )
            else:
                projects = db.get_all_projects(enabled_only=True)
            
            # Format and display
            formatter = ProjectTableFormatter()
            formatter.format_projects(projects)
            
        finally:
            db.close()
            
    except ImportError as e:
        console.print(f"[red]ERROR: Failed to import required modules:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]ERROR: Listing projects failed:[/bold red] {e}")
        sys.exit(1)


@cli.command(cls=RichCommand)
@click.option('--no-open', is_flag=True, help='Generate HTML but do not open in browser')
@click.option('--output', '-o', type=click.Path(), help='Output file path (defaults to temp directory)')
def html(no_open, output):
    """Generate and open an HTML page with project list.
    
    Creates a beautiful, interactive HTML page with all your projects.
    Includes search, filtering, and sorting capabilities. By default,
    opens in your web browser automatically.
    
    Examples:
    
    # Generate and open HTML in browser
    $ pm-cli html
    
    # Generate without opening browser
    $ pm-cli html --no-open
    
    # Save to specific location
    $ pm-cli html --output ~/projects.html
    $ pm-cli html -o ~/Desktop/my-projects.html
    
    # Generate to file without opening
    $ pm-cli html --output report.html --no-open
    """
    try:
        from core.database import DatabaseManager
        from .formatters import HTMLGenerator
        
        # Get database path from config
        config_manager = ConfigManager()
        if not config_manager.config_exists():
            console.print("[red]ERROR: Configuration not found.[/red] Run [cyan]'pm-cli init'[/cyan] first.")
            sys.exit(1)
        
        config_data = config_manager.load_config()
        db_path = config_data.get('db_path')
        
        if not db_path:
            console.print("[red]ERROR: Database path not configured.[/red]")
            sys.exit(1)
        
        # Connect to database and fetch projects
        db = DatabaseManager(db_path=db_path)
        db.connect()
        
        try:
            projects = db.get_all_projects(enabled_only=True)
            
            # Generate HTML
            output_dir = str(Path(output).parent) if output else None
            generator = HTMLGenerator(output_dir=output_dir)
            
            # If specific output path provided, we need to handle it
            if output:
                output_path = generator.generate(projects, open_browser=False)
                # Move to desired location if different
                import shutil
                final_path = Path(output)
                if Path(output_path) != final_path:
                    shutil.move(output_path, final_path)
                    output_path = str(final_path)
                
                if not no_open:
                    import webbrowser
                    webbrowser.open(f"file://{Path(output_path).resolve()}")
            else:
                output_path = generator.generate(projects, open_browser=not no_open)
            
            console.print(f"[green]HTML page generated:[/green] [cyan]{output_path}[/cyan]")
            
            if not no_open:
                console.print("[dim]Opening in default browser...[/dim]")
            
        finally:
            db.close()
            
    except ImportError as e:
        console.print(f"[red]ERROR: Failed to import required modules:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]ERROR: Generating HTML failed:[/bold red] {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
