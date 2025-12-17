"""Tag pill widget for displaying and filtering tags."""

from textual.app import ComposeResult
from textual.widgets import Button, Label, Static
from textual.containers import Horizontal, HorizontalScroll
from textual.message import Message
from textual.reactive import reactive


class TagPill(Static, can_focus=True):
    """A pill-shaped tag widget."""

    def __init__(self, tag: str, color: str = "#3b82f6", icon: str = "🏷️",
                 removable: bool = False, clickable: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.tag = tag
        self.color = color
        self.icon = icon
        self.removable = removable
        self.clickable = clickable
        self.selected = reactive(False)

    def watch_selected(self, selected: bool) -> None:
        self.set_class(selected, "selected")

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

    def set_selected(self, selected: bool) -> None:
        """Set selected state (visual only)."""
        self.selected = selected

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
        self._pills_by_tag: dict[str, TagPill] = {}

    def compose(self) -> ComposeResult:
        """Create tag filter content."""
        with HorizontalScroll(classes="tag-filter-container"):
            yield Label("Filter by tags:", classes="tag-filter-label")
            yield Button("Clear", id="clear-tags", variant="default", classes="tag-clear-btn")
            for tag_info in self.available_tags:
                tag_name = tag_info.get('name', '')
                tag_color = tag_info.get('color', '#3b82f6')
                tag_icon = tag_info.get('icon', '🏷️')
                pill = TagPill(
                    tag=tag_name,
                    color=tag_color,
                    icon=tag_icon,
                    clickable=True,
                    id=f"tag-{tag_name}",
                )
                self._pills_by_tag[tag_name] = pill
                yield pill

    def on_tag_pill_tag_clicked(self, message: TagPill.TagClicked) -> None:
        """Handle tag selection."""
        tag = message.tag
        if tag in self.selected_tags:
            self.selected_tags.remove(tag)
        else:
            self.selected_tags.append(tag)

        # Update pill visuals
        pill = self._pills_by_tag.get(tag)
        if pill:
            pill.set_selected(tag in self.selected_tags)

        self.post_message(self.FilterChanged(self.selected_tags))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "clear-tags":
            self.clear_selection()
            event.stop()

    def clear_selection(self) -> None:
        """Clear current selection and update pill UI."""
        self.selected_tags = []
        for pill in self._pills_by_tag.values():
            pill.set_selected(False)
        self.post_message(self.FilterChanged(self.selected_tags))

    class FilterChanged(Message):
        """Message sent when tag filter changes."""
        def __init__(self, tags: list):
            super().__init__()
            self.tags = tags
