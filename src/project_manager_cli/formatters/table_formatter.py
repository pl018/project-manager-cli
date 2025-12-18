"""Terminal table formatter using rich library for project list display."""

from typing import Any, Dict, List
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.style import Style


class ProjectTableFormatter:
    """Formats project data as a terminal table using rich library."""

    # Tag colors mapping
    TAG_COLORS = {
        "frontend": "#3b82f6",  # blue
        "backend": "#22c55e",   # green
        "fullstack": "#8b5cf6", # purple
        "api": "#f59e0b",       # amber
        "cli": "#06b6d4",       # cyan
        "library": "#ec4899",   # pink
        "tool": "#64748b",      # slate
        "app": "#14b8a6",       # teal
        "mobile": "#f97316",    # orange
        "web": "#6366f1",       # indigo
    }

    def __init__(self):
        self.console = Console()

    def format_projects(self, projects: List[Dict[str, Any]]) -> None:
        """Print a formatted table of projects to the console."""
        if not projects:
            self.console.print("[yellow]No projects found.[/yellow]")
            return

        table = Table(
            title="[bold cyan]Project Manager - Projects[/bold cyan]",
            title_style="bold",
            header_style="bold magenta",
            border_style="bright_black",
            show_header=True,
            show_lines=True,
            expand=False,
        )

        # Add columns
        table.add_column("", style="dim", width=3, justify="center")  # Favorite
        table.add_column("Name", style="cyan", min_width=20, max_width=35)
        table.add_column("Path", style="dim", min_width=30, max_width=50)
        table.add_column("Tags", min_width=15, max_width=30)
        table.add_column("Last Opened", style="green", width=12, justify="center")
        table.add_column("Opens", style="yellow", width=6, justify="center")

        for project in projects:
            # Favorite indicator
            fav = "★" if project.get("favorite") else ""
            fav_style = Style(color="yellow") if project.get("favorite") else Style()

            # Project name with AI name if available
            name = project.get("ai_app_name") or project.get("name", "Unknown")
            
            # Truncate path for display
            path = project.get("root_path", "")
            if len(path) > 50:
                path = "..." + path[-47:]

            # Format tags with colors
            tags = project.get("tags", [])
            if isinstance(tags, str):
                import json
                try:
                    tags = json.loads(tags)
                except json.JSONDecodeError:
                    tags = []
            
            tags_text = self._format_tags(tags)

            # Format last opened date
            last_opened = project.get("last_opened")
            if last_opened:
                try:
                    if isinstance(last_opened, str):
                        dt = datetime.fromisoformat(last_opened)
                    else:
                        dt = last_opened
                    last_opened_str = dt.strftime("%Y-%m-%d")
                except (ValueError, AttributeError):
                    last_opened_str = "-"
            else:
                last_opened_str = "-"

            # Open count
            open_count = str(project.get("open_count", 0))

            table.add_row(
                Text(fav, style=fav_style),
                name,
                path,
                tags_text,
                last_opened_str,
                open_count,
            )

        self.console.print()
        self.console.print(table)
        self.console.print()
        self.console.print(f"[dim]Total: {len(projects)} project(s)[/dim]")
        self.console.print()

    def _format_tags(self, tags: List[str]) -> Text:
        """Format tags with colors."""
        if not tags:
            return Text("-", style="dim")

        text = Text()
        for i, tag in enumerate(tags):
            color = self.TAG_COLORS.get(tag.lower(), "#94a3b8")
            text.append(tag, style=f"bold {color}")
            if i < len(tags) - 1:
                text.append(" ", style="default")

        return text

    def print_project_count(self, count: int) -> None:
        """Print the project count summary."""
        self.console.print(f"[bold green]Found {count} project(s)[/bold green]")

