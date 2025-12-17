"""Project detail screen with notes, tags, and actions."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Label, Button, TextArea, Markdown
from textual.binding import Binding


class ProjectDetailScreen(Screen):
    """Detailed view of a single project."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("o", "open_project", "Open"),
        Binding("e", "edit_notes", "Edit Notes"),
        Binding("f", "toggle_favorite", "Favorite"),
        Binding("d", "delete_project", "Delete"),
    ]

    def __init__(self, project: dict, db_manager, tool_registry, **kwargs):
        super().__init__(**kwargs)
        self.project = project
        self.db_manager = db_manager
        self.tool_registry = tool_registry
        self.edit_mode = False

    def compose(self) -> ComposeResult:
        """Create project detail layout."""
        yield Header()

        with Container(id="detail-container"):
            # Project header
            with Horizontal(id="project-header"):
                favorite = self.project.get('favorite', 0)
                favorite_icon = "⭐" if favorite else "☆"
                name = self.project.get('ai_app_name') or self.project.get('name', 'Unknown')

                yield Label(f"{favorite_icon} {name}", id="project-title")

            # Project metadata
            with Container(id="metadata-container"):
                path = self.project.get('root_path', '')
                yield Label(f"📁 Path: {path}", classes="metadata-row")

                # Tags
                tags = self.project.get('tags', [])
                if tags:
                    tag_text = ", ".join(tags)
                    yield Label(f"🏷️  Tags: {tag_text}", classes="metadata-row")

                # Description (prefer explicit field; fall back to legacy AI description)
                desc = self.project.get('description') or self.project.get('ai_app_description')
                if desc:
                    yield Label(f"📝 Description: {desc}", classes="metadata-row")

                # Stats
                open_count = self.project.get('open_count', 0)
                yield Label(f"🔄 Opened {open_count} times", classes="metadata-row")

                last_opened = self.project.get('last_opened')
                if last_opened:
                    yield Label(f"🕒 Last opened: {last_opened}", classes="metadata-row")

            # Action buttons
            with Horizontal(id="action-buttons"):
                # Get available tools
                available_tools = self.tool_registry.get_available_tools()
                for tool in available_tools[:4]:  # Show first 4 tools
                    yield Button(
                        f"{tool.icon} {tool.display_name}",
                        id=f"open-{tool.name}",
                        variant="primary",
                        classes="tool-button"
                    )

                yield Button("⭐ Favorite", id="favorite-btn", variant="warning")
                yield Button("🗑️  Delete", id="delete-btn", variant="error")

            # Notes section
            with Container(id="notes-container"):
                yield Label("📝 Notes:", classes="section-header")

                notes = self.project.get('notes', '')
                if notes:
                    if self.edit_mode:
                        yield TextArea(notes, id="notes-editor")
                        with Horizontal(id="notes-actions"):
                            yield Button("💾 Save", id="save-notes-btn", variant="success")
                            yield Button("❌ Cancel", id="cancel-notes-btn")
                    else:
                        yield Markdown(notes, id="notes-display")
                        yield Button("✏️  Edit Notes", id="edit-notes-btn")
                else:
                    yield Label("No notes yet. Press 'e' to add notes.", classes="empty-notes")
                    yield Button("✏️  Add Notes", id="edit-notes-btn")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        # Tool launch buttons
        if button_id and button_id.startswith("open-"):
            tool_name = button_id.replace("open-", "")
            self.open_in_tool(tool_name)

        # Other actions
        elif button_id == "favorite-btn":
            self.action_toggle_favorite()
        elif button_id == "delete-btn":
            self.action_delete_project()
        elif button_id == "edit-notes-btn":
            self.action_edit_notes()
        elif button_id == "save-notes-btn":
            self.save_notes()
        elif button_id == "cancel-notes-btn":
            self.cancel_edit_notes()

    def open_in_tool(self, tool_name: str) -> None:
        """Open project in specified tool."""
        path = self.project.get('root_path', '')
        success = self.tool_registry.open_project(tool_name, path)

        if success:
            # Record the open event
            self.db_manager.record_project_open(self.project['uuid'])
            self.notify(f"Opened in {tool_name}", severity="information")
        else:
            self.notify(f"Failed to open in {tool_name}", severity="error")

    def action_open_project(self) -> None:
        """Open project in default tool."""
        default_tool = self.tool_registry.get_default_tool()
        if default_tool:
            self.open_in_tool(default_tool.name)
        else:
            self.notify("No available tools found", severity="error")

    def action_toggle_favorite(self) -> None:
        """Toggle favorite status."""
        try:
            is_favorite = self.db_manager.toggle_favorite(self.project['uuid'])
            self.project['favorite'] = 1 if is_favorite else 0

            # Update UI
            self.refresh(layout=True)
            status = "added to" if is_favorite else "removed from"
            self.notify(f"Project {status} favorites", severity="information")
        except Exception as e:
            self.notify(f"Error toggling favorite: {e}", severity="error")

    def action_edit_notes(self) -> None:
        """Enter notes edit mode."""
        self.edit_mode = True
        self.refresh(layout=True)

    def save_notes(self) -> None:
        """Save edited notes."""
        try:
            editor = self.query_one("#notes-editor", TextArea)
            new_notes = editor.text

            self.db_manager.update_notes(self.project['uuid'], new_notes)
            self.project['notes'] = new_notes

            self.edit_mode = False
            self.refresh(layout=True)
            self.notify("Notes saved successfully", severity="information")
        except Exception as e:
            self.notify(f"Error saving notes: {e}", severity="error")

    def cancel_edit_notes(self) -> None:
        """Cancel notes editing."""
        self.edit_mode = False
        self.refresh(layout=True)

    def action_delete_project(self) -> None:
        """Delete the project."""
        # In a real implementation, this should show a confirmation dialog
        try:
            self.db_manager.delete_project(self.project['uuid'])
            self.notify("Project deleted", severity="warning")
            self.action_back()
        except Exception as e:
            self.notify(f"Error deleting project: {e}", severity="error")

    def action_back(self) -> None:
        """Go back to dashboard."""
        self.app.pop_screen()
