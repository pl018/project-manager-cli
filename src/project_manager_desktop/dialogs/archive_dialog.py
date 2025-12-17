"""Archive project dialog with progress indicator."""

from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtWidgets

from core.database import DatabaseManager
from project_manager_cli.services.archive_service import ArchiveService
from project_manager_cli.services.git_service import GitService


class ArchiveProjectDialog(QtWidgets.QDialog):
    """Dialog for archiving a project with progress feedback."""

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        db: DatabaseManager,
        project_uuid: str,
        project_name: str,
        project_path: str
    ):
        super().__init__(parent)
        self.db = db
        self.project_uuid = project_uuid
        self.project_name = project_name
        self.project_path = project_path

        self.archive_path: Optional[str] = None
        self.archive_size_mb: float = 0.0
        self.success = False

        self.setWindowTitle("Archive Project")
        self.setModal(True)
        self.resize(600, 400)

        self._build_ui()
        self._check_git_status()

    def _build_ui(self):
        """Build dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QtWidgets.QLabel(f"<h2>Archive Project: {self.project_name}</h2>")
        layout.addWidget(header)

        # Warning message
        warning = QtWidgets.QLabel(
            "<b>Warning:</b> This is a destructive operation that will:\n"
            "1. Check for uncommitted git changes (if git repo)\n"
            "2. Delete library folders (node_modules, venv, dist, build, etc.)\n"
            "3. Create a ZIP archive in %APPDATA%\\project-manager-cli\\archives\n"
            "4. Mark project as archived in database\n\n"
            "The project files will remain on disk but library folders will be deleted."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #dc2626; padding: 10px; background-color: #fef2f2; border-radius: 4px;")
        layout.addWidget(warning)

        # Git status area
        self.git_status_label = QtWidgets.QLabel("Checking git status...")
        layout.addWidget(self.git_status_label)

        # Progress log (read-only text area)
        self.progress_log = QtWidgets.QPlainTextEdit()
        self.progress_log.setReadOnly(True)
        self.progress_log.setMaximumHeight(150)
        layout.addWidget(QtWidgets.QLabel("Progress Log:"))
        layout.addWidget(self.progress_log)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Delete original directory checkbox
        self.delete_original_checkbox = QtWidgets.QCheckBox(
            "Delete original project directory after archiving (DESTRUCTIVE!)"
        )
        self.delete_original_checkbox.setStyleSheet("color: #dc2626; font-weight: bold;")
        self.delete_original_checkbox.setToolTip(
            "After successful archive, the original project directory will be permanently deleted.\n"
            "This will kill locked processes and force-delete all files."
        )
        layout.addWidget(self.delete_original_checkbox)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox()
        self.archive_btn = button_box.addButton("Start Archive", QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.cancel_btn = button_box.addButton(QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.archive_btn.clicked.connect(self._start_archive)
        self.cancel_btn.clicked.connect(self.reject)

        layout.addWidget(button_box)

    def _check_git_status(self):
        """Check git status and display in UI."""
        git_service = GitService()

        if not git_service.is_git_repository(self.project_path):
            self.git_status_label.setText("✓ Not a git repository (no git check needed)")
            self.git_status_label.setStyleSheet("color: green;")
            return

        has_changes, status_output = git_service.has_uncommitted_changes(self.project_path)

        if has_changes:
            self.git_status_label.setText(
                "⚠ Warning: Uncommitted git changes detected!\n"
                "Please review before archiving."
            )
            self.git_status_label.setStyleSheet("color: #f59e0b; font-weight: bold;")

            # Show git status in progress log
            self.progress_log.appendPlainText("Uncommitted changes:")
            self.progress_log.appendPlainText(status_output or "")
        else:
            self.git_status_label.setText("✓ Git repository is clean (no uncommitted changes)")
            self.git_status_label.setStyleSheet("color: green;")

    def _log(self, message: str):
        """Add message to progress log."""
        self.progress_log.appendPlainText(message)
        QtWidgets.QApplication.processEvents()  # Update UI

    def _delete_original_directory(self) -> bool:
        """
        Delete the original project directory using PowerShell.

        Returns:
            True if successful, False otherwise
        """
        import subprocess

        # PowerShell command to kill processes holding handles and delete directory
        ps_command = f'''$path="{self.project_path}"; if(Test-Path -LiteralPath $path){{ $pids=(& handle.exe -accepteula -nobanner $path 2>$null | % {{ if($_ -match '\\spid:\\s+(\\d+)\\s'){{ [int]$matches[1] }} }} | sort -Unique); if($pids){{ Stop-Process -Id $pids -Force -ErrorAction SilentlyContinue }}; try{{ Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction Stop }} catch {{ takeown /F $path /R /D Y | Out-Null; icacls $path /grant "$env:USERNAME:(OI)(CI)F" /T /C | Out-Null; Remove-Item -LiteralPath $path -Recurse -Force }} }}'''

        try:
            self._log("Killing processes with handles to directory...")
            QtWidgets.QApplication.processEvents()

            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )

            return result.returncode == 0
        except Exception as e:
            self._log(f"Error deleting directory: {str(e)}")
            return False

    def _start_archive(self):
        """Start the archive process."""
        self.archive_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

        try:
            # Step 1: Delete library folders (25%)
            self.progress_bar.setValue(5)
            self._log("\n=== Step 1: Deleting library folders ===")

            deleted = ArchiveService.delete_library_folders(
                self.project_path,
                progress_callback=self._log
            )

            if deleted:
                self._log(f"Deleted {len(deleted)} library folders")
            else:
                self._log("No library folders found to delete")

            self.progress_bar.setValue(25)

            # Step 2: Create archive (50%)
            self._log("\n=== Step 2: Creating ZIP archive ===")
            archive_dir = ArchiveService.get_archive_directory()
            project_dir_name = Path(self.project_path).name
            archive_filename = ArchiveService.generate_archive_filename(
                self.project_uuid,
                project_dir_name
            )
            archive_path = archive_dir / archive_filename

            self.progress_bar.setValue(30)

            success = ArchiveService.create_zip_archive(
                self.project_path,
                archive_path,
                progress_callback=self._log
            )

            if not success:
                raise Exception("Failed to create archive")

            self.progress_bar.setValue(75)
            self.archive_path = str(archive_path)
            self.archive_size_mb = ArchiveService.get_archive_size_mb(archive_path)

            # Step 3: Update database (100%)
            self._log("\n=== Step 3: Updating database ===")
            self.db.archive_project(
                self.project_uuid,
                self.archive_path,
                self.archive_size_mb
            )

            self.progress_bar.setValue(100)
            self._log(f"\n✓ Archive complete: {archive_filename}")
            self._log(f"✓ Archive size: {self.archive_size_mb:.2f} MB")
            self._log(f"✓ Archive location: {self.archive_path}")

            self.success = True

            # Check if original directory should be deleted
            if self.delete_original_checkbox.isChecked():
                self._log("\n=== Step 4: Deleting original directory ===")
                if self._delete_original_directory():
                    self._log(f"✓ Original directory deleted: {self.project_path}")
                else:
                    self._log(f"⚠ Warning: Could not fully delete original directory")

            # Success message
            delete_msg = ""
            if self.delete_original_checkbox.isChecked():
                delete_msg = f"\n\n⚠ Original directory deleted from disk!"

            QtWidgets.QMessageBox.information(
                self,
                "Archive Complete",
                f"Project archived successfully!\n\n"
                f"Archive: {archive_filename}\n"
                f"Size: {self.archive_size_mb:.2f} MB\n"
                f"Location: {archive_dir}"
                f"{delete_msg}"
            )

            self.accept()

        except Exception as e:
            self.progress_bar.setValue(0)
            self._log(f"\n✗ Error: {str(e)}")

            QtWidgets.QMessageBox.critical(
                self,
                "Archive Failed",
                f"Failed to archive project:\n\n{str(e)}"
            )

            self.archive_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
