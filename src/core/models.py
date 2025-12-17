"""Data models for project manager."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    """Project information model."""
    rootFolderName: str
    rootFolderPath: str
    ParentRootFolderName: str
    cwdfolderName: str


class AIGeneratedInfo(BaseModel):
    """AI-generated information about the project."""
    tags: List[str]
    app_name: Optional[str] = None
    app_description: Optional[str] = None


class Tag(BaseModel):
    """Tag model with color and icon."""
    name: str
    color: str = "#3b82f6"
    icon: str = "🏷️"


class ToolConfig(BaseModel):
    """Tool-specific configuration."""
    project_uuid: str
    tool_name: str
    config: dict = Field(default_factory=dict)


class Project(BaseModel):
    """Complete project model with all metadata."""
    uuid: str
    name: str
    root_path: str
    tags: List[str] = Field(default_factory=list)
    ai_app_name: Optional[str] = None
    ai_app_description: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    favorite: bool = False
    last_opened: Optional[datetime] = None
    open_count: int = 0
    date_added: datetime
    last_updated: datetime
    enabled: bool = True
    color_theme: str = "blue"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ProjectEntry(BaseModel):
    """Project entry model for Cursor Project Manager (backward compatibility)."""
    name: str
    rootPath: str
    paths: List[str] = Field(default_factory=list)
    tags: List[str]
    enabled: bool = True
    project_uuid: Optional[str] = None


class SearchFilter(BaseModel):
    """Search and filter criteria."""
    text: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    tag_mode: str = "AND"  # AND or OR
    favorites_only: bool = False
    tools: List[str] = Field(default_factory=list)
    sort_by: str = "name"  # name, date, frequency, updated
    sort_order: str = "asc"  # asc or desc


class DocFile(BaseModel):
    """Documentation file model for markdown file browser."""
    filename: str
    full_path: Path
    relative_path: str
    extension: str
    size_bytes: int
    modified_date: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            Path: lambda v: str(v)
        }
