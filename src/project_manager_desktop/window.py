from __future__ import annotations

from typing import Any, Dict, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from core.config_manager import config as dynamic_config
from core.database import DatabaseManager
from integrations.registry import ToolRegistry

from .models import ProjectsFilterProxyModel, ProjectsTableModel


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

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.open_default_btn = QtWidgets.QPushButton("Open")
        self.toggle_fav_btn = QtWidgets.QPushButton("Toggle Favorite")

        top_row.addWidget(self.search_input, 1)
        top_row.addWidget(self.fav_only)
        top_row.addWidget(self.refresh_btn)
        top_row.addWidget(self.open_default_btn)
        top_row.addWidget(self.toggle_fav_btn)
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
        title_font.setPointSize(title_font.pointSize() + 4)
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

        # Docs tab (placeholder for future)
        self.docs_tab = QtWidgets.QWidget()
        docs_layout = QtWidgets.QVBoxLayout(self.docs_tab)
        self.docs_label = QtWidgets.QLabel(
            "Docs/knowledge base view goes here.\n\n"
            "Planned: link to README, per-project docs, AI summaries, and quick actions."
        )
        self.docs_label.setWordWrap(True)
        docs_layout.addWidget(self.docs_label)
        docs_layout.addStretch(1)
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
        self.refresh_btn.clicked.connect(lambda: self.refresh_projects(select_first=False))
        self.open_default_btn.clicked.connect(self.open_in_default_tool)
        self.toggle_fav_btn.clicked.connect(self.toggle_favorite)

        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.table.doubleClicked.connect(lambda _idx: self.open_in_default_tool())

        self.notes_edit.textChanged.connect(self._on_notes_changed)
        self.save_notes_btn.clicked.connect(self.save_notes)
        self.revert_notes_btn.clicked.connect(self.revert_notes)

        self.open_tool_btn.clicked.connect(self.open_in_selected_tool)

    # ---------------- Data / actions ----------------
    def _ensure_db(self) -> None:
        # Safe to call multiple times: connect() is idempotent-ish (stores conn).
        self.db.connect()
        self.db.create_tables()

    def refresh_projects(self, select_first: bool) -> None:
        try:
            self._ensure_db()
            projects = self.db.get_all_projects(enabled_only=True)
            self._projects_model.set_projects(projects)
            self._proxy.sort(ProjectsTableModel.COL_NAME, QtCore.Qt.SortOrder.AscendingOrder)
            self.status.showMessage(f"Loaded {len(projects)} projects", 2500)

            if select_first and projects:
                self.table.selectRow(0)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load projects:\n{e}")

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

    def _maybe_confirm_discard_notes(self) -> bool:
        if not self._dirty_notes:
            return True
        resp = QtWidgets.QMessageBox.question(
            self,
            "Unsaved notes",
            "You have unsaved notes changes. Discard them?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        )
        return resp == QtWidgets.QMessageBox.StandardButton.Yes

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


