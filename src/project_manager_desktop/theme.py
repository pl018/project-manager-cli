from __future__ import annotations

from dataclasses import dataclass

from PySide6 import QtGui, QtWidgets


@dataclass(frozen=True)
class ThemeTokens:
    # Surfaces
    bg_base: str = "#0f1115"
    bg_panel: str = "#151a22"
    bg_panel_2: str = "#111621"
    bg_table: str = "#0f141d"
    bg_hover: str = "#1a2230"
    bg_pressed: str = "#202a3a"

    # Text
    fg: str = "#e6e8ee"
    fg_muted: str = "#9aa4b2"
    fg_disabled: str = "#6d7787"

    # Lines / borders
    border: str = "#252e3d"
    border_subtle: str = "#1d2532"

    # Brand / states
    accent: str = "#5b8cff"
    accent_2: str = "#4a79f0"
    focus_ring: str = "#7aa2ff"
    danger: str = "#e05252"
    warning: str = "#f0b35b"
    success: str = "#4ac28e"

    # Radius
    radius_sm: int = 6
    radius_md: int = 8


TOKENS = ThemeTokens()


def build_qss(t: ThemeTokens = TOKENS) -> str:
    r_sm = f"{t.radius_sm}px"
    r_md = f"{t.radius_md}px"

    # Note: keep QSS conservative to avoid fighting native platform metrics.
    return f"""
/* ---- Base ---- */
QWidget {{
  background-color: {t.bg_base};
  color: {t.fg};
  selection-background-color: rgba(91, 140, 255, 0.22);
  selection-color: {t.fg};
}}

QMainWindow {{
  background-color: {t.bg_base};
}}

QLabel[role="muted"] {{
  color: {t.fg_muted};
}}

QFrame[role="panel"] {{
  background-color: {t.bg_panel};
  border: 1px solid {t.border};
  border-radius: {r_md};
}}

QFrame[role="panel2"] {{
  background-color: {t.bg_panel_2};
  border: 1px solid {t.border};
  border-radius: {r_md};
}}

QFrame[role="toolbar"] {{
  background-color: {t.bg_panel};
  border: 1px solid {t.border};
  border-radius: {r_md};
}}

QSplitter::handle {{
  background: {t.border_subtle};
}}

/* ---- Inputs ---- */
QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser {{
  background-color: {t.bg_panel_2};
  border: 1px solid {t.border};
  border-radius: {r_sm};
}}

QLineEdit {{
  padding: 7px 10px;
}}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QTextBrowser:focus {{
  border: 1px solid rgba(122, 162, 255, 0.75);
}}

QLineEdit:disabled, QPlainTextEdit:disabled, QTextEdit:disabled {{
  color: {t.fg_disabled};
}}

/* ---- Buttons ---- */
QPushButton {{
  background-color: {t.bg_panel};
  border: 1px solid {t.border};
  border-radius: {r_sm};
  padding: 7px 12px;
}}

QPushButton:hover {{
  background-color: {t.bg_hover};
}}

QPushButton:pressed {{
  background-color: {t.bg_pressed};
}}

QPushButton:disabled {{
  color: {t.fg_disabled};
  background-color: {t.bg_panel_2};
}}

QPushButton[variant="primary"] {{
  background-color: {t.accent};
  border: 1px solid {t.accent_2};
  color: #ffffff;
}}
QPushButton[variant="primary"]:hover {{
  background-color: {t.accent_2};
}}

QPushButton[variant="secondary"] {{
  background-color: transparent;
  border: 1px solid {t.border};
  color: {t.fg};
}}
QPushButton[variant="secondary"]:hover {{
  background-color: {t.bg_hover};
}}

QPushButton[variant="danger"] {{
  background-color: rgba(224, 82, 82, 0.12);
  border: 1px solid rgba(224, 82, 82, 0.45);
  color: {t.danger};
}}
QPushButton[variant="danger"]:hover {{
  background-color: rgba(224, 82, 82, 0.18);
}}

QPushButton[variant="warning"] {{
  background-color: rgba(240, 179, 91, 0.10);
  border: 1px solid rgba(240, 179, 91, 0.45);
  color: {t.warning};
}}
QPushButton[variant="warning"]:hover {{
  background-color: rgba(240, 179, 91, 0.16);
}}

QToolButton {{
  background-color: transparent;
  border: 1px solid {t.border};
  border-radius: {r_sm};
  padding: 6px 10px;
}}
QToolButton:hover {{
  background-color: {t.bg_hover};
}}
QToolButton:checked {{
  background-color: rgba(91, 140, 255, 0.16);
  border: 1px solid rgba(91, 140, 255, 0.55);
}}

/* ---- Tabs (underline style) ---- */
QTabWidget::pane {{
  border: 1px solid {t.border};
  border-radius: {r_md};
  top: -1px;
  background-color: {t.bg_panel};
}}

QTabBar::tab {{
  background: transparent;
  color: {t.fg_muted};
  padding: 10px 12px;
  margin: 0px 6px 0px 0px;
  border: none;
}}

QTabBar::tab:selected {{
  color: {t.fg};
  border-bottom: 2px solid {t.accent};
}}

QTabBar::tab:hover {{
  color: {t.fg};
}}

/* ---- Tables ---- */
QTableView, QTableWidget {{
  background-color: {t.bg_table};
  alternate-background-color: rgba(255, 255, 255, 0.02);
  border: 1px solid {t.border};
  border-radius: {r_md};
  gridline-color: {t.border_subtle};
  selection-background-color: rgba(91, 140, 255, 0.22);
  selection-color: {t.fg};
}}

QHeaderView::section {{
  background-color: {t.bg_panel};
  color: {t.fg_muted};
  padding: 8px 10px;
  border: none;
  border-bottom: 1px solid {t.border};
}}

QTableView::item, QTableWidget::item {{
  padding: 6px 8px;
  border: none;
}}

QTableView::item:hover, QTableWidget::item:hover {{
  background-color: rgba(255, 255, 255, 0.03);
}}

/* ---- Scrollbars ---- */
QScrollBar:vertical {{
  background: transparent;
  width: 12px;
  margin: 0px;
}}
QScrollBar::handle:vertical {{
  background: rgba(154, 164, 178, 0.35);
  border-radius: 6px;
  min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
  background: rgba(154, 164, 178, 0.5);
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
  height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
  background: transparent;
}}
"""


def apply_theme(app: QtWidgets.QApplication, tokens: ThemeTokens = TOKENS) -> None:
    """Apply the Project Manager dark theme to the QApplication."""
    # Typography: prefer modern system sans.
    font = QtGui.QFont("Segoe UI")
    font.setPointSize(10)  # ~13-14px on Windows; stays readable cross-platform
    app.setFont(font)

    # Palette: keep consistent selection + disabled foreground.
    pal = app.palette()
    pal.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(tokens.bg_base))
    pal.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(tokens.bg_panel_2))
    pal.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(tokens.bg_table))
    pal.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(tokens.fg))
    pal.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(tokens.fg))
    pal.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(tokens.bg_panel))
    pal.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(tokens.fg))
    pal.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(tokens.accent))
    pal.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor("#ffffff"))
    app.setPalette(pal)

    app.setStyleSheet(build_qss(tokens))


