from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from PySide6 import QtCore


def _fmt_dt(value: Any) -> str:
    if not value:
        return ""
    # DB stores ISO strings; tolerate datetime too.
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    try:
        dt = datetime.fromisoformat(str(value))
        return dt.isoformat(sep=" ", timespec="seconds")
    except Exception:
        return str(value)


class ProjectsTableModel(QtCore.QAbstractTableModel):
    COL_FAVORITE = 0
    COL_NAME = 1
    COL_PATH = 2
    COL_TAGS = 3
    COL_UPDATED = 4

    HEADERS = ["★", "Name", "Path", "Tags", "Updated"]

    def __init__(self, projects: Optional[List[Dict[str, Any]]] = None) -> None:
        super().__init__()
        self._projects: List[Dict[str, Any]] = projects or []

    def set_projects(self, projects: List[Dict[str, Any]]) -> None:
        self.beginResetModel()
        self._projects = projects
        self.endResetModel()

    def project_at(self, row: int) -> Optional[Dict[str, Any]]:
        if 0 <= row < len(self._projects):
            return self._projects[row]
        return None

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._projects)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: QtCore.Qt.Orientation,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == QtCore.Qt.Orientation.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        return super().headerData(section, orientation, role)

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> Any:  # noqa: N802
        if not index.isValid():
            return None
        project = self.project_at(index.row())
        if not project:
            return None

        col = index.column()

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if col == self.COL_FAVORITE:
                return "★" if project.get("favorite", 0) in (1, True) else "☆"
            if col == self.COL_NAME:
                return project.get("ai_app_name") or project.get("name") or ""
            if col == self.COL_PATH:
                return project.get("root_path") or ""
            if col == self.COL_TAGS:
                tags = project.get("tags") or []
                if isinstance(tags, str):
                    return tags
                return ", ".join([str(t) for t in tags if t])
            if col == self.COL_UPDATED:
                return _fmt_dt(project.get("last_updated"))

        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            name = project.get("ai_app_name") or project.get("name") or ""
            path = project.get("root_path") or ""
            tags = project.get("tags") or []
            if not isinstance(tags, str):
                tags = ", ".join([str(t) for t in tags if t])
            desc = project.get("description") or project.get("ai_app_description") or ""
            return "\n".join([line for line in [name, path, tags, desc] if line])

        if role == QtCore.Qt.ItemDataRole.TextAlignmentRole and col == self.COL_FAVORITE:
            return int(QtCore.Qt.AlignmentFlag.AlignCenter)

        return None

    def sort(self, column: int, order: QtCore.Qt.SortOrder = QtCore.Qt.SortOrder.AscendingOrder) -> None:  # noqa: N802
        reverse = order == QtCore.Qt.SortOrder.DescendingOrder

        def key_fn(p: Dict[str, Any]):
            if column == self.COL_FAVORITE:
                return 1 if p.get("favorite", 0) in (1, True) else 0
            if column == self.COL_NAME:
                return (p.get("name") or "").lower()
            if column == self.COL_PATH:
                return (p.get("root_path") or "").lower()
            if column == self.COL_TAGS:
                tags = p.get("tags") or []
                if isinstance(tags, str):
                    return tags.lower()
                return " ".join([str(t).lower() for t in tags if t])
            if column == self.COL_UPDATED:
                return str(p.get("last_updated") or "")
            return ""

        self.layoutAboutToBeChanged.emit()
        self._projects.sort(key=key_fn, reverse=reverse)
        self.layoutChanged.emit()


class ProjectsFilterProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self) -> None:
        super().__init__()
        self._query = ""
        self._favorites_only = False

        self.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.setSortCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)

    def set_query(self, query: str) -> None:
        self._query = (query or "").strip()
        self.invalidateFilter()

    def set_favorites_only(self, enabled: bool) -> None:
        self._favorites_only = bool(enabled)
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QtCore.QModelIndex) -> bool:  # noqa: N802
        model = self.sourceModel()
        if model is None:
            return True

        idx_name = model.index(source_row, ProjectsTableModel.COL_NAME, source_parent)
        idx_path = model.index(source_row, ProjectsTableModel.COL_PATH, source_parent)
        idx_tags = model.index(source_row, ProjectsTableModel.COL_TAGS, source_parent)
        idx_fav = model.index(source_row, ProjectsTableModel.COL_FAVORITE, source_parent)

        if self._favorites_only:
            fav_text = str(model.data(idx_fav, QtCore.Qt.ItemDataRole.DisplayRole) or "")
            if fav_text != "★":
                return False

        if not self._query:
            return True

        hay = " ".join(
            [
                str(model.data(idx_name, QtCore.Qt.ItemDataRole.DisplayRole) or ""),
                str(model.data(idx_path, QtCore.Qt.ItemDataRole.DisplayRole) or ""),
                str(model.data(idx_tags, QtCore.Qt.ItemDataRole.DisplayRole) or ""),
            ]
        )
        return self._query.lower() in hay.lower()


