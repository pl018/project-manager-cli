# Project Structure Documentation

This document describes the refactored structure of the project manager CLI application.

## Overview

The application has been refactored from a single monolithic file (`pyproject.py`) into a well-organized modular structure following Python best practices.

## Directory Structure

```
project-manager-cli/
├── src/
│   └── project_manager_cli/
│       ├── __init__.py
│       ├── app.py
│       ├── cli.py
│       ├── config.py
│       ├── exceptions.py
│       ├── main.py
│       ├── models.py
│       └── services/
│           ├── __init__.py
│           ├── ai_service.py
│           ├── database_service.py
│           ├── logging_service.py
│           ├── project_manager_service.py
│           └── project_service.py
├── pyproject.py                 # Back-compat entrypoint
├── main.py                      # Back-compat entrypoint
├── pyproject.toml               # Packaging config
├── requirements.txt
├── README.md
├── INSTALL.md
└── STRUCTURE.md
```

## Module Descriptions

### Core Modules

#### `src/project_manager_cli/config.py`
- Contains the `Config` class with all application configuration
- Environment variables, file paths, API settings
- Configuration validation logic

#### `src/project_manager_cli/models.py`
- Pydantic data models for type validation
- `ProjectInfo`, `AIGeneratedInfo`, `ProjectEntry` classes
- Ensures data integrity and provides IDE support

#### `src/project_manager_cli/exceptions.py`
- Custom exception classes
- `ConfigError`, `ProjectManagerError`, `AITaggingError`
- Provides specific error handling for different failure modes

#### `src/project_manager_cli/app.py`
- Main `Application` class
- Orchestrates the entire application flow
- Handles initialization, configuration, and service coordination

#### `src/project_manager_cli/main.py`
- Entry point function
- Argument parsing for test mode
- Application instantiation and execution

### Service Modules

#### `src/project_manager_cli/services/ai_service.py`
- `AITaggingService` class
- OpenAI API integration
- Tag generation and content analysis

#### `src/project_manager_cli/services/database_service.py`
- `DatabaseManager` class
- SQLite database operations
- Project data persistence and retrieval

#### `src/project_manager_cli/services/logging_service.py`
- `LoggingManager` class
- Application logging setup
- Receipt generation for operations

#### `src/project_manager_cli/services/project_service.py`
- `ProjectContext` class
- Project information collection
- File sampling for AI analysis

#### `src/project_manager_cli/services/project_manager_service.py`
- `ProjectManager` class
- Cursor Project Manager integration
- JSON file generation

## Entry Points

### New Entry Point: `main.py`
```bash
python main.py [options]
```

### Legacy Entry Point: `pyproject.py`
```bash
python pyproject.py [options]
```
The legacy entry point is maintained for backward compatibility and imports from the new structure.

## Benefits of the Refactored Structure

### 1. **Separation of Concerns**
- Each module has a single, well-defined responsibility
- Services are isolated and can be tested independently
- Configuration is centralized and easily manageable

### 2. **Maintainability**
- Smaller, focused files are easier to understand and modify
- Changes to one service don't affect others
- Clear dependency relationships

### 3. **Testability**
- Individual services can be unit tested
- Mock objects can be easily injected
- Test coverage is more granular

### 4. **Reusability**
- Services can be imported and used in other contexts
- Clean interfaces allow for easy extension
- Modular design supports plugin architecture

### 5. **Code Quality**
- Better IDE support with proper imports
- Type hints are more effective with smaller modules
- Linting and static analysis are more precise

## Usage

The refactored application maintains full backward compatibility:

```bash
# Using the new entry point
python main.py --tag development

# Using the legacy entry point
python pyproject.py --tag development --folder

# Test mode
python main.py --test
```

All existing command-line arguments and functionality remain unchanged.

## Future Enhancements

The modular structure enables easy addition of new features:

1. **Plugin System**: New services can be added to the `services/` directory
2. **Configuration Sources**: Multiple config sources (files, environment, CLI)
3. **Alternative Storage**: Easy to add new database backends
4. **API Integrations**: Additional AI services or project management tools
5. **Testing Framework**: Comprehensive test suite with service mocking

## Migration Notes

- The original `pyproject.py` file is preserved for compatibility
- All existing functionality is maintained
- Environment variables and configuration remain the same
- Database schema and file formats are unchanged 