"""Custom exceptions for the project manager CLI."""


class ConfigError(Exception):
    """Configuration error exception."""
    pass


class ProjectManagerError(Exception):
    """Project manager operation error."""
    pass


class AITaggingError(Exception):
    """AI tagging operation error."""
    pass 