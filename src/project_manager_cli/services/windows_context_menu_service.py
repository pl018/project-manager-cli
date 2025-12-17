from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ContextMenuInstallResult:
    installed: bool
    message: str
    pwsh_path: str
    python_exe: str


class WindowsContextMenuService:
    """
    Windows Explorer context menu integration (HKCU) for running pm-cli on a folder.

    This installs two entries:
      - Right-click a folder item:  HKCU\\Software\\Classes\\Directory\\shell\\...
      - Right-click folder background: HKCU\\Software\\Classes\\Directory\\Background\\shell\\...

    Both open a new PowerShell window, run `pm-cli run` (via `python -m project_manager_cli.cli run`)
    with working directory set to the selected folder, then wait for a keypress before closing.
    """

    MENU_KEY_NAME = "pm-cli.run"
    MENU_LABEL = "Run Project Manager (pm-cli)"

    def is_supported(self) -> bool:
        return sys.platform.startswith("win")

    def install(self, *, force: bool = False) -> ContextMenuInstallResult:
        if not self.is_supported():
            return ContextMenuInstallResult(
                installed=False,
                message="Not on Windows; Explorer context menu integration is only supported on Windows.",
                pwsh_path="",
                python_exe="",
            )

        pwsh_path = self._find_pwsh()
        python_exe = str(Path(sys.executable).resolve())

        # Build the commands for both kinds of shell entries.
        cmd_for_folder_item = self._build_registry_command(
            pwsh_path=pwsh_path,
            python_exe=python_exe,
            start_dir_placeholder="%1",
        )
        cmd_for_background = self._build_registry_command(
            pwsh_path=pwsh_path,
            python_exe=python_exe,
            start_dir_placeholder="%V",
        )

        try:
            import winreg  # type: ignore
        except Exception as e:  # pragma: no cover
            return ContextMenuInstallResult(
                installed=False,
                message=f"Failed to import winreg; cannot install context menu. Error: {e}",
                pwsh_path=pwsh_path,
                python_exe=python_exe,
            )

        base_dir = r"Software\Classes\Directory\shell"
        base_bg = r"Software\Classes\Directory\Background\shell"

        # Create keys under HKCU (no admin).
        self._write_menu_key(
            winreg=winreg,
            base=base_dir,
            command=cmd_for_folder_item,
            force=force,
        )
        self._write_menu_key(
            winreg=winreg,
            base=base_bg,
            command=cmd_for_background,
            force=force,
        )

        return ContextMenuInstallResult(
            installed=True,
            message=(
                "Installed Explorer context menu entry. You can now right-click a folder (or folder background) "
                "and run Project Manager in a new PowerShell window."
            ),
            pwsh_path=pwsh_path,
            python_exe=python_exe,
        )

    def uninstall(self) -> bool:
        if not self.is_supported():
            return False
        try:
            import winreg  # type: ignore
        except Exception:
            return False

        removed_any = False
        for base in (
            r"Software\Classes\Directory\shell",
            r"Software\Classes\Directory\Background\shell",
        ):
            key_path = base + "\\" + self.MENU_KEY_NAME
            removed_any = self._delete_tree(winreg, winreg.HKEY_CURRENT_USER, key_path) or removed_any
        return removed_any

    def is_installed(self) -> bool:
        if not self.is_supported():
            return False
        try:
            import winreg  # type: ignore
        except Exception:
            return False

        for base in (
            r"Software\Classes\Directory\shell",
            r"Software\Classes\Directory\Background\shell",
        ):
            key_path = base + "\\" + self.MENU_KEY_NAME
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path):
                    return True
            except FileNotFoundError:
                continue
        return False

    # -------------------------
    # Internals
    # -------------------------

    def _find_pwsh(self) -> str:
        """
        Prefer PowerShell 7 (pwsh). Fall back to Windows PowerShell if needed.
        Returns an executable path or name that can be invoked.
        """
        which = shutil.which("pwsh")
        if which:
            return which

        candidates = [
            r"C:\Program Files\PowerShell\7\pwsh.exe",
            r"C:\Program Files (x86)\PowerShell\7\pwsh.exe",
        ]
        for c in candidates:
            if Path(c).exists():
                return c

        # Last resort: Windows PowerShell (still works for our pause behavior).
        return "powershell.exe"

    def _build_registry_command(self, *, pwsh_path: str, python_exe: str, start_dir_placeholder: str) -> str:
        """
        Return the command string stored in the registry for Explorer.

        Uses cmd.exe + start to open a NEW window with working directory set to the clicked folder.
        """
        # PowerShell script: run pm-cli, then pause for keypress.
        # Use python -m to avoid relying on pm-cli being on PATH.
        ps_script = (
            "& { "
            "try { "
            f"& '{python_exe}' -m project_manager_cli.cli run "
            "} finally { "
            "Write-Host ''; "
            "Write-Host 'Press any key to close...'; "
            "$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown'); "
            "} "
            "}"
        )

        # cmd.exe string with quoting:
        # - start "" sets window title
        # - /D sets working directory
        # - call pwsh and run -Command "<script>"
        cmd = (
            f'cmd.exe /c start "" /D "{start_dir_placeholder}" "{pwsh_path}" '
            f'-NoLogo -NoProfile -ExecutionPolicy Bypass -Command "{ps_script}"'
        )
        return cmd

    def _write_menu_key(self, *, winreg, base: str, command: str, force: bool) -> None:
        """
        Write:
          HKCU\\<base>\\<MENU_KEY_NAME>\\(Default) = MENU_LABEL
          HKCU\\<base>\\<MENU_KEY_NAME>\\Icon = python.exe
          HKCU\\<base>\\<MENU_KEY_NAME>\\command\\(Default) = <command>
        """
        root = winreg.HKEY_CURRENT_USER
        menu_key_path = base + "\\" + self.MENU_KEY_NAME
        command_key_path = menu_key_path + "\\command"

        if not force:
            try:
                with winreg.OpenKey(root, command_key_path):
                    # Already exists; leave as-is.
                    return
            except FileNotFoundError:
                pass

        with winreg.CreateKeyEx(root, menu_key_path, 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, self.MENU_LABEL)
            winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, str(Path(sys.executable).resolve()))

        with winreg.CreateKeyEx(root, command_key_path, 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, command)

    def _delete_tree(self, winreg, root, sub_key: str) -> bool:
        """
        Recursively delete a registry tree. Returns True if anything was deleted.
        """
        try:
            with winreg.OpenKey(root, sub_key, 0, winreg.KEY_READ | winreg.KEY_WRITE) as k:
                # Delete children first
                while True:
                    try:
                        child = winreg.EnumKey(k, 0)
                    except OSError:
                        break
                    self._delete_tree(winreg, root, sub_key + "\\" + child)
        except FileNotFoundError:
            return False

        try:
            winreg.DeleteKey(root, sub_key)
            return True
        except FileNotFoundError:
            return False


