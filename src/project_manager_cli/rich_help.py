"""Rich-enhanced help formatting for Click CLI."""

from typing import Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax


console = Console()


class RichGroup(click.Group):
    """Custom Click Group with Rich formatting."""
    
    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Format help with Rich."""
        console = Console()
        
        # Title
        console.print()
        console.print(
            Panel(
                "[bold cyan]Project Manager CLI[/bold cyan]\n"
                "[dim]Manage your project metadata and Cursor integration[/dim]",
                border_style="cyan",
                padding=(1, 2)
            )
        )
        
        # Usage
        console.print("\n[bold yellow]Usage:[/bold yellow]")
        console.print(f"  [dim]$[/dim] [green]pm-cli[/green] [cyan][OPTIONS][/cyan] [yellow]COMMAND[/yellow] [cyan][ARGS]...[/cyan]")
        
        # Common Examples
        console.print("\n[bold yellow]Common Examples:[/bold yellow]")
        examples = [
            ("Initialize the CLI", "pm-cli init"),
            ("Register current project", "pm-cli run"),
            ("List all projects", "pm-cli list"),
            ("List favorites only", "pm-cli list --favorites"),
            ("Search projects", 'pm-cli list --search "my-app"'),
            ("Generate HTML report", "pm-cli html"),
            ("Launch interactive UI", "pm-cli tui"),
        ]
        
        for desc, cmd in examples:
            console.print(f"  [dim]# {desc}[/dim]")
            console.print(f"  [dim]$[/dim] [green]{cmd}[/green]")
            console.print()
        
        # Commands table
        console.print("[bold yellow]Available Commands:[/bold yellow]")
        table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
        table.add_column("Command", style="green", width=12)
        table.add_column("Description", style="white")
        
        commands = sorted(self.list_commands(ctx))
        for cmd_name in commands:
            cmd = self.get_command(ctx, cmd_name)
            if cmd and cmd.help:
                # Get first line of help text
                help_text = cmd.help.split('\n')[0].strip()
                table.add_row(cmd_name, help_text)
        
        console.print(table)
        
        # Options
        if self.params:
            console.print("\n[bold yellow]Options:[/bold yellow]")
            for param in self.params:
                self._print_param(param)
        
        # Footer
        console.print("\n[bold yellow]Get Detailed Help:[/bold yellow]")
        console.print("  [dim]$[/dim] [green]pm-cli[/green] [yellow]COMMAND[/yellow] [cyan]--help[/cyan]")
        console.print()
    
    def _print_param(self, param: click.Parameter) -> None:
        """Print a parameter with Rich formatting."""
        opts = []
        for opt in param.opts:
            if opt.startswith('--'):
                opts.append(f"[cyan]{opt}[/cyan]")
            else:
                opts.append(f"[cyan]{opt}[/cyan]")
        
        opts_str = ", ".join(opts)
        help_text = param.help or ""
        console.print(f"  {opts_str}  [dim]{help_text}[/dim]")


class RichCommand(click.Command):
    """Custom Click Command with Rich formatting."""
    
    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Format command help with Rich."""
        console = Console()
        
        # Title
        console.print()
        console.print(
            Panel(
                f"[bold cyan]pm-cli {self.name}[/bold cyan]\n"
                f"[dim]{self.get_short_help_str()}[/dim]",
                border_style="cyan",
                padding=(1, 2)
            )
        )
        
        # Usage
        console.print("\n[bold yellow]Usage:[/bold yellow]")
        pieces = self.collect_usage_pieces(ctx)
        prog_name = "[green]pm-cli[/green] [yellow]{}[/yellow]".format(self.name)
        usage = " ".join([prog_name] + [f"[cyan]{p}[/cyan]" for p in pieces])
        console.print(f"  [dim]$[/dim] {usage}")
        
        # Description
        if self.help:
            console.print("\n[bold yellow]Description:[/bold yellow]")
            # Get description (before Examples section)
            help_parts = self.help.split('Examples:')
            description = help_parts[0].strip()
            for line in description.split('\n'):
                line = line.strip()
                if line:
                    console.print(f"  {line}")
        
        # Examples
        if self.help and 'Examples:' in self.help:
            console.print("\n[bold yellow]Examples:[/bold yellow]")
            examples_text = self.help.split('Examples:')[1].strip()
            
            # Parse examples
            lines = examples_text.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith('#'):
                    # Comment line
                    console.print(f"  [dim]{line}[/dim]")
                elif line.startswith('$') or line.startswith('pm-cli') or line.startswith('project-manager-cli'):
                    # Command line
                    cmd = line.replace('$', '').strip()
                    cmd = cmd.replace('project-manager-cli', 'pm-cli')
                    # Highlight command
                    parts = cmd.split()
                    if parts:
                        formatted_cmd = f"[green]{parts[0]}[/green]"
                        if len(parts) > 1:
                            formatted_cmd += f" [yellow]{parts[1]}[/yellow]"
                        if len(parts) > 2:
                            formatted_cmd += " " + " ".join([f"[cyan]{p}[/cyan]" for p in parts[2:]])
                        console.print(f"  [dim]$[/dim] {formatted_cmd}")
                elif line:
                    # Other content
                    console.print(f"    [dim]{line}[/dim]")
                i += 1
            console.print()
        
        # Options
        if self.params:
            console.print("[bold yellow]Options:[/bold yellow]")
            
            # Create table for options
            table = Table(show_header=False, box=None, padding=(0, 2), show_edge=False)
            table.add_column("Option", style="cyan", width=30)
            table.add_column("Description", style="white")
            
            for param in self.params:
                if isinstance(param, click.Option):
                    opts = []
                    for opt in param.opts:
                        opts.append(opt)
                    
                    opts_str = ", ".join(opts)
                    
                    # Add type info if present
                    if param.type and param.type.name != 'BOOL':
                        opts_str += f" [{param.type.name}]"
                    
                    help_text = param.help or ""
                    table.add_row(opts_str, help_text)
            
            console.print(table)
        
        # Arguments
        args = [p for p in self.params if isinstance(p, click.Argument)]
        if args:
            console.print("\n[bold yellow]Arguments:[/bold yellow]")
            table = Table(show_header=False, box=None, padding=(0, 2), show_edge=False)
            table.add_column("Argument", style="yellow", width=30)
            table.add_column("Description", style="white")
            
            for arg in args:
                arg_name = arg.name.upper()
                help_text = arg.help or "Required argument"
                if not arg.required:
                    help_text += " (optional)"
                table.add_row(arg_name, help_text)
            
            console.print(table)
        
        console.print()


def print_command_examples(examples: list[tuple[str, str]]) -> None:
    """Print formatted command examples."""
    for desc, cmd in examples:
        console.print(f"  [dim]# {desc}[/dim]")
        
        # Highlight command
        parts = cmd.split()
        if parts:
            formatted_cmd = f"[green]{parts[0]}[/green]"
            if len(parts) > 1:
                formatted_cmd += f" [yellow]{parts[1]}[/yellow]"
            if len(parts) > 2:
                formatted_cmd += " " + " ".join([f"[cyan]{p}[/cyan]" for p in parts[2:]])
            console.print(f"  [dim]$[/dim] {formatted_cmd}")
        console.print()


def create_examples_panel(title: str, examples: list[tuple[str, str]]) -> Panel:
    """Create a rich panel with examples."""
    content = []
    for desc, cmd in examples:
        content.append(f"[dim]# {desc}[/dim]")
        content.append(f"[dim]$[/dim] [green]{cmd}[/green]")
        content.append("")
    
    return Panel(
        "\n".join(content),
        title=f"[bold yellow]{title}[/bold yellow]",
        border_style="yellow",
        padding=(1, 2)
    )

