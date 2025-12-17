"""Main Textual application for Project Manager TUI."""

from textual.app import App
from textual.binding import Binding

from core.config import Config
from core.database import DatabaseManager
from integrations.registry import ToolRegistry
from .screens.dashboard import Dashboard


class ProjectManagerApp(App):
    """A beautiful TUI for managing development projects."""

    CSS = """
    /* Global Styles */
    Screen {
        background: $surface;
    }

    /* Header and Footer */
    Header {
        background: $primary;
        color: $text;
    }

    Footer {
        background: $panel;
    }

    /* Main Container */
    #main-container {
        padding: 1;
        height: 100%;
    }

    /* Top Bar */
    #top-bar {
        height: 3;
        padding: 1;
        background: $panel;
        border: round $primary;
    }

    #title {
        width: 1fr;
        content-align: left middle;
        text-style: bold;
        color: $accent;
    }

    #stats {
        width: auto;
        content-align: right middle;
        color: $text-muted;
        margin-right: 1;
    }

    Button {
        margin-right: 1;
    }

    /* Search Bar */
    #search-bar {
        height: auto;
        margin: 1 0;
    }

    .search-container {
        height: 3;
        background: $panel;
        border: round $primary;
    }

    .search-bar-horizontal {
        width: 100%;
        height: 100%;
        padding: 0 1;
    }

    .search-icon {
        width: auto;
        content-align: center middle;
        padding-right: 1;
    }

    .search-input {
        width: 1fr;
    }

    /* Tag Filter */
    #tag-filter-container {
        height: auto;
        margin-bottom: 1;
    }

    .tag-filter-container {
        height: auto;
        padding: 1;
        background: $panel;
        border: round $primary;
    }

    .tag-pill {
        height: auto;
        width: auto;
        margin-right: 1;
        padding: 0 1;
        background: $surface;
        border: round $primary;
    }

    .tag-pill.selected {
        background: $accent;
        border: round $accent;
        color: $text;
        text-style: bold;
    }

    .tag-pill:focus {
        border: round $success;
    }

    .tag-label {
        padding: 0 1;
    }

    .tag-clear-btn {
        margin-right: 2;
    }

    /* Projects Container */
    #projects-container {
        height: 1fr;
        border: round $primary;
        padding: 1;
    }

    /* Project Cards */
    .project-card {
        height: auto;
        margin-bottom: 1;
        padding: 1 2;
        background: $panel;
        border: round $primary;
    }

    .project-card:hover {
        border: round $accent;
        background: $surface;
    }

    .project-card:focus {
        border: round $success;
    }

    .project-name {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .project-path {
        color: $text-muted;
        margin-bottom: 1;
    }

    .project-tags {
        color: $primary;
        margin-bottom: 1;
    }

    .project-description {
        color: $text;
        margin-bottom: 1;
        text-style: italic;
    }

    .project-notes-preview {
        color: $text-muted;
        margin-bottom: 1;
        background: $surface;
        padding: 0 1;
    }

    .project-stats {
        color: $text-muted;
    }

    #loading-message, #empty-message {
        width: 100%;
        height: 100%;
        content-align: center middle;
        color: $text-muted;
    }

    /* Project Detail Screen */
    #detail-container {
        padding: 2;
        height: 100%;
    }

    #project-header {
        height: 3;
        margin-bottom: 2;
    }

    #project-title {
        width: 100%;
        text-style: bold;
        color: $accent;
    }

    #metadata-container {
        padding: 1;
        margin-bottom: 2;
        background: $panel;
        border: solid $primary;
    }

    .metadata-row {
        margin-bottom: 1;
    }

    #action-buttons {
        height: auto;
        margin-bottom: 2;
    }

    .tool-button {
        margin-right: 1;
    }

    #notes-container {
        height: 1fr;
        padding: 1;
        background: $panel;
        border: solid $primary;
    }

    .section-header {
        text-style: bold;
        margin-bottom: 1;
        color: $accent;
    }

    #notes-display {
        height: 1fr;
        margin-bottom: 1;
    }

    #notes-editor {
        height: 20;
        margin-bottom: 1;
    }

    #notes-actions {
        height: auto;
    }

    .empty-notes {
        color: $text-muted;
        margin-bottom: 1;
    }
    """

    TITLE = Config.APP_NAME
    SUB_TITLE = f"v{Config.VERSION}"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.tool_registry = ToolRegistry()

    def on_mount(self) -> None:
        """Initialize the application."""
        try:
            # Connect to database and create tables
            self.db_manager.connect()
            self.db_manager.create_tables()

            # Load the dashboard
            dashboard = Dashboard(
                db_manager=self.db_manager,
                tool_registry=self.tool_registry
            )
            self.push_screen(dashboard)

        except Exception as e:
            self.exit(message=f"Failed to initialize: {e}")

    def on_unmount(self) -> None:
        """Cleanup when application closes."""
        if self.db_manager:
            self.db_manager.close()


def run_tui():
    """Run the TUI application."""
    app = ProjectManagerApp()
    app.run()


if __name__ == "__main__":
    run_tui()
