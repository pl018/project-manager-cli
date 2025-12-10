"""Custom exceptions for project manager."""


class ProjectManagerError(Exception):
    """Base exception for project manager errors."""
    pass


class ConfigError(ProjectManagerError):
    """Configuration error exception."""
    pass


class DatabaseError(ProjectManagerError):
    """Database operation error."""
    pass


class AITaggingError(ProjectManagerError):
    """AI tagging operation error."""
    pass


class ToolIntegrationError(ProjectManagerError):
    """Tool integration error."""
    pass


class ValidationError(ProjectManagerError):
    """Data validation error."""
    pass
