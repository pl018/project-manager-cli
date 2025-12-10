"""Data models for the project manager CLI."""

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


class ProjectEntry(BaseModel):
    """Project entry model for Cursor Project Manager."""
    name: str
    rootPath: str
    paths: List[str] = Field(default_factory=list)
    tags: List[str]
    enabled: bool = True
    project_uuid: Optional[str] = None 