# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Windows TODO Panel is a standalone desktop application built with Python Tkinter that provides a compact, modern TODO management interface with system tray integration. The application features Magic UI styling, web link functionality, and persistent data storage.

## Common Commands

### Building the Application
```bash
# Build using PyInstaller spec file (recommended)
pyinstaller --clean --noconfirm todo_panel.spec

# Alternative build using build script
python build.py

# Debug build with console output
python build.py --debug

# Build without UPX compression
python build.py --no-upx
```

### Testing and Development
```bash
# Run the main application
cd src && python main.py

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
├── ui_components.py        # UI widgets and Magic UI styling
├── todo_manager.py         # Synchronous TODO data management
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

### Text Display and Web Link Functionality
- **Single-line display**: All todo items display in exactly one line (`wrap='none'`, `height=1`)
- **Text truncation**: Long text is cut off but partially visible based on window width
- **URL pattern**: `r'https?://[^\s]+|www\.[^\s]+'`
- **Clickable links**: URLs embedded in todo text using Tkinter text tags
- **Browser integration**: `webbrowser.open()` for link handling
- **Multiple URLs**: Supports multiple clickable URLs per todo item

### Build System
- **PyInstaller**: Single executable generation via `todo_panel.spec`
- **Icon/Version**: Automatic embedding of Windows metadata
- **Dependencies**: Minimal external requirements (pystray, Pillow, psutil)
- **Size Optimization**: UPX compression and module exclusion

### Data Compatibility
- JSON schema maintained for backward compatibility
- Migration logic handles schema updates transparently
- User data stored in standard Windows AppData locations
- Automatic backup and recovery mechanisms

## Development Guidelines

- Always test both sync and async TodoManager implementations
- Maintain data format compatibility when modifying schemas
- Use the existing tooltip system for UI help text
- Follow Magic UI color schemes for consistent styling
- Test system tray functionality on Windows platform
- Verify single executable builds before releasing
- Run comprehensive tests including UI responsiveness and file operations