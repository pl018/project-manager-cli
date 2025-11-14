"""Search bar widget with live filtering."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Input, Label, Static
from textual.message import Message


class SearchBar(Static):
    """Search bar with filters and live search."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_input = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container(classes="search-container"):
            with Horizontal(classes="search-bar-horizontal"):
                yield Label("🔍", classes="search-icon")
                self.search_input = Input(
                    placeholder="Search projects... (press / to focus)",
                    classes="search-input"
                )
                yield self.search_input

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input == self.search_input:
            self.post_message(self.SearchChanged(event.value))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search submission."""
        if event.input == self.search_input:
            self.post_message(self.SearchSubmitted(event.value))

    def focus_search(self) -> None:
        """Focus the search input."""
        if self.search_input:
            self.search_input.focus()

    def clear(self) -> None:
        """Clear the search input."""
        if self.search_input:
            self.search_input.value = ""

    class SearchChanged(Message):
        """Message sent when search text changes."""
        def __init__(self, query: str):
            super().__init__()
            self.query = query

    class SearchSubmitted(Message):
        """Message sent when search is submitted."""
        def __init__(self, query: str):
            super().__init__()
            self.query = query
