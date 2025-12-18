from __future__ import annotations

import sys


def main() -> None:
    """Entry point for the desktop GUI (pm-gui)."""
    try:
        from PySide6 import QtWidgets  # noqa: WPS433 (runtime import)
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            "PySide6 is not installed.\n\n"
            "Install the GUI extra:\n"
            "  pip install -e \".[gui]\"\n"
        ) from e

    from .window import MainWindow
    from .theme import apply_theme

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Project Manager")
    apply_theme(app)
    win = MainWindow()
    win.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    main()


