"""Tag editor widget for managing project tags."""

import re
from typing import List

from PySide6 import QtCore, QtWidgets


class QFlowLayout(QtWidgets.QLayout):
    """Flow layout that wraps widgets to the next line when needed."""

    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self._item_list = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def __del__(self):
        while self.count():
            self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QtCore.QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QtCore.QSize(margins.left() + margins.right(),
                           margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            widget = item.widget()
            space_x = spacing
            space_y = spacing

            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()


class TagEditorWidget(QtWidgets.QWidget):
    """Widget for editing project tags with add/remove functionality."""

    # Signal emitted when tags are modified
    tags_changed = QtCore.Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_tags: List[str] = []
        self._available_tags: List[str] = []
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the tag editor UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Current tags section
        current_label = QtWidgets.QLabel("Current Tags:")
        current_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(current_label)

        # Scroll area for current tags
        current_scroll = QtWidgets.QScrollArea()
        current_scroll.setWidgetResizable(True)
        current_scroll.setMaximumHeight(120)
        current_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.current_tags_widget = QtWidgets.QWidget()
        self.current_tags_layout = QFlowLayout(self.current_tags_widget)
        self.current_tags_layout.setContentsMargins(4, 4, 4, 4)
        self.current_tags_layout.setSpacing(6)

        current_scroll.setWidget(self.current_tags_widget)
        layout.addWidget(current_scroll)

        # Available tags section
        available_label = QtWidgets.QLabel("Available Tags (click to add):")
        available_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(available_label)

        # Scroll area for available tags
        available_scroll = QtWidgets.QScrollArea()
        available_scroll.setWidgetResizable(True)
        available_scroll.setMaximumHeight(100)
        available_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.available_tags_widget = QtWidgets.QWidget()
        self.available_tags_layout = QFlowLayout(self.available_tags_widget)
        self.available_tags_layout.setContentsMargins(4, 4, 4, 4)
        self.available_tags_layout.setSpacing(6)

        available_scroll.setWidget(self.available_tags_widget)
        layout.addWidget(available_scroll)

        # Add custom tag section
        custom_layout = QtWidgets.QHBoxLayout()
        custom_label = QtWidgets.QLabel("Add Custom Tag:")
        self.custom_tag_input = QtWidgets.QLineEdit()
        self.custom_tag_input.setPlaceholderText("Enter tag name (lowercase alphanumeric)")
        self.add_custom_btn = QtWidgets.QPushButton("Add")

        custom_layout.addWidget(custom_label)
        custom_layout.addWidget(self.custom_tag_input, 1)
        custom_layout.addWidget(self.add_custom_btn)
        layout.addLayout(custom_layout)

        # Connect signals
        self.add_custom_btn.clicked.connect(self._on_add_custom_tag)
        self.custom_tag_input.returnPressed.connect(self._on_add_custom_tag)

    def set_tags(self, tags: List[str]) -> None:
        """Set the current tags."""
        self._current_tags = list(tags) if tags else []
        self._refresh_current_tags()

    def set_available_tags(self, tags: List[str]) -> None:
        """Set the available tags from database."""
        self._available_tags = list(tags) if tags else []
        self._refresh_available_tags()

    def get_tags(self) -> List[str]:
        """Get the current tags."""
        return list(self._current_tags)

    def _refresh_current_tags(self) -> None:
        """Refresh the current tags display."""
        # Clear existing widgets
        while self.current_tags_layout.count():
            item = self.current_tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add tag pills with remove buttons
        for tag in self._current_tags:
            pill = self._create_tag_pill(tag, removable=True)
            self.current_tags_layout.addWidget(pill)

        # Add placeholder if no tags
        if not self._current_tags:
            placeholder = QtWidgets.QLabel("No tags")
            placeholder.setStyleSheet("color: #888; font-style: italic;")
            self.current_tags_layout.addWidget(placeholder)

    def _refresh_available_tags(self) -> None:
        """Refresh the available tags display."""
        # Clear existing widgets
        while self.available_tags_layout.count():
            item = self.available_tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Filter out tags that are already in current tags
        available = [tag for tag in self._available_tags if tag not in self._current_tags]

        # Add clickable tag buttons
        for tag in available:
            btn = self._create_tag_button(tag)
            self.available_tags_layout.addWidget(btn)

        # Add placeholder if no available tags
        if not available:
            placeholder = QtWidgets.QLabel("No available tags")
            placeholder.setStyleSheet("color: #888; font-style: italic;")
            self.available_tags_layout.addWidget(placeholder)

    def _create_tag_pill(self, tag: str, removable: bool = False) -> QtWidgets.QWidget:
        """Create a tag pill widget."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        label = QtWidgets.QLabel(tag)
        layout.addWidget(label)

        if removable:
            remove_btn = QtWidgets.QToolButton()
            remove_btn.setText("×")
            remove_btn.setStyleSheet("font-size: 14px; font-weight: bold; border: none; padding: 0px;")
            remove_btn.setMaximumSize(16, 16)
            remove_btn.clicked.connect(lambda: self._remove_tag(tag))
            layout.addWidget(remove_btn)

        widget.setStyleSheet("""
            QWidget {
                background-color: #3b82f6;
                color: white;
                border-radius: 4px;
            }
        """)

        return widget

    def _create_tag_button(self, tag: str) -> QtWidgets.QPushButton:
        """Create a clickable tag button."""
        btn = QtWidgets.QPushButton(tag)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #e5e7eb;
                color: #1f2937;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #d1d5db;
            }
        """)
        btn.clicked.connect(lambda: self._add_tag(tag))
        return btn

    def _add_tag(self, tag: str) -> None:
        """Add a tag to current tags."""
        if tag and tag not in self._current_tags:
            self._current_tags.append(tag)
            self._refresh_current_tags()
            self._refresh_available_tags()
            self.tags_changed.emit(self._current_tags)

    def _remove_tag(self, tag: str) -> None:
        """Remove a tag from current tags."""
        if tag in self._current_tags:
            self._current_tags.remove(tag)
            self._refresh_current_tags()
            self._refresh_available_tags()
            self.tags_changed.emit(self._current_tags)

    def _on_add_custom_tag(self) -> None:
        """Handle adding a custom tag."""
        tag = self.custom_tag_input.text().strip().lower()

        if not tag:
            return

        # Validate tag (alphanumeric lowercase only)
        if not re.match(r'^[a-z0-9]+$', tag):
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Tag",
                "Tag must be lowercase alphanumeric characters only (a-z, 0-9)."
            )
            return

        # Check if tag already exists
        if tag in self._current_tags:
            QtWidgets.QMessageBox.information(
                self,
                "Tag Exists",
                f"Tag '{tag}' is already added."
            )
            self.custom_tag_input.clear()
            return

        # Add the tag
        self._add_tag(tag)
        self.custom_tag_input.clear()
