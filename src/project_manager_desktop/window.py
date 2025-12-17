from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from core.config_manager import config as dynamic_config
from core.database import DatabaseManager
from core.models import DocFile
from integrations.registry import ToolRegistry
from project_manager_cli.services.docs_discovery_service import DocsDiscoveryService

from .dialogs import ArchiveProjectDialog
from .models import ProjectsFilterProxyModel, ProjectsTableModel
from .widgets import TagEditorWidget


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Project Manager")
        self.resize(1200, 720)

        self.db = DatabaseManager(dynamic_config.SQLITE_DB_PATH)
        self.tools = ToolRegistry()

        self._projects_model = ProjectsTableModel([])
        self._proxy = ProjectsFilterProxyModel()
        self._proxy.setSourceModel(self._projects_model)
        self._proxy.setDynamicSortFilter(True)

        self._current_project_uuid: Optional[str] = None
        self._dirty_notes = False
        self._dirty_edit = False
        self._current_docs: List[DocFile] = []

        self._build_ui()
        self._connect_signals()
        self.refresh_projects(select_first=True)

    # ---------------- UI ----------------
    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        root_layout = QtWidgets.QVBoxLayout(central)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        # Top toolbar row
        top_row = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search name / path / tags…")

        self.fav_only = QtWidgets.QToolButton()
        self.fav_only.setCheckable(True)
        self.fav_only.setText("★ Favorites")

        self.show_archived = QtWidgets.QToolButton()
        self.show_archived.setCheckable(True)
        self.show_archived.setText("📦 Show Archived")

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.open_default_btn = QtWidgets.QPushButton("Open")
        self.toggle_fav_btn = QtWidgets.QPushButton("Toggle Favorite")
        self.archive_btn = QtWidgets.QPushButton("Archive Project")
        self.archive_btn.setStyleSheet("QPushButton { color: #f59e0b; }")
        self.delete_btn = QtWidgets.QPushButton("Delete Project")
        self.delete_btn.setStyleSheet("QPushButton { color: #dc2626; }")

        top_row.addWidget(self.search_input, 1)
        top_row.addWidget(self.fav_only)
        top_row.addWidget(self.show_archived)
        top_row.addWidget(self.refresh_btn)
        top_row.addWidget(self.open_default_btn)
        top_row.addWidget(self.toggle_fav_btn)
        top_row.addWidget(self.archive_btn)
        top_row.addWidget(self.delete_btn)
        root_layout.addLayout(top_row)

        # Splitter: list | detail
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # Left: table
        left = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.table = QtWidgets.QTableView()
        self.table.setModel(self._proxy)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(ProjectsTableModel.COL_NAME, QtCore.Qt.SortOrder.AscendingOrder)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(ProjectsTableModel.COL_FAVORITE, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(ProjectsTableModel.COL_NAME, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(ProjectsTableModel.COL_PATH, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(ProjectsTableModel.COL_TAGS, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(ProjectsTableModel.COL_UPDATED, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        left_layout.addWidget(self.table, 1)
        splitter.addWidget(left)

        # Right: detail tabs
        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self.detail_title = QtWidgets.QLabel("Select a project")
        title_font = self.detail_title.font()
        # Handle font size safely (pointSize can be -1 if font uses pixel size)
        current_size = title_font.pointSize()
        if current_size > 0:
            title_font.setPointSize(current_size + 4)
        else:
            title_font.setPointSize(14)  # Default larger size
        title_font.setBold(True)
        self.detail_title.setFont(title_font)
        right_layout.addWidget(self.detail_title)

        self.tabs = QtWidgets.QTabWidget()
        right_layout.addWidget(self.tabs, 1)

        # Overview tab
        self.overview = QtWidgets.QWidget()
        ov = QtWidgets.QFormLayout(self.overview)
        ov.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.ov_uuid = QtWidgets.QLineEdit(); self.ov_uuid.setReadOnly(True)
        self.ov_path = QtWidgets.QLineEdit(); self.ov_path.setReadOnly(True)
        self.ov_tags = QtWidgets.QLineEdit(); self.ov_tags.setReadOnly(True)
        self.ov_updated = QtWidgets.QLineEdit(); self.ov_updated.setReadOnly(True)
        self.ov_open_count = QtWidgets.QLineEdit(); self.ov_open_count.setReadOnly(True)
        self.ov_last_opened = QtWidgets.QLineEdit(); self.ov_last_opened.setReadOnly(True)
        self.ov_desc = QtWidgets.QPlainTextEdit(); self.ov_desc.setReadOnly(True); self.ov_desc.setMaximumHeight(120)
        ov.addRow("UUID:", self.ov_uuid)
        ov.addRow("Path:", self.ov_path)
        ov.addRow("Tags:", self.ov_tags)
        ov.addRow("Updated:", self.ov_updated)
        ov.addRow("Open count:", self.ov_open_count)
        ov.addRow("Last opened:", self.ov_last_opened)
        ov.addRow("Description:", self.ov_desc)
        self.tabs.addTab(self.overview, "Overview")

        # Edit tab
        self.edit = QtWidgets.QWidget()
        edit_layout = QtWidgets.QVBoxLayout(self.edit)
        edit_layout.setSpacing(12)

        # Scroll area for edit form
        edit_scroll = QtWidgets.QScrollArea()
        edit_scroll.setWidgetResizable(True)
        edit_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        edit_form_widget = QtWidgets.QWidget()
        edit_form = QtWidgets.QFormLayout(edit_form_widget)
        edit_form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        edit_form.setSpacing(12)

        # Project name field
        self.edit_name = QtWidgets.QLineEdit()
        self.edit_name.setPlaceholderText("Enter project name")
        edit_form.addRow("Name:", self.edit_name)

        # Description field
        self.edit_desc = QtWidgets.QPlainTextEdit()
        self.edit_desc.setPlaceholderText("Enter project description")
        self.edit_desc.setMaximumHeight(150)
        edit_form.addRow("Description:", self.edit_desc)

        # Tags editor
        self.edit_tags = TagEditorWidget()
        edit_form.addRow("Tags:", self.edit_tags)

        edit_scroll.setWidget(edit_form_widget)
        edit_layout.addWidget(edit_scroll, 1)

        # Buttons
        edit_buttons = QtWidgets.QHBoxLayout()
        self.save_edit_btn = QtWidgets.QPushButton("Save Changes")
        self.save_edit_btn.setEnabled(False)
        self.cancel_edit_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_edit_btn.setEnabled(False)
        edit_buttons.addWidget(self.save_edit_btn)
        edit_buttons.addWidget(self.cancel_edit_btn)
        edit_buttons.addStretch(1)
        edit_layout.addLayout(edit_buttons)

        self.tabs.addTab(self.edit, "Edit")

        # Notes tab
        self.notes = QtWidgets.QWidget()
        notes_layout = QtWidgets.QVBoxLayout(self.notes)
        self.notes_edit = QtWidgets.QPlainTextEdit()
        self.notes_edit.setPlaceholderText("Write notes (Markdown supported)…")
        notes_layout.addWidget(self.notes_edit, 1)

        notes_actions = QtWidgets.QHBoxLayout()
        self.save_notes_btn = QtWidgets.QPushButton("Save Notes")
        self.revert_notes_btn = QtWidgets.QPushButton("Revert")
        notes_actions.addWidget(self.save_notes_btn)
        notes_actions.addWidget(self.revert_notes_btn)
        notes_actions.addStretch(1)
        notes_layout.addLayout(notes_actions)
        self.tabs.addTab(self.notes, "Notes")

        # Tools tab
        self.tools_tab = QtWidgets.QWidget()
        tools_layout = QtWidgets.QVBoxLayout(self.tools_tab)
        self.tools_list = QtWidgets.QListWidget()
        self.tools_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        tools_layout.addWidget(QtWidgets.QLabel("Open current project in:"))
        tools_layout.addWidget(self.tools_list, 1)
        self.open_tool_btn = QtWidgets.QPushButton("Open Selected Tool")
        tools_layout.addWidget(self.open_tool_btn)
        self.tabs.addTab(self.tools_tab, "Tools")

        # Docs tab
        self.docs_tab = QtWidgets.QWidget()
        docs_layout = QtWidgets.QVBoxLayout(self.docs_tab)
        docs_layout.setSpacing(8)

        # Top toolbar for Docs tab
        docs_toolbar = QtWidgets.QHBoxLayout()
        self.docs_search = QtWidgets.QLineEdit()
        self.docs_search.setPlaceholderText("Search documentation files...")
        self.docs_refresh_btn = QtWidgets.QPushButton("Refresh")
        docs_toolbar.addWidget(QtWidgets.QLabel("Search:"))
        docs_toolbar.addWidget(self.docs_search, 1)
        docs_toolbar.addWidget(self.docs_refresh_btn)
        docs_layout.addLayout(docs_toolbar)

        # Splitter: file list | preview
        docs_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)

        # File table
        self.docs_table = QtWidgets.QTableWidget()
        self.docs_table.setColumnCount(3)
        self.docs_table.setHorizontalHeaderLabels(["Filename", "Path", "Modified"])
        self.docs_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.docs_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.docs_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.docs_table.setAlternatingRowColors(True)
        self.docs_table.verticalHeader().setVisible(False)
        self.docs_table.horizontalHeader().setStretchLastSection(True)
        self.docs_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.docs_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.docs_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        docs_splitter.addWidget(self.docs_table)

        # Preview area
        preview_widget = QtWidgets.QWidget()
        preview_layout = QtWidgets.QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(6)

        preview_header = QtWidgets.QHBoxLayout()
        self.docs_preview_label = QtWidgets.QLabel("Preview:")
        self.docs_preview_label.setStyleSheet("font-weight: bold;")
        preview_header.addWidget(self.docs_preview_label)
        preview_header.addStretch(1)
        preview_layout.addLayout(preview_header)

        self.docs_preview = QtWidgets.QTextBrowser()
        self.docs_preview.setOpenExternalLinks(False)
        preview_layout.addWidget(self.docs_preview, 1)

        # Preview buttons
        preview_buttons = QtWidgets.QHBoxLayout()
        self.docs_open_cursor_btn = QtWidgets.QPushButton("Open in Cursor")
        self.docs_open_default_btn = QtWidgets.QPushButton("Open in Default Editor")
        preview_buttons.addWidget(self.docs_open_cursor_btn)
        preview_buttons.addWidget(self.docs_open_default_btn)
        preview_buttons.addStretch(1)
        preview_layout.addLayout(preview_buttons)

        docs_splitter.addWidget(preview_widget)
        docs_splitter.setStretchFactor(0, 2)
        docs_splitter.setStretchFactor(1, 3)

        docs_layout.addWidget(docs_splitter, 1)
        self.tabs.addTab(self.docs_tab, "Docs")

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        root_layout.addWidget(splitter, 1)
        self.setCentralWidget(central)

        # Status bar
        self.status = self.statusBar()
        self.status.showMessage("Ready")

        # Populate tools list
        self._reload_tools()

    def _connect_signals(self) -> None:
        self.search_input.textChanged.connect(self._on_search_changed)
        self.fav_only.toggled.connect(self._on_fav_only_changed)
        self.show_archived.toggled.connect(self._on_show_archived_changed)
        self.refresh_btn.clicked.connect(self._on_toolbar_refresh)
        self.open_default_btn.clicked.connect(self.open_in_default_tool)
        self.toggle_fav_btn.clicked.connect(self.toggle_favorite)
        self.archive_btn.clicked.connect(self.archive_project)
        self.delete_btn.clicked.connect(self.delete_project)

        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.table.doubleClicked.connect(lambda _idx: self.open_in_default_tool())

        self.notes_edit.textChanged.connect(self._on_notes_changed)
        self.save_notes_btn.clicked.connect(self.save_notes)
        self.revert_notes_btn.clicked.connect(self.revert_notes)

        self.edit_name.textChanged.connect(self._on_edit_changed)
        self.edit_desc.textChanged.connect(self._on_edit_changed)
        self.edit_tags.tags_changed.connect(self._on_edit_changed)
        self.save_edit_btn.clicked.connect(self.save_edit)
        self.cancel_edit_btn.clicked.connect(self.cancel_edit)

        self.docs_search.textChanged.connect(self._on_docs_search_changed)
        self.docs_refresh_btn.clicked.connect(self._on_docs_refresh)
        self.docs_table.itemSelectionChanged.connect(self._on_docs_selection_changed)
        self.docs_open_cursor_btn.clicked.connect(self._on_docs_open_cursor)
        self.docs_open_default_btn.clicked.connect(self._on_docs_open_default)

        self.open_tool_btn.clicked.connect(self.open_in_selected_tool)

    # ---------------- Data / actions ----------------
    def _ensure_db(self) -> None:
        # Safe to call multiple times: connect() is idempotent-ish (stores conn).
        self.db.connect()
        self.db.create_tables()

    def refresh_projects(self, select_first: bool) -> None:
        try:
            self._ensure_db()

            # Check if showing archived projects
            if self.show_archived.isChecked():
                # Show all projects (enabled + archived)
                projects = self.db.get_all_projects(enabled_only=False)
                # Filter to only show archived
                projects = [p for p in projects if p.get('archived', 0) == 1]
            else:
                # Default: show only enabled, non-archived projects
                projects = self.db.get_all_projects(enabled_only=True)

            self._projects_model.set_projects(projects)
            self._proxy.sort(ProjectsTableModel.COL_NAME, QtCore.Qt.SortOrder.AscendingOrder)
            self.status.showMessage(f"Loaded {len(projects)} projects", 2500)

            if select_first and projects:
                self.table.selectRow(0)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load projects:\n{e}")

    def _on_toolbar_refresh(self) -> None:
        """Handle toolbar refresh button - refresh projects and current tab content."""
        # Always refresh the projects list
        self.refresh_projects(select_first=False)

        # Refresh the current tab's content if applicable
        current_tab_index = self.tabs.currentIndex()

        # Tab indices: 0=Overview, 1=Edit, 2=Notes, 3=Tools, 4=Docs
        if current_tab_index == 4:  # Docs tab
            self._on_docs_refresh()

    def _reload_tools(self) -> None:
        self.tools_list.clear()
        available = self.tools.get_available_tools()
        for tool in available:
            item = QtWidgets.QListWidgetItem(f"{tool.display_name}")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, tool.name)
            self.tools_list.addItem(item)

    def _current_project(self) -> Optional[Dict[str, Any]]:
        if not self._current_project_uuid:
            return None
        return self.db.get_project_by_uuid(self._current_project_uuid)

    def _set_current_project(self, project: Optional[Dict[str, Any]]) -> None:
        if not project:
            self._current_project_uuid = None
            self.detail_title.setText("Select a project")
            self.ov_uuid.setText("")
            self.ov_path.setText("")
            self.ov_tags.setText("")
            self.ov_updated.setText("")
            self.ov_open_count.setText("")
            self.ov_last_opened.setText("")
            self.ov_desc.setPlainText("")
            self.notes_edit.blockSignals(True)
            self.notes_edit.setPlainText("")
            self.notes_edit.blockSignals(False)
            self._dirty_notes = False
            self.save_notes_btn.setEnabled(False)
            self.revert_notes_btn.setEnabled(False)
            return

        self._current_project_uuid = project.get("uuid")
        self.detail_title.setText(project.get("ai_app_name") or project.get("name") or "Unnamed project")

        tags = project.get("tags") or []
        if not isinstance(tags, str):
            tags = ", ".join([str(t) for t in tags if t])

        self.ov_uuid.setText(str(project.get("uuid") or ""))
        self.ov_path.setText(str(project.get("root_path") or ""))
        self.ov_tags.setText(str(tags))
        self.ov_updated.setText(str(project.get("last_updated") or ""))
        self.ov_open_count.setText(str(project.get("open_count") or 0))
        self.ov_last_opened.setText(str(project.get("last_opened") or ""))
        self.ov_desc.setPlainText(str(project.get("description") or project.get("ai_app_description") or ""))

        self.notes_edit.blockSignals(True)
        self.notes_edit.setPlainText(str(project.get("notes") or ""))
        self.notes_edit.blockSignals(False)
        self._dirty_notes = False
        self.save_notes_btn.setEnabled(False)
        self.revert_notes_btn.setEnabled(False)

        # Load Edit tab data
        self.edit_name.blockSignals(True)
        self.edit_desc.blockSignals(True)
        self.edit_tags.blockSignals(True)

        self.edit_name.setText(str(project.get("ai_app_name") or ""))
        self.edit_desc.setPlainText(str(project.get("description") or project.get("ai_app_description") or ""))

        # Load tags and available tags
        try:
            self._ensure_db()
            all_tags = self.db.get_all_tags()
            available_tag_names = [tag['name'] for tag in all_tags]
            self.edit_tags.set_available_tags(available_tag_names)
        except Exception:
            self.edit_tags.set_available_tags([])

        current_tags = project.get("tags", [])
        if isinstance(current_tags, str):
            import json
            try:
                current_tags = json.loads(current_tags)
            except:
                current_tags = []
        self.edit_tags.set_tags(current_tags)

        self.edit_name.blockSignals(False)
        self.edit_desc.blockSignals(False)
        self.edit_tags.blockSignals(False)

        self._dirty_edit = False
        self.save_edit_btn.setEnabled(False)
        self.cancel_edit_btn.setEnabled(False)

        # Load Docs tab
        self._load_docs()

    def _maybe_confirm_discard_notes(self) -> bool:
        if self._dirty_notes:
            resp = QtWidgets.QMessageBox.question(
                self,
                "Unsaved notes",
                "You have unsaved notes changes. Discard them?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            )
            if resp != QtWidgets.QMessageBox.StandardButton.Yes:
                return False

        if self._dirty_edit:
            resp = QtWidgets.QMessageBox.question(
                self,
                "Unsaved changes",
                "You have unsaved changes in the Edit tab. Discard them?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            )
            if resp != QtWidgets.QMessageBox.StandardButton.Yes:
                return False

        return True

    # ---------------- slots ----------------
    def _on_search_changed(self, text: str) -> None:
        self._proxy.set_query(text)

    def _on_fav_only_changed(self, enabled: bool) -> None:
        self._proxy.set_favorites_only(enabled)

    def _on_selection_changed(self, _selected: QtCore.QItemSelection, _deselected: QtCore.QItemSelection) -> None:
        if not self._maybe_confirm_discard_notes():
            # Revert selection change: best-effort (keep current selection)
            if self._current_project_uuid:
                self._reselect_current_uuid()
            return

        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            self._set_current_project(None)
            return

        proxy_index = indexes[0]
        src_index = self._proxy.mapToSource(proxy_index)
        project = self._projects_model.project_at(src_index.row())
        if not project:
            self._set_current_project(None)
            return

        # Reload the full project record (ensures notes/fields are fresh)
        try:
            self._ensure_db()
            full = self.db.get_project_by_uuid(project["uuid"])
            self._set_current_project(full)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load project:\n{e}")

    def _reselect_current_uuid(self) -> None:
        # Find uuid in source model and select corresponding proxy row.
        uuid_ = self._current_project_uuid
        if not uuid_:
            return
        for row in range(self._projects_model.rowCount()):
            p = self._projects_model.project_at(row)
            if p and p.get("uuid") == uuid_:
                src = self._projects_model.index(row, 0)
                proxy = self._proxy.mapFromSource(src)
                if proxy.isValid():
                    self.table.selectRow(proxy.row())
                return

    def _on_notes_changed(self) -> None:
        if not self._current_project_uuid:
            return
        self._dirty_notes = True
        self.save_notes_btn.setEnabled(True)
        self.revert_notes_btn.setEnabled(True)

    def _on_edit_changed(self, *args) -> None:
        if not self._current_project_uuid:
            return
        self._dirty_edit = True
        self.save_edit_btn.setEnabled(True)
        self.cancel_edit_btn.setEnabled(True)

    # ---------------- public actions ----------------
    def save_notes(self) -> None:
        if not self._current_project_uuid:
            return
        try:
            self._ensure_db()
            text = self.notes_edit.toPlainText()
            self.db.update_notes(self._current_project_uuid, text)
            self._dirty_notes = False
            self.save_notes_btn.setEnabled(False)
            self.revert_notes_btn.setEnabled(False)
            self.status.showMessage("Notes saved", 2000)
            # Refresh the project record for updated timestamps
            self._set_current_project(self._current_project())
            self.refresh_projects(select_first=False)
            self._reselect_current_uuid()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save notes:\n{e}")

    def revert_notes(self) -> None:
        project = self._current_project()
        if not project:
            return
        self.notes_edit.blockSignals(True)
        self.notes_edit.setPlainText(str(project.get("notes") or ""))
        self.notes_edit.blockSignals(False)
        self._dirty_notes = False
        self.save_notes_btn.setEnabled(False)
        self.revert_notes_btn.setEnabled(False)
        self.status.showMessage("Reverted notes changes", 1500)

    def save_edit(self) -> None:
        """Save edited project fields with validation."""
        if not self._current_project_uuid:
            return

        # Validation
        name = self.edit_name.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(
                self,
                "Validation Error",
                "Project name cannot be empty."
            )
            return

        description = self.edit_desc.toPlainText().strip()
        tags = self.edit_tags.get_tags()

        try:
            self._ensure_db()
            # Update project fields
            self.db.update_project_fields(
                self._current_project_uuid,
                ai_app_name=name,
                description=description,
                tags=tags
            )

            self._dirty_edit = False
            self.save_edit_btn.setEnabled(False)
            self.cancel_edit_btn.setEnabled(False)
            self.status.showMessage("Project updated successfully", 2000)

            # Refresh the project record and UI
            self._set_current_project(self._current_project())
            self.refresh_projects(select_first=False)
            self._reselect_current_uuid()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Failed to save changes:\n{e}"
            )

    def cancel_edit(self) -> None:
        """Cancel edit changes and revert to original values."""
        project = self._current_project()
        if not project:
            return

        self.edit_name.blockSignals(True)
        self.edit_desc.blockSignals(True)
        self.edit_tags.blockSignals(True)

        self.edit_name.setText(str(project.get("ai_app_name") or ""))
        self.edit_desc.setPlainText(str(project.get("description") or project.get("ai_app_description") or ""))

        # Reload tags
        current_tags = project.get("tags", [])
        if isinstance(current_tags, str):
            import json
            try:
                current_tags = json.loads(current_tags)
            except:
                current_tags = []
        self.edit_tags.set_tags(current_tags)

        self.edit_name.blockSignals(False)
        self.edit_desc.blockSignals(False)
        self.edit_tags.blockSignals(False)

        self._dirty_edit = False
        self.save_edit_btn.setEnabled(False)
        self.cancel_edit_btn.setEnabled(False)
        self.status.showMessage("Reverted edit changes", 1500)

    # ---------------- Docs tab methods ----------------
    def _load_docs(self) -> None:
        """Load documentation files for the current project."""
        project = self._current_project()
        if not project:
            self._current_docs = []
            self._populate_docs_table([])
            self.docs_preview.clear()
            self.docs_preview_label.setText("Preview:")
            return

        try:
            root_path = project.get("root_path", "")
            self._current_docs = DocsDiscoveryService.discover_docs(root_path)
            self._populate_docs_table(self._current_docs)

            if self._current_docs:
                self.status.showMessage(f"Found {len(self._current_docs)} documentation files", 2000)
            else:
                self.docs_preview.setHtml("<p style='color: #888; font-style: italic;'>No documentation files found in this project.</p>")
                self.docs_preview_label.setText("Preview:")

        except Exception as e:
            self._current_docs = []
            self._populate_docs_table([])
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to discover docs:\n{e}")

    def _populate_docs_table(self, docs: List[DocFile]) -> None:
        """Populate the docs table with documentation files."""
        self.docs_table.setRowCount(0)
        self.docs_table.setRowCount(len(docs))

        for row, doc in enumerate(docs):
            # Filename
            filename_item = QtWidgets.QTableWidgetItem(doc.filename)
            filename_item.setData(QtCore.Qt.ItemDataRole.UserRole, row)  # Store index
            self.docs_table.setItem(row, 0, filename_item)

            # Relative path
            path_item = QtWidgets.QTableWidgetItem(doc.relative_path)
            self.docs_table.setItem(row, 1, path_item)

            # Modified date
            modified_str = doc.modified_date.strftime("%Y-%m-%d %H:%M")
            modified_item = QtWidgets.QTableWidgetItem(modified_str)
            self.docs_table.setItem(row, 2, modified_item)

    def _on_docs_refresh(self) -> None:
        """Refresh the docs list."""
        self._load_docs()
        self.docs_search.clear()

    def _on_docs_search_changed(self, query: str) -> None:
        """Filter docs table based on search query."""
        query_lower = query.lower()

        for row in range(self.docs_table.rowCount()):
            filename_item = self.docs_table.item(row, 0)
            path_item = self.docs_table.item(row, 1)

            if not query_lower:
                self.docs_table.setRowHidden(row, False)
            else:
                filename = filename_item.text().lower() if filename_item else ""
                path = path_item.text().lower() if path_item else ""
                match = query_lower in filename or query_lower in path
                self.docs_table.setRowHidden(row, not match)

    def _on_docs_selection_changed(self) -> None:
        """Handle docs table selection change."""
        doc = self._get_selected_doc()
        if not doc:
            self.docs_preview.clear()
            self.docs_preview_label.setText("Preview:")
            return

        self._render_markdown_preview(doc)

    def _render_markdown_preview(self, doc: DocFile) -> None:
        """Render markdown file preview."""
        try:
            self.docs_preview_label.setText(f"Preview: {doc.filename}")

            # Read file content (limit to 100KB)
            max_size = 100 * 1024  # 100KB
            if doc.size_bytes > max_size:
                with open(doc.full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(max_size)
                content += "\n\n... (file truncated)"
            else:
                with open(doc.full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

            # Try to render as markdown, fallback to plain text
            try:
                import markdown

                # Configure extensions
                extensions = ['fenced_code', 'tables', 'nl2br']
                extension_configs = {}

                # Try to use codehilite with pygments for syntax highlighting
                try:
                    import pygments
                    extensions.append('codehilite')
                    extension_configs['codehilite'] = {
                        'css_class': 'highlight',
                        'linenums': False
                    }
                except ImportError:
                    pass

                # Try to use pymdown extensions
                try:
                    import pymdownx
                    extensions.extend(['pymdownx.superfences', 'pymdownx.highlight'])
                except ImportError:
                    pass

                html = markdown.markdown(
                    content,
                    extensions=extensions,
                    extension_configs=extension_configs
                )

                # Generate pygments CSS if available
                pygments_css = ""
                try:
                    from pygments.formatters import HtmlFormatter
                    formatter = HtmlFormatter(style='monokai')
                    pygments_css = formatter.get_style_defs('.highlight')
                except ImportError:
                    pass

                # Wrap in dark-themed HTML with styling (lighter, more readable theme)
                styled_html = f"""
                <html>
                <head>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        padding: 16px;
                        color: #d4d4d8;
                        background-color: #2e3440;
                        line-height: 1.6;
                    }}
                    code {{
                        background-color: #3b4252;
                        color: #88c0d0;
                        padding: 3px 6px;
                        border-radius: 4px;
                        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                        font-size: 0.9em;
                    }}
                    pre {{
                        background-color: #3b4252;
                        color: #d8dee9;
                        padding: 16px;
                        border-radius: 6px;
                        overflow-x: auto;
                        border: 1px solid #4c566a;
                        line-height: 1.5;
                    }}
                    pre code {{
                        background-color: transparent;
                        color: inherit;
                        padding: 0;
                        font-size: 0.9em;
                    }}
                    table {{
                        border-collapse: collapse;
                        margin: 12px 0;
                        color: #d4d4d8;
                        width: 100%;
                    }}
                    th, td {{
                        border: 1px solid #4c566a;
                        padding: 10px 12px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #3b4252;
                        color: #eceff4;
                        font-weight: 600;
                    }}
                    tr:nth-child(even) {{
                        background-color: #343d4d;
                    }}
                    a {{
                        color: #88c0d0;
                        text-decoration: none;
                    }}
                    a:hover {{
                        color: #8fbcbb;
                        text-decoration: underline;
                    }}
                    h1, h2, h3, h4, h5, h6 {{
                        color: #eceff4;
                        margin-top: 24px;
                        margin-bottom: 12px;
                        font-weight: 600;
                    }}
                    h1 {{
                        font-size: 2em;
                        border-bottom: 2px solid #4c566a;
                        padding-bottom: 10px;
                    }}
                    h2 {{
                        font-size: 1.5em;
                        border-bottom: 1px solid #4c566a;
                        padding-bottom: 8px;
                    }}
                    h3 {{ font-size: 1.25em; }}
                    h4 {{ font-size: 1.1em; }}
                    blockquote {{
                        border-left: 4px solid #5e81ac;
                        padding-left: 16px;
                        margin: 16px 0;
                        color: #b8c5db;
                        font-style: italic;
                    }}
                    ul, ol {{
                        color: #d4d4d8;
                        padding-left: 28px;
                    }}
                    li {{
                        margin: 6px 0;
                    }}
                    hr {{
                        border: none;
                        border-top: 1px solid #4c566a;
                        margin: 24px 0;
                    }}
                    img {{
                        max-width: 100%;
                        height: auto;
                        border-radius: 4px;
                    }}
                    strong {{
                        color: #eceff4;
                        font-weight: 600;
                    }}
                    em {{
                        color: #b8c5db;
                    }}
                    {pygments_css}
                </style>
                </head>
                <body>
                {html}
                </body>
                </html>
                """
                self.docs_preview.setHtml(styled_html)
            except ImportError:
                # Fallback to plain text if markdown library not available
                self.docs_preview.setPlainText(content)

        except Exception as e:
            self.docs_preview.setHtml(f"<p style='color: red;'>Error reading file: {e}</p>")

    def _get_selected_doc(self) -> Optional[DocFile]:
        """Get the currently selected documentation file."""
        selected_rows = self.docs_table.selectionModel().selectedRows()
        if not selected_rows:
            return None

        row = selected_rows[0].row()
        if row < 0 or row >= len(self._current_docs):
            return None

        # Get the doc index from the first column's UserRole
        filename_item = self.docs_table.item(row, 0)
        if not filename_item:
            return None

        doc_index = filename_item.data(QtCore.Qt.ItemDataRole.UserRole)
        if doc_index is None or doc_index >= len(self._current_docs):
            return None

        return self._current_docs[doc_index]

    def _on_docs_open_cursor(self) -> None:
        """Open selected doc file in Cursor."""
        doc = self._get_selected_doc()
        if not doc:
            QtWidgets.QMessageBox.information(self, "No Selection", "Please select a file first.")
            return

        cursor_tool = self.tools.get_tool("cursor")
        if not cursor_tool or not cursor_tool.is_available():
            QtWidgets.QMessageBox.warning(
                self,
                "Cursor Not Available",
                "Cursor is not installed or not available on this system."
            )
            return

        try:
            success = cursor_tool.open_file(str(doc.full_path))
            if success:
                self.status.showMessage(f"Opened {doc.filename} in Cursor", 2000)
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Failed",
                    f"Failed to open {doc.filename} in Cursor."
                )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Error opening file in Cursor:\n{e}"
            )

    def _on_docs_open_default(self) -> None:
        """Open selected doc file in default editor."""
        doc = self._get_selected_doc()
        if not doc:
            QtWidgets.QMessageBox.information(self, "No Selection", "Please select a file first.")
            return

        try:
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl

            url = QUrl.fromLocalFile(str(doc.full_path))
            success = QDesktopServices.openUrl(url)

            if success:
                self.status.showMessage(f"Opened {doc.filename} in default editor", 2000)
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Failed",
                    f"Failed to open {doc.filename} with default application."
                )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Error opening file:\n{e}"
            )

    def toggle_favorite(self) -> None:
        if not self._current_project_uuid:
            return
        try:
            self._ensure_db()
            new_state = self.db.toggle_favorite(self._current_project_uuid)
            self.status.showMessage("Favorited" if new_state else "Unfavorited", 1500)
            self.refresh_projects(select_first=False)
            self._reselect_current_uuid()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to toggle favorite:\n{e}")

    def delete_project(self) -> None:
        """Delete the current project with confirmation dialog."""
        if not self._current_project_uuid:
            return

        project = self._current_project()
        if not project:
            return

        project_name = project.get("ai_app_name") or project.get("name") or "this project"
        project_path = str(project.get("root_path") or "")

        # Custom dialog with checkbox for hard delete
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Confirm Delete")
        dialog.resize(500, 320)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Message
        message = QtWidgets.QLabel(
            f"Are you sure you want to delete '{project_name}'?\n\n"
            f"This will remove it from the project manager (soft delete).\n"
            f"The actual project files will NOT be deleted."
        )
        message.setWordWrap(True)
        layout.addWidget(message)

        # Hard delete checkbox
        hard_delete_checkbox = QtWidgets.QCheckBox(
            "Permanently delete from database (cannot be undone)"
        )
        hard_delete_checkbox.setStyleSheet("color: #dc2626; font-weight: bold;")
        layout.addWidget(hard_delete_checkbox)

        # Delete files checkbox
        delete_files_checkbox = QtWidgets.QCheckBox(
            "Also delete project files from disk (DESTRUCTIVE!)"
        )
        delete_files_checkbox.setStyleSheet("color: #dc2626; font-weight: bold;")
        layout.addWidget(delete_files_checkbox)

        # Warning label for hard delete (hidden by default)
        warning_label = QtWidgets.QLabel(
            "⚠ WARNING: Hard delete permanently removes all database records.\n"
            "This action cannot be undone!"
        )
        warning_label.setStyleSheet(
            "color: #991b1b; background-color: #fef2f2; "
            "padding: 8px; border-radius: 4px; font-weight: bold;"
        )
        warning_label.setWordWrap(True)
        warning_label.setVisible(False)
        layout.addWidget(warning_label)

        # Warning label for file deletion (hidden by default)
        files_warning_label = QtWidgets.QLabel(
            "⚠⚠ CRITICAL: This will PERMANENTLY DELETE all project files and folders!\n"
            "Locked files will be force-closed. This CANNOT be undone!"
        )
        files_warning_label.setStyleSheet(
            "color: #7f1d1d; background-color: #fee2e2; "
            "padding: 8px; border-radius: 4px; font-weight: bold; border: 2px solid #dc2626;"
        )
        files_warning_label.setWordWrap(True)
        files_warning_label.setVisible(False)
        layout.addWidget(files_warning_label)

        # Show/hide warnings based on checkboxes
        def on_hard_delete_changed(checked):
            warning_label.setVisible(checked)
            update_message()

        def on_delete_files_changed(checked):
            files_warning_label.setVisible(checked)
            update_message()

        def update_message():
            hard_delete = hard_delete_checkbox.isChecked()
            delete_files = delete_files_checkbox.isChecked()

            if delete_files:
                message.setText(
                    f"Are you sure you want to DELETE ALL FILES for '{project_name}'?\n\n"
                    f"This will PERMANENTLY DELETE the entire project directory:\n"
                    f"{project_path}\n\n"
                    f"{'Database records will be permanently removed.' if hard_delete else 'Project will be removed from database (soft delete).'}"
                )
            elif hard_delete:
                message.setText(
                    f"Are you sure you want to PERMANENTLY DELETE '{project_name}'?\n\n"
                    f"This will completely remove all database records.\n"
                    f"The actual project files will NOT be deleted."
                )
            else:
                message.setText(
                    f"Are you sure you want to delete '{project_name}'?\n\n"
                    f"This will remove it from the project manager (soft delete).\n"
                    f"The actual project files will NOT be deleted."
                )

        hard_delete_checkbox.stateChanged.connect(on_hard_delete_changed)
        delete_files_checkbox.stateChanged.connect(on_delete_files_changed)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Yes |
            QtWidgets.QDialogButtonBox.StandardButton.No
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Show dialog
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        try:
            self._ensure_db()

            # Check if hard delete was requested
            if hard_delete_checkbox.isChecked():
                self.db.hard_delete_project(self._current_project_uuid)
                self.status.showMessage(f"Permanently deleted {project_name}", 2000)
            else:
                self.db.delete_project(self._current_project_uuid)
                self.status.showMessage(f"Deleted {project_name}", 2000)

            # Check if physical file deletion was requested
            if delete_files_checkbox.isChecked() and project_path:
                self.status.showMessage(f"Deleting project files from disk...", 1000)
                QtWidgets.QApplication.processEvents()  # Update UI

                if self._delete_project_directory(project_path):
                    self.status.showMessage(f"Deleted {project_name} and all files", 3000)
                else:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Partial Success",
                        f"Project removed from database but failed to delete some/all files.\n\n"
                        f"You may need to manually delete:\n{project_path}"
                    )

            # Clear current project
            self._current_project_uuid = None
            self._set_current_project(None)

            # Refresh the project list
            self.refresh_projects(select_first=True)

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Failed to delete project:\n{e}"
            )

    def archive_project(self) -> None:
        """Archive the current project with confirmation."""
        if not self._current_project_uuid:
            return

        project = self._current_project()
        if not project:
            return

        project_name = project.get("ai_app_name") or project.get("name") or "this project"
        project_path = str(project.get("root_path") or "")

        if not project_path:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Project",
                "Project path not found."
            )
            return

        # Show archive dialog
        dialog = ArchiveProjectDialog(
            self,
            self.db,
            self._current_project_uuid,
            project_name,
            project_path
        )

        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted and dialog.success:
            self.status.showMessage(f"Archived {project_name}", 3000)

            # Clear current project and refresh list
            self._current_project_uuid = None
            self._set_current_project(None)
            self.refresh_projects(select_first=True)

    def _on_show_archived_changed(self, checked: bool) -> None:
        """Handle show archived toggle."""
        self.refresh_projects(select_first=False)

    def _delete_project_directory(self, project_path: str) -> bool:
        """
        Delete project directory using PowerShell with handle cleanup.

        Args:
            project_path: Full path to project directory to delete

        Returns:
            True if successful, False otherwise
        """
        import subprocess

        # PowerShell command to kill processes holding handles and delete directory
        ps_command = f'''$path="{project_path}"; if(Test-Path -LiteralPath $path){{ $pids=(& handle.exe -accepteula -nobanner $path 2>$null | % {{ if($_ -match '\\spid:\\s+(\\d+)\\s'){{ [int]$matches[1] }} }} | sort -Unique); if($pids){{ Stop-Process -Id $pids -Force -ErrorAction SilentlyContinue }}; try{{ Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction Stop }} catch {{ takeown /F $path /R /D Y | Out-Null; icacls $path /grant "$env:USERNAME:(OI)(CI)F" /T /C | Out-Null; Remove-Item -LiteralPath $path -Recurse -Force }} }}'''

        try:
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout for large directories
            )
            return result.returncode == 0
        except Exception as e:
            self.status.showMessage(f"Error deleting directory: {e}", 3000)
            return False

    def open_in_default_tool(self) -> None:
        project = self._current_project()
        if not project:
            return
        path = str(project.get("root_path") or "")
        if not path:
            return
        default_tool = self.tools.get_default_tool()
        if not default_tool:
            QtWidgets.QMessageBox.information(self, "No tools", "No available tools detected on this system.")
            return
        ok = self.tools.open_project(default_tool.name, path)
        if ok:
            try:
                self._ensure_db()
                self.db.record_project_open(project["uuid"])
            except Exception:
                pass
            self.status.showMessage(f"Opened in {default_tool.display_name}", 2000)
        else:
            QtWidgets.QMessageBox.warning(self, "Failed", f"Could not open in {default_tool.display_name}.")

    def open_in_selected_tool(self) -> None:
        project = self._current_project()
        if not project:
            return
        item = self.tools_list.currentItem()
        if not item:
            QtWidgets.QMessageBox.information(self, "Select tool", "Select a tool first.")
            return
        tool_name = item.data(QtCore.Qt.ItemDataRole.UserRole)
        path = str(project.get("root_path") or "")
        ok = self.tools.open_project(str(tool_name), path)
        if ok:
            try:
                self._ensure_db()
                self.db.record_project_open(project["uuid"])
            except Exception:
                pass
            self.status.showMessage(f"Opened in {item.text()}", 2000)
        else:
            QtWidgets.QMessageBox.warning(self, "Failed", f"Could not open in {item.text()}.")

    # ---------------- close handling ----------------
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
        if not self._maybe_confirm_discard_notes():
            event.ignore()
            return
        try:
            self.db.close()
        except Exception:
            pass
        event.accept()


