# CoreSecFrame
A modular terminal-based framework for managing and executing cybersecurity tools on Linux systems.

## Overview
SecTools Framework provides a unified interface for managing security testing tools through an interactive command-line environment. Features session management, real-time logging, and an extensible plugin system.

## Key Features
- Modular tool management and execution
- Interactive terminal interface with tmux sessions
- Real-time logging and output management 
- Guided and direct execution modes
- Easy tool integration through templates
- Automated dependency management

## Quick Start

For detailed installation instructions, see [INSTALL.md](INSTALL.md)

## Basic Commands
- `help`: Show framework help
- `list`: List available tools
- `use <tool>`: Select a tool
- `info`: Show tool details
- `sessions`: List active sessions
- `clear`: Clear screen

## Adding New Tools
1. Use provided templates in `templates/`
2. Create module in `modules/` directory
3. Implement tool class inheriting from `ToolModule`
4. Framework will detect new module automatically

## Requirements
- Python 3.x
- tmux
- Dependencies listed in requirements.txt

## Contributing
1. Fork the project
2. Create feature branch
3. Submit pull request

## License
This project is licensed under GNU GPL v3.
See LICENSE file for details.

## Contact
Project: [https://github.com/yourusername/sectools](https://github.com/yourusername/sectools)
