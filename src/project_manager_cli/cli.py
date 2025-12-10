#!/usr/bin/env python3
"""Command-line interface for the project manager CLI."""

import os
import sys
from pathlib import Path
import click
import yaml
from typing import Dict, Any

from .config import Config, ConfigManager
from .app import Application


@click.group()
@click.version_option()
def cli():
    """Project Manager CLI - Manage your project metadata and Cursor integration."""
    pass


@cli.command()
@click.option('--db-path', type=click.Path(), help='Path to store the SQLite database')
@click.option('--projects-file', type=click.Path(), help='Path to Cursor projects.json file')
@click.option('--openai-api-key', help='OpenAI API key for AI tagging')
@click.option('--force', is_flag=True, help='Overwrite existing configuration')
def init(db_path, projects_file, openai_api_key, force):
    """Initialize the project manager CLI configuration."""
    click.echo("🚀 Initializing Project Manager CLI...")
    
    config_manager = ConfigManager()
    
    # Check if config already exists
    if config_manager.config_exists() and not force:
        click.echo("⚠️  Configuration already exists!")
        if not click.confirm("Do you want to reconfigure?"):
            click.echo("Configuration unchanged.")
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
        click.echo(f"✅ Configuration saved to: {config_manager.config_file}")
        click.echo(f"📁 Database will be stored at: {config_data['db_path']}")
        click.echo(f"📄 Projects file: {config_data['projects_file']}")
        
        # Create database directory if it doesn't exist
        Path(config_data['db_path']).parent.mkdir(parents=True, exist_ok=True)
        
        click.echo("\n🎉 Project Manager CLI is ready to use!")
        click.echo("Run 'project-manager-cli --help' to see available commands.")
        
    except Exception as e:
        click.echo(f"❌ Error saving configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--test', is_flag=True, help='Run in test mode (no changes saved)')
@click.argument('directory', type=click.Path(exists=True), default='.')
def run(test, directory):
    """Run the project manager on a directory."""
    try:
        config_manager = ConfigManager()
        if not config_manager.config_exists():
            click.echo("❌ Configuration not found. Run 'project-manager-cli init' first.", err=True)
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
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def config():
    """Show current configuration."""
    config_manager = ConfigManager()
    
    if not config_manager.config_exists():
        click.echo("❌ Configuration not found. Run 'project-manager-cli init' first.", err=True)
        return
    
    config_data = config_manager.load_config()
    
    click.echo("📋 Current Configuration:")
    click.echo("=" * 40)
    for key, value in config_data.items():
        if key == 'openai_api_key' and value:
            value = '***hidden***'
        click.echo(f"{key}: {value}")


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to reset the configuration?')
def reset():
    """Reset configuration to defaults."""
    config_manager = ConfigManager()
    
    if config_manager.config_exists():
        config_manager.config_file.unlink()
        click.echo("✅ Configuration reset. Run 'project-manager-cli init' to reconfigure.")
    else:
        click.echo("ℹ️  No configuration found to reset.")


@cli.command()
def tui():
    """Launch the interactive TUI (Terminal User Interface)."""
    try:
        # Import here to avoid loading TUI dependencies for other commands
        from ui.app import run_tui
        
        click.echo("🚀 Launching Project Manager TUI...")
        run_tui()
        
    except ImportError as e:
        click.echo(f"❌ Failed to import TUI module: {e}", err=True)
        click.echo("Make sure textual is installed: pip install textual", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ Error launching TUI: {e}", err=True)
        sys.exit(1)


@cli.command(name='list')
@click.option('--favorites', '-f', is_flag=True, help='Show only favorite projects')
@click.option('--tag', '-t', multiple=True, help='Filter by tag (can be used multiple times)')
@click.option('--search', '-s', help='Search projects by name or path')
def list_projects(favorites, tag, search):
    """List all projects in a formatted table."""
    try:
        from core.database import DatabaseManager
        from .formatters import ProjectTableFormatter
        
        # Get database path from config
        config_manager = ConfigManager()
        if not config_manager.config_exists():
            click.echo("❌ Configuration not found. Run 'pm-cli init' first.", err=True)
            sys.exit(1)
        
        config_data = config_manager.load_config()
        db_path = config_data.get('db_path')
        
        if not db_path:
            click.echo("❌ Database path not configured.", err=True)
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
        click.echo(f"❌ Failed to import required modules: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error listing projects: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--no-open', is_flag=True, help='Generate HTML but do not open in browser')
@click.option('--output', '-o', type=click.Path(), help='Output file path (defaults to temp directory)')
def html(no_open, output):
    """Generate and open an HTML page with project list."""
    try:
        from core.database import DatabaseManager
        from .formatters import HTMLGenerator
        
        # Get database path from config
        config_manager = ConfigManager()
        if not config_manager.config_exists():
            click.echo("❌ Configuration not found. Run 'pm-cli init' first.", err=True)
            sys.exit(1)
        
        config_data = config_manager.load_config()
        db_path = config_data.get('db_path')
        
        if not db_path:
            click.echo("❌ Database path not configured.", err=True)
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
            
            click.echo(f"HTML page generated: {output_path}")
            
            if not no_open:
                click.echo("Opening in default browser...")
            
        finally:
            db.close()
            
    except ImportError as e:
        click.echo(f"❌ Failed to import required modules: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error generating HTML: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
