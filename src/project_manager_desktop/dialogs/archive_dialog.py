"""Archive project dialog with progress indicator."""

from pathlib import Path
from typing import Optional

from PySide6 import QtWidgets

from core.database import DatabaseManager
from project_manager_cli.services.archive_service import ArchiveService
from project_manager_cli.services.git_service import GitService
from ..theme import TOKENS


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
        warning.setStyleSheet(
            f"color: {TOKENS.warning}; padding: 10px; "
            f"background-color: rgba(240, 179, 91, 0.10); border: 1px solid rgba(240, 179, 91, 0.35); "
            "border-radius: 8px;"
        )
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
        self.delete_original_checkbox.setStyleSheet(f"color: {TOKENS.danger}; font-weight: 600;")
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
            self.git_status_label.setStyleSheet(f"color: {TOKENS.success};")
            return

        has_changes, status_output = git_service.has_uncommitted_changes(self.project_path)

        if has_changes:
            self.git_status_label.setText(
                "⚠ Warning: Uncommitted git changes detected!\n"
                "Please review before archiving."
            )
            self.git_status_label.setStyleSheet(f"color: {TOKENS.warning}; font-weight: 600;")

            # Show git status in progress log
            self.progress_log.appendPlainText("Uncommitted changes:")
            self.progress_log.appendPlainText(status_output or "")
        else:
            self.git_status_label.setText("✓ Git repository is clean (no uncommitted changes)")
            self.git_status_label.setStyleSheet(f"color: {TOKENS.success};")

    def _log(self, message: str):
        """Add message to progress log."""
        self.progress_log.appendPlainText(message)
        QtWidgets.QApplication.processEvents()  # Update UI

    def _delete_original_directory(self) -> bool:
        """
        Delete the original project directory using an elevated PowerShell process.

        Returns:
            True if successful, False otherwise
        """
        import base64
        import subprocess

        # Use a PowerShell single-quoted string for path safety; escape embedded single quotes.
        path_ps = self.project_path.replace("'", "''")

        # Inner payload runs elevated.
        inner_ps = rf"""
$ErrorActionPreference = "Stop"
$path = '{path_ps}'

if (Test-Path -LiteralPath $path) {{
  # avoid killing the current PowerShell process
  $myPid = $PID

  if (-not (Get-Command handle64.exe -ErrorAction SilentlyContinue)) {{
    Write-Error "handle64.exe not found on PATH. Put Sysinternals handle64.exe on PATH or use an absolute path."
  }}

  $pids = (& handle64.exe -accepteula -nobanner $path 2>$null |
    ForEach-Object {{ if ($_ -match '\spid:\s+(\d+)\s') {{ [int]$matches[1] }} }} |
    Sort-Object -Unique
  ) | Where-Object {{ $_ -ne $myPid }}

  if ($pids) {{
    Stop-Process -Id $pids -Force -ErrorAction SilentlyContinue
  }}

  try {{
    Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction Stop
  }}
  catch {{
    takeown /F $path /R /D Y | Out-Null
    icacls $path /grant "$env:USERNAME:(OI)(CI)F" /T /C | Out-Null
    Remove-Item -LiteralPath $path -Recurse -Force
  }}
}}
"""

        enc = base64.b64encode(inner_ps.encode("utf-16le")).decode("ascii")

        # Outer wrapper: elevate if needed, wait, and return exit code.
        outer_ps = rf"""
$enc = "{enc}"
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {{
  pwsh.exe -NoProfile -ExecutionPolicy Bypass -EncodedCommand $enc
  exit $LASTEXITCODE
}} else {{
  $p = Start-Process pwsh.exe -Verb RunAs -Wait -PassThru -ArgumentList @(
    '-NoProfile','-ExecutionPolicy','Bypass','-EncodedCommand',$enc
  )
  exit $p.ExitCode
}}
"""

        try:
            self._log("Requesting administrator rights to force-close handles and delete directory...")
            QtWidgets.QApplication.processEvents()

            result = subprocess.run(
                ["pwsh.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", outer_ps],
                capture_output=True,
                text=True,
                timeout=180,
            )

            # If user cancels UAC, you'll typically get a non-zero exit code.
            if result.stdout and result.stdout.strip():
                self._log(result.stdout.strip())
            if result.stderr and result.stderr.strip():
                self._log(result.stderr.strip())

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            self._log("Timed out while deleting directory.")
            return False
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
            try:
                # Use transaction to ensure database consistency
                with self.db.transaction():
                    self.db.archive_project(
                        self.project_uuid,
                        self.archive_path,
                        self.archive_size_mb
                    )
            except Exception as db_error:
                # If database update fails, clean up the archive file
                self._log(f"⚠ Database update failed: {db_error}")
                self._log("Cleaning up archive file...")
                if archive_path.exists():
                    archive_path.unlink()
                raise Exception(f"Database update failed: {db_error}")

            self.progress_bar.setValue(100)
            self._log(f"\n✓ Archive complete: {archive_filename}")
            self._log(f"✓ Archive size: {self.archive_size_mb:.2f} MB")
            self._log(f"✓ Archive path: {self.archive_path}")

            # Step 4 (optional): Delete original directory
            if self.delete_original_checkbox.isChecked():
                self._log("\n=== Step 4: Deleting original project directory ===")
                self.progress_bar.setValue(95)

                deleted_ok = self._delete_original_directory()
                if deleted_ok:
                    self._log("✓ Original project directory deleted")
                else:
                    self._log("⚠ Failed to delete original directory (archive still created)")

                self.progress_bar.setValue(100)

            self.success = True
            self.accept()

        except Exception as e:
            self._log(f"\n✗ Archive failed: {e}")
            QtWidgets.QMessageBox.critical(self, "Archive Failed", str(e))
            self.cancel_btn.setEnabled(True)
            self.cancel_btn.setText("Close")
        finally:
            # Ensure the UI is left in a usable state.
            if not self.success:
                self.cancel_btn.setEnabled(True)
