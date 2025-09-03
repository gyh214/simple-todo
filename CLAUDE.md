# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Windows TODO Panel is a standalone desktop application built with Python Tkinter that provides a compact, modern TODO management interface with system tray integration. The application features Magic UI styling, web link functionality, and persistent data storage.

## Common Commands

### Building the Application
```bash
# Build using PyInstaller spec file (recommended)
pyinstaller --clean --noconfirm todo_panel.spec

# Alternative build using build script with options
python build.py                    # Standard build
python build.py --debug            # Debug build with console output
python build.py --no-upx           # Build without UPX compression
python build.py --keep-temp        # Keep temporary files for debugging
```

### Testing and Development
```bash
# Run the main application
cd src && python main.py

# Alternative entry point
cd src && python run_todo_panel.py

# Run in debug mode with logging
cd src && python main.py --debug

# Run UI component tests
python test_ui.py

# Run specific component tests
cd src && python test_todo_manager.py
cd src && python test_main.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

## Architecture Overview

### Core Components Structure
```
src/
├── main.py                 # Main application with system tray integration
├── run_todo_panel.py       # Alternative application entry point
├── ui_components.py        # UI widgets and Magic UI styling
├── todo_manager.py         # Synchronous TODO data management
├── todo_manager_fixed.py   # Enhanced data manager with position/drag-drop support
├── async_todo_manager.py   # Asynchronous TODO management with batching
└── tooltip.py             # Custom tooltip widget
```

### Key Architectural Patterns

**Multi-layered Architecture:**
- **Presentation Layer**: `ui_components.py` - TodoPanelApp, TodoItemWidget, ClickableTextWidget
- **Business Logic**: `todo_manager.py` / `async_todo_manager.py` - Data persistence and validation
- **System Integration**: `main.py` - System tray, single instance management, logging

**Data Flow:**
1. UI events → TodoPanelApp → TodoManager → JSON file storage
2. File changes → TodoManager → UI refresh via observer pattern
3. System tray interactions → MainApplication → TodoPanelApp visibility control

**Key Design Decisions:**
- **Single Instance Management**: Uses socket-based locking mechanism on port 65432
- **System Tray Integration**: Custom pystray implementation with dynamic icon generation
- **Data Persistence**: JSON-based storage in user's AppData/Local/TodoPanel
- **UI Responsiveness**: AsyncTodoManager provides non-blocking file operations with batch saving
- **Compact Display**: Single-line text display with truncation for maximum information density
- **URL Handling**: Regex pattern matching in ClickableTextWidget for web link functionality

### Widget Hierarchy
```
TodoPanelApp (main window)
├── TodoListWidget (scrollable container)
│   ├── TodoItemWidget (individual todo items)
│   │   ├── ClickableTextWidget (URL-aware text display)
│   │   ├── Status indicators (completion, priority)
│   │   └── Action buttons (complete, delete)
└── TodoInputWidget (new todo creation)
```

### Data Management Patterns
- **Synchronous**: `TodoManager` for immediate operations
- **Asynchronous**: `AsyncTodoManager` for background operations with batching
- **Thread Safety**: RLock-based synchronization for concurrent access
- **Error Recovery**: Automatic backup system with retry logic
- **Validation**: Schema validation for todo items and JSON integrity

## Important Implementation Details

### System Tray Integration
- Application minimizes to system tray instead of closing
- Dynamic icon generation using PIL for consistent branding
- Right-click context menu with show/hide/exit options
- Single instance enforcement prevents multiple app launches

### Magic UI Styling and Display Philosophy
- **Dark/Light theme support** with automatic detection
- **Ultra-compact design** optimized for maximum information density
- **Single-line constraint**: Every todo item uses exactly one line (no multi-line wrapping)
- **Partial text visibility**: Long text is truncated but remains partially visible
- **Hover effects** and smooth transitions for modern UX
- **Color schemes** defined in `ui_components.py` theme dictionaries

### Text Display and Clickable Link Functionality
- **Single-line display**: All todo items display in exactly one line (`wrap='none'`, `height=1`)
- **Text truncation**: Long text is cut off but partially visible based on window width
- **Dual Link Support**: Automatic recognition of both web links and file paths
  - **Web links**: `r'https?://[^\s]+|www\.[^\s]+'` - displayed in blue (#007acc)
  - **File paths**: Windows absolute, relative, and network paths - displayed in orange (#ff9800)
- **Clickable interaction**: Links embedded in todo text using Tkinter text tags with hover effects
- **Smart opening**: 
  - Web links: `webbrowser.open()` for browser handling
  - File paths: `os.startfile()` for Windows default application opening
- **Security features**: Executable file detection with user confirmation dialogs
- **Multiple links**: Supports multiple clickable URLs and file paths per todo item
- **Visual feedback**: Distinct colors, tooltips ("웹사이트 열기" / "파일 열기"), and cursor changes

### Build System
- **PyInstaller**: Single executable generation via `todo_panel.spec` or `build.py`
- **Spec File**: Advanced configuration through `todo_panel.spec` with hidden imports and excludes
- **Build Options**: Debug mode, UPX compression control, temp file management
- **Icon/Version**: Automatic embedding of Windows metadata via `TodoPanel.ico` and `version_info.txt`
- **Dependencies**: External (pystray, Pillow, psutil) + Built-in (tkinter, json, uuid, pathlib, threading, datetime, logging, os, sys)
- **Size Optimization**: UPX compression (optional), module exclusion, and bundling optimization

### Data Compatibility
- JSON schema maintained for backward compatibility
- Migration logic handles schema updates transparently
- User data stored in standard Windows AppData locations
- Automatic backup and recovery mechanisms

## Development Guidelines

- Always test both sync and async TodoManager implementations
- Consider using `todo_manager_fixed.py` for enhanced features like drag-drop positioning
- Maintain data format compatibility when modifying schemas
- Use the existing tooltip system for UI help text
- Follow Magic UI color schemes for consistent styling
- Test system tray functionality on Windows platform
- Verify single executable builds before releasing using both spec file and build script methods
- Run comprehensive tests including UI responsiveness and file operations
- Use appropriate build options (`--debug`, `--no-upx`, `--keep-temp`) based on development needs

### ⚠️ Critical Development Notes

- **Size and Font Size Values**: ALWAYS use integer values only for all size-related parameters (font size, width, height, padding, etc.). Using decimal/float values will cause runtime errors in Tkinter.
  - ✅ Correct: `font=('Segoe UI', 9)`, `width=100`, `height=25`
  - ❌ Incorrect: `font=('Segoe UI', 9.5)`, `width=100.5`, `height=25.3`
- This applies to all UI components: buttons, labels, text widgets, frames, and any Tkinter widget properties

## Additional Components

### Alternative Entry Points
- **run_todo_panel.py**: Simplified application launcher that imports and runs main.py
- Useful for testing or when direct main.py execution is not suitable

### Enhanced Data Management
- **todo_manager_fixed.py**: Advanced TodoManager with additional features:
  - Position-based ordering for drag-and-drop functionality
  - Enhanced CRUD operations with comprehensive error handling
  - Thread-safe operations with proper locking
  - Data import/export capabilities
  - Statistics and filtering methods

### Build Configuration Details
- **todo_panel.spec**: PyInstaller specification file with:
  - Hidden imports for all required modules
  - Module exclusions for test files
  - Icon and version file integration
  - Windows-specific optimizations
  - UPX compression settings