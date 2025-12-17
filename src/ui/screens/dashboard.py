"""Main dashboard screen displaying all projects."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll, Horizontal
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Label, Button
from textual.binding import Binding

from ..widgets.search_bar import SearchBar
from ..widgets.project_card import ProjectCard
from ..widgets.tag_pill import TagFilter


class Dashboard(Screen):
    """Main dashboard showing all projects."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("slash", "focus_search", "Search", key_display="/"),
        Binding("escape", "clear_filters", "Clear Filters", show=False),
        Binding("n", "new_project", "New Project"),
        Binding("r", "refresh", "Refresh"),
        Binding("f", "toggle_favorites", "Favorites"),
        Binding("question_mark", "help", "Help", key_display="?"),
    ]

    def __init__(self, db_manager, tool_registry, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        self.tool_registry = tool_registry
        self.projects = []
        self.filtered_projects = []
        self.search_query = ""
        self.selected_tags = []
        self.favorites_only = False

    def compose(self) -> ComposeResult:
        """Create dashboard layout."""
        yield Header(show_clock=True)

        with Container(id="main-container"):
            # Top bar with stats and actions
            with Horizontal(id="top-bar"):
                yield Label("📊 Project Manager", id="title")
                yield Label("", id="stats")
                yield Button("⭐ Favorites", id="favorites-btn", variant="primary")
                yield Button("➕ New", id="new-btn", variant="success")
                yield Button("🔄 Refresh", id="refresh-btn")

            # Search bar
            yield SearchBar(id="search-bar")

            # Tag filter (will be populated dynamically)
            with Container(id="tag-filter-container"):
                pass  # Tags loaded in on_mount

            # Project grid/list
            with VerticalScroll(id="projects-container"):
                yield Label("Loading projects...", id="loading-message")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize dashboard when mounted."""
        self.load_projects()
        self.load_tag_filter()

    def load_projects(self) -> None:
        """Load all projects from database."""
        try:
            self.projects = self.db_manager.get_all_projects(enabled_only=True)
            self.filtered_projects = self.projects.copy()
            self.update_stats()
            self.display_projects()
        except Exception as e:
            self.notify(f"Error loading projects: {e}", severity="error")

    def load_tag_filter(self) -> None:
        """Load available tags for filtering."""
        try:
            tags = self.db_manager.get_all_tags()
            container = self.query_one("#tag-filter-container")

            # Clear existing content
            container.remove_children()

            if tags:
                tag_filter = TagFilter(available_tags=tags, id="tag-filter")
                container.mount(tag_filter)
        except Exception as e:
            self.notify(f"Error loading tags: {e}", severity="error")

    def display_projects(self) -> None:
        """Display filtered projects as cards."""
        container = self.query_one("#projects-container")

        # Clear existing cards
        container.remove_children()

        if not self.filtered_projects:
            # Give a useful empty state, especially when filters are active.
            active_bits = []
            if self.search_query:
                active_bits.append(f"search='{self.search_query}'")
            if self.selected_tags:
                active_bits.append(f"tags={len(self.selected_tags)}")
            if self.favorites_only:
                active_bits.append("favorites")

            suffix = f"\n[dim]Active filters: {', '.join(active_bits)} • Press Esc to clear[/dim]" if active_bits else ""
            container.mount(
                Label(
                    f"No projects found. Press 'n' to add a new project.{suffix}",
                    id="empty-message"
                )
            )
            return

        # Display project cards
        for project in self.filtered_projects:
            card = ProjectCard(project=project, classes="project-card")
            container.mount(card)

    def apply_filters(self) -> None:
        """Apply search and tag filters to projects."""
        self.filtered_projects = []

        for project in self.projects:
            # Check favorites filter
            if self.favorites_only and not project.get('favorite', 0):
                continue

            # Check search query
            if self.search_query:
                query_lower = self.search_query.lower()
                # Many fields can be None depending on DB history/migrations; normalize to strings.
                name_text = project.get("name") or ""
                path_text = project.get("root_path") or ""
                notes_text = project.get("notes") or ""
                ai_name_text = project.get("ai_app_name") or ""
                ai_desc_text = project.get("description") or project.get("ai_app_description") or ""

                tags_value = project.get("tags") or []
                if isinstance(tags_value, str):
                    tags_text = tags_value
                else:
                    tags_text = " ".join([str(t) for t in tags_value if t])

                haystack = " ".join([name_text, path_text, tags_text, ai_name_text, ai_desc_text, notes_text]).lower()
                match = query_lower in haystack

                if not match:
                    continue

            # Check tag filter
            if self.selected_tags:
                project_tags = project.get('tags', [])
                if not any(tag in project_tags for tag in self.selected_tags):
                    continue

            self.filtered_projects.append(project)

        self.update_stats()
        self.display_projects()

    def update_stats(self) -> None:
        """Update top-bar stats label."""
        try:
            stats = self.query_one("#stats", Label)
        except Exception:
            return

        total = len(self.projects)
        shown = len(self.filtered_projects) if self.filtered_projects is not None else 0
        filters = []
        if self.favorites_only:
            filters.append("⭐")
        if self.selected_tags:
            filters.append(f"🏷️ {len(self.selected_tags)}")
        if self.search_query:
            filters.append("🔍")

        suffix = f"  [dim]{' '.join(filters)}[/dim]" if filters else ""
        stats.update(f"[dim]{shown}/{total} shown[/dim]{suffix}")

    # Event handlers
    def on_search_bar_search_changed(self, message: SearchBar.SearchChanged) -> None:
        """Handle search query changes."""
        self.search_query = message.query
        self.apply_filters()

    def on_tag_filter_filter_changed(self, message) -> None:
        """Handle tag filter changes."""
        self.selected_tags = message.tags
        self.apply_filters()

    def on_project_card_selected(self, message: ProjectCard.Selected) -> None:
        """Handle project card selection."""
        project = message.project
        self.open_project_detail(project)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "favorites-btn":
            self.action_toggle_favorites()
        elif event.button.id == "new-btn":
            self.action_new_project()
        elif event.button.id == "refresh-btn":
            self.action_refresh()

    # Actions
    def action_focus_search(self) -> None:
        """Focus the search bar."""
        search_bar = self.query_one("#search-bar", SearchBar)
        search_bar.focus_search()

    def action_toggle_favorites(self) -> None:
        """Toggle favorites-only filter."""
        self.favorites_only = not self.favorites_only
        btn = self.query_one("#favorites-btn", Button)
        btn.variant = "warning" if self.favorites_only else "primary"
        btn.label = "⭐ Favorites (On)" if self.favorites_only else "⭐ Favorites"
        self.apply_filters()

    def action_new_project(self) -> None:
        """Add a new project."""
        # This would typically open a new project dialog
        # For now, just notify
        self.notify("New project dialog not yet implemented", severity="information")

    def action_refresh(self) -> None:
        """Refresh the project list."""
        self.load_projects()
        self.notify("Projects refreshed", severity="information")

    def action_clear_filters(self) -> None:
        """Clear search + tag + favorites filters."""
        cleared_any = bool(self.search_query or self.selected_tags or self.favorites_only)
        self.search_query = ""
        self.selected_tags = []
        self.favorites_only = False

        # Update UI widgets if present.
        try:
            search_bar = self.query_one("#search-bar", SearchBar)
            search_bar.clear()
        except Exception:
            pass
        try:
            btn = self.query_one("#favorites-btn", Button)
            btn.variant = "primary"
            btn.label = "⭐ Favorites"
        except Exception:
            pass
        try:
            tag_filter = self.query_one("#tag-filter", TagFilter)
            tag_filter.clear_selection()
        except Exception:
            pass

        self.apply_filters()
        if cleared_any:
            self.notify("Cleared filters", severity="information", timeout=1.5)

    def action_help(self) -> None:
        """Show help dialog."""
        help_text = """
        Keyboard Shortcuts:

        /  - Focus search
        Esc - Clear filters
        n  - New project
        r  - Refresh
        f  - Toggle favorites
        q  - Quit
        ?  - Show this help

        Click on a project card to view details.
        """
        self.notify(help_text, title="Help", timeout=10)

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def open_project_detail(self, project: dict) -> None:
        """Open the project detail screen."""
        from .project_detail import ProjectDetailScreen

        detail_screen = ProjectDetailScreen(
            project=project,
            db_manager=self.db_manager,
            tool_registry=self.tool_registry
        )
        self.app.push_screen(detail_screen)
