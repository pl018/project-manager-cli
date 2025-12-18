"""Tool integration registry."""

from typing import Dict, List, Optional

from .base import ToolIntegration
from .cursor import CursorIntegration
from .explorer import ExplorerIntegration
from .jetbrains import IntelliJIntegration, PyCharmIntegration, WebStormIntegration
from .terminal import TerminalIntegration, WarpIntegration
from .vscode import VSCodeIntegration


class ToolRegistry:
    """Registry of all available tool integrations."""

    def __init__(self):
        self._tools: Dict[str, ToolIntegration] = {}
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize all tool integrations."""
        tools = [
            CursorIntegration(),
            VSCodeIntegration(),
            VSCodeIntegration(insiders=True),
            ExplorerIntegration(),
            PyCharmIntegration(),
            WebStormIntegration(),
            IntelliJIntegration(),
            TerminalIntegration(),
            WarpIntegration(),
        ]

        for tool in tools:
            self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ToolIntegration]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_available_tools(self) -> List[ToolIntegration]:
        """Get all available (installed) tools."""
        return [tool for tool in self._tools.values() if tool.is_available()]

    def get_all_tools(self) -> List[ToolIntegration]:
        """Get all registered tools."""
        return list(self._tools.values())

    def open_project(self, tool_name: str, path: str) -> bool:
        """Open a project using specified tool."""
        tool = self.get_tool(tool_name)
        if tool and tool.is_available():
            return tool.open_project(path)
        return False

    def get_default_tool(self) -> Optional[ToolIntegration]:
        """Get the default tool (first available)."""
        available = self.get_available_tools()
        return available[0] if available else None
