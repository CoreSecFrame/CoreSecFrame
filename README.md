# Core Security Framework
A modular framework for managing and executing security tools on Linux systems.

[Visit our official website for complete documentation, images, etc](https://coresecframe.github.io/)

## Features
- Modular tool management
- Automatic dependency installation and updates
- Guided and direct modes for each tool
- Enhanced command-line interface 
- External module repository
- Centralized management of tools and operating system

## Installation
### 1. Clone the repository
```bash
git clone https://github.com/CoreSecFrame/CoreSecFrame.git
cd CoreSecFrame
```

### 2. Recommended installation method (Virtual Environment)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. System Dependencies
Based on your Linux distribution:

#### Debian/Kali Linux
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv tmux
```

### 4. Global Installation 
There are two methods to install CoreSecFrame globally:

#### Method 1: Installation in /opt (Recommended)
```bash
# Create application directory
sudo mkdir -p /opt/coresecframe

# Copy framework files
sudo cp -r . /opt/coresecframe/

# Create symbolic link
sudo ln -s /opt/coresecframe/main.py /usr/local/bin/coresecframe

# Set permissions
sudo chmod +x /usr/local/bin/coresecframe
sudo chmod -R 755 /opt/coresecframe
```

To run CoreSecFrame you'll need sudo privileges:
```bash
sudo coresecframe
```

#### Method 2: Using Shell Alias
```bash
# Add alias to your shell configuration file
echo "alias coresecframe='python3 $(pwd)/main.py'" >> ~/.bashrc
# Or if using zsh
echo "alias coresecframe='python3 $(pwd)/main.py'" >> ~/.zshrc

# Reload configuration
source ~/.bashrc # Or source ~/.zshrc
```

## Python Dependencies
The following dependencies will be automatically installed through requirements.txt:
- **psutil**: System monitoring
- **cmd2**: Command-line interface enhancements  
- **colorama**: Terminal color support
- **prompt_toolkit**: Enhanced input handling
- **paramiko**: SSH protocol implementation
- **eventlet**: Concurrent networking library
- **requests**: HTTP library

## Usage
You can start the framework in two ways:
```bash
# If installed globally
sudo coresecframe

# Or from the project directory
python3 main.py
```

## Project Structure
```
CoreSecFrame/
├── core/           # Framework core
├── modules/        # Tool modules
├── scripts/        # Tool scripts
├── venv/          # Virtual environment (if used)
├── main.py        # Entry point
├── requirements.txt
└── README.md
```

## Adding New Tools
1. On first launch, the framework will check for available tools in our official repository
2. Tool URLs will be cached locally for download using the "download <tool>" command
3. Every 12 hours, the framework will check for new modules in the official repository and update accordingly

## Contributing
1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License
This project is licensed under GNU GPLv3 - see the [LICENSE](LICENSE) file for details.

## Contact
Project Link: [https://github.com/CoreSecFrame/CoreSecFrame](https://github.com/CoreSecFrame/CoreSecFrame)
