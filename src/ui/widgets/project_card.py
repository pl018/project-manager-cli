"""Project card widget displaying project information."""

from datetime import datetime
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Label, Static
from textual.reactive import reactive
from textual.message import Message
from textual.binding import Binding


class ProjectCard(Static, can_focus=True):
    """A beautiful card displaying project information."""

    BORDER_TITLE = "Project"
    BINDINGS = [
        Binding("enter", "open", "Open", show=False),
        Binding("o", "open", "Open", show=False),
    ]

    def __init__(self, project: dict, **kwargs):
        super().__init__(**kwargs)
        self.project = project
        self.selected = reactive(False)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container(classes="project-card-container"):
            # Project name and favorite indicator
            name = self.project.get('ai_app_name') or self.project.get('name') or 'Unknown'
            favorite = self.project.get('favorite', 0)
            favorite_icon = "⭐ " if favorite else ""

            yield Label(f"{favorite_icon}{name}", classes="project-name")

            # Path
            path = self.project.get('root_path') or ''
            yield Label(f"📁 {path}", classes="project-path")

            # Tags
            tags = self.project.get('tags') or []
            if tags:
                tag_text = " ".join([f"[{tag}]" for tag in tags[:5]])
                yield Label(f"🏷️  {tag_text}", classes="project-tags")

            # Description (prefer explicit field; fall back to legacy AI description)
            description = (self.project.get('description') or self.project.get('ai_app_description') or '').strip()
            if description:
                # Truncate if too long
                desc_preview = description[:100] + "..." if len(description) > 100 else description
                yield Label(desc_preview, classes="project-description")

            # Notes preview (if available)
            notes = self.project.get('notes') or ''
            if notes:
                # Show first line or first 80 chars of notes
                first_line = notes.split('\n')[0]
                notes_preview = first_line[:80] + "..." if len(first_line) > 80 else first_line
                yield Label(f"📝 {notes_preview}", classes="project-notes-preview")

            # Stats footer
            open_count = self.project.get('open_count', 0)
            last_opened = self.project.get('last_opened')

            stats_parts = []
            if open_count:
                stats_parts.append(f"🔄 {open_count}")
            if last_opened:
                try:
                    dt = datetime.fromisoformat(last_opened)
                    time_ago = self._time_ago(dt)
                    stats_parts.append(f"🕒 {time_ago}")
                except:
                    pass

            if stats_parts:
                yield Label(" • ".join(stats_parts), classes="project-stats")

    def _time_ago(self, dt: datetime) -> str:
        """Get human-readable time ago string."""
        now = datetime.now()
        diff = now - dt

        if diff.days > 365:
            years = diff.days // 365
            return f"{years}y ago"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months}mo ago"
        elif diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "just now"

    def on_click(self) -> None:
        """Handle click events."""
        self.post_message(self.Selected(self.project))

    def action_open(self) -> None:
        """Open this project (keyboard)."""
        self.post_message(self.Selected(self.project))

    class Selected(Message):
        """Event raised when a project card is selected."""
        def __init__(self, project: dict):
            super().__init__()
            self.project = project
