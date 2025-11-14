"""Tag pill widget for displaying and filtering tags."""

from textual.app import ComposeResult
from textual.widgets import Button, Label, Static
from textual.containers import Horizontal
from textual.message import Message


class TagPill(Static):
    """A pill-shaped tag widget."""

    def __init__(self, tag: str, color: str = "#3b82f6", icon: str = "🏷️",
                 removable: bool = False, clickable: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.tag = tag
        self.color = color
        self.icon = icon
        self.removable = removable
        self.clickable = clickable

    def compose(self) -> ComposeResult:
        """Create tag pill content."""
        with Horizontal(classes="tag-pill"):
            yield Label(f"{self.icon} {self.tag}", classes="tag-label")
            if self.removable:
                yield Button("×", variant="error", classes="tag-remove-btn")

    def on_click(self) -> None:
        """Handle tag click."""
        if self.clickable and not self.removable:
            self.post_message(self.TagClicked(self.tag))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle remove button click."""
        if self.removable:
            self.post_message(self.TagRemoved(self.tag))
            event.stop()

    class TagClicked(Message):
        """Message sent when tag is clicked."""
        def __init__(self, tag: str):
            super().__init__()
            self.tag = tag

    class TagRemoved(Message):
        """Message sent when tag remove button is clicked."""
        def __init__(self, tag: str):
            super().__init__()
            self.tag = tag


class TagFilter(Static):
    """Widget for filtering by multiple tags."""

    def __init__(self, available_tags: list, **kwargs):
        super().__init__(**kwargs)
        self.available_tags = available_tags
        self.selected_tags = []

    def compose(self) -> ComposeResult:
        """Create tag filter content."""
        with Horizontal(classes="tag-filter-container"):
            yield Label("Filter by tags:", classes="tag-filter-label")
            for tag_info in self.available_tags:
                tag_name = tag_info.get('name', '')
                tag_color = tag_info.get('color', '#3b82f6')
                tag_icon = tag_info.get('icon', '🏷️')
                yield TagPill(
                    tag=tag_name,
                    color=tag_color,
                    icon=tag_icon,
                    clickable=True
                )

    def on_tag_pill_tag_clicked(self, message: TagPill.TagClicked) -> None:
        """Handle tag selection."""
        tag = message.tag
        if tag in self.selected_tags:
            self.selected_tags.remove(tag)
        else:
            self.selected_tags.append(tag)

        self.post_message(self.FilterChanged(self.selected_tags))

    class FilterChanged(Message):
        """Message sent when tag filter changes."""
        def __init__(self, tags: list):
            super().__init__()
            self.tags = tags
