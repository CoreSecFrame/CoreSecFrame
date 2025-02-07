import cmd
import importlib
import pkgutil
import subprocess
import signal
import os
import getpass
from datetime import datetime
from pathlib import Path
import shutil
from typing import Dict, Optional, List
import platform
from .terminal_management import TerminalManager
from .sessions_manager import SessionManager
from .colors import Colors
from .base import ToolModule, PackageManager


class FrameworkInterface(cmd.Cmd):
    # Obtener nombre de usuario
    username = getpass.getuser()
    current_time = datetime.now().strftime("%H:%M:%S")

    intro = f'''{Colors.CYAN}
    ╔══════════════════════════════════════════════════════════════════════╗
    ║    {Colors.ACCENT}╭───────────────────────────────────────────────────────────╮{Colors.CYAN}     ║
    ║    {Colors.ACCENT}│{Colors.SECONDARY}                  {Colors.BOLD}CoreSecurityFramework                    {Colors.ACCENT}│     {Colors.CYAN}║
    ║    {Colors.ACCENT}╰───────────────────────────────────────────────────────────╯{Colors.CYAN}     ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║                                                                      ║
    ║           {Colors.SUCCESS}●{Colors.PRIMARY} System  {Colors.TEXT}Type {Colors.HIGHLIGHT}'help'{Colors.TEXT} or {Colors.HIGHLIGHT}'?'{Colors.TEXT} to view commands     {Colors.CYAN}         ║
    {Colors.CYAN}║           {Colors.ERROR}●{Colors.PRIMARY} Sessions {Colors.TEXT}Use {Colors.HIGHLIGHT}'sessions'{Colors.TEXT} to manage sessions    {Colors.CYAN}           ║
    {Colors.CYAN}║                                                                      ║
    {Colors.CYAN}╚══════════════════════════════════════════════════════════════════════╝
    {Colors.TEXT}Started at {current_time}  |  Licensed under GNU GPLv3{Colors.ENDC}
    {Colors.TEXT}CoreSecurityFramework v1.0.3  {Colors.ACCENT}Developed with {Colors.ACCENT} ♥ {Colors.PRIMARY}by {Colors.SECONDARY} CoreSecurity Team{Colors.ENDC}
    '''

    prompt = f'{Colors.SECONDARY}╭─{Colors.SECONDARY}({Colors.PRIMARY}{username}{Colors.ACCENT}@CoreSec{Colors.SECONDARY}){Colors.SECONDARY}─{Colors.SUBTLE}[{Colors.FAIL}#{Colors.SUBTLE}]{Colors.SECONDARY}\n╰─{Colors.ACCENT}≫ {Colors.TEXT}'
    
    def __init__(self):

        super().__init__()
        self.modules = ToolModule.load_modules()
        self.session_manager = SessionManager()
        TerminalManager.check_tmux_installed()
        signal.signal(signal.SIGINT, self.handle_sigint)
        ToolModule.load_modules()
        TerminalManager.clear_screen()


    def execute_pkg(self, tool_name: str, command_type: str) -> None:
        # Usar el primer módulo disponible para ejecutar el comando
        if self.modules:
            first_module = next(iter(self.modules.values()))
            first_module._execute_package_commands(tool_name, command_type)
        else:
            print("[!] Error: No modules loaded")

    def handle_sigint(self, signum, frame):
        """Manejador personalizado para Ctrl+C"""
        print("\n\n[!] Use 'exit' to exit the framework")
        return

    def default(self, line: str) -> None:
        """Manejador de comandos desconocidos"""
        print(f"{Colors.FAIL}[!] Unknown command: {line}{Colors.ENDC}")
        print(f"{Colors.CYAN}[*] Use 'help' to see available commands{Colors.ENDC}")
        
    def emptyline(self) -> bool:
        """No hacer nada cuando se presiona Enter sin comando"""
        return False

    def do_exit(self, arg: str) -> bool:
        """Exit the framework"""
        if self.session_manager.sessions:
            print(f"\n{Colors.WARNING}[!] There are active sessions. You need to close them before exiting. Do it now? (y/N){Colors.ENDC}")
            if input().lower() != 'y':
                print(f"\n{Colors.CYAN}[*] Returning to framework...{Colors.ENDC}")
                return False
                
            # Call kill_all_sessions and handle its return
            self.session_manager.kill_all_sessions()
            # If there are still sessions (user cancelled killing), return to framework
            if self.session_manager.sessions:
                return False
                
            print(f"\n{Colors.SUBTLE}[*] Should we fear hackers? Intention is at the heart of this discussion.{Colors.ENDC}")
            return True
            
        print(f"\n{Colors.SUBTLE}[*] Should we fear hackers? Intention is at the heart of this discussion.{Colors.ENDC}")
        return True

    def do_install(self, arg: str) -> None:
        """Instala una herramienta"""
        args = arg.split()
        if not args:
            print(f"{Colors.FAIL}[!] Error: You must specify a tool{Colors.ENDC}")
            return
        self.execute_pkg(args[0], 'install')

    def do_update(self, arg: str) -> None:
        """Actualiza una herramienta"""
        args = arg.split()
        if not args:
            print(f"{Colors.FAIL}[!] Error: Debes You must specify a tool{Colors.ENDC}")
            return
        self.execute_pkg(args[0], 'update')

    def do_remove(self, arg: str) -> None:
        """Desinstala una herramienta"""
        args = arg.split()
        if not args:
            print(f"{Colors.FAIL}[!] Error: You must specify a tool{Colors.ENDC}")
            return
        self.execute_pkg(args[0], 'remove')


    def do_use(self, arg: str) -> None:
        """Ejecuta una herramienta o conecta a una sesión
        Uso: use <tool> | use session <id>"""
        args = arg.split()
        if not args:
            print(f"{Colors.FAIL}[!] Error: Incorrect command{Colors.ENDC}")
            print("Usage: use <tool> | use session <id>")
            return

        if args[0].lower() == "session" and len(args) > 1:
            self.session_manager.use_session(args[1])
        else:
            self._use_tool(args[0])

    def _get_mode_selection(self) -> Optional[str]:
        """
        Gets user mode selection with proper error handling
        
        Returns:
            Optional[str]: Selected mode ('1', '2') or None if cancelled
        """
        max_attempts = 3
        attempt = 0
        
        # Store the original SIGINT handler
        original_handler = signal.getsignal(signal.SIGINT)
        
        # Set up our temporary handler
        def temp_handler(signum, frame):
            # Restore original handler immediately
            signal.signal(signal.SIGINT, original_handler)
            # Clear line and raise KeyboardInterrupt to handle it in the try/except
            print('\r', end='')
            raise KeyboardInterrupt
        
        try:
            # Set our temporary handler
            signal.signal(signal.SIGINT, temp_handler)
            
            while attempt < max_attempts:
                try:
                    mode = input(f"\n{Colors.BOLD}Choose mode (1/2/0): {Colors.ENDC}").strip()
                    
                    if mode in ('1', '2', '0'):
                        if mode == '0':
                            print(f"\n{Colors.CYAN}[*] Operation cancelled by user{Colors.ENDC}")
                            return None
                        return mode
                        
                    print(f"{Colors.FAIL}[!] Invalid option. Please select 1 for Guided mode, 2 for Direct mode, or 0 to cancel{Colors.ENDC}")
                    attempt += 1
                    
                except KeyboardInterrupt:
                    # Clear screen and return to framework interface
                    TerminalManager.clear_screen()
                    print(self.intro)
                    return None
                except EOFError:
                    print(f"\n{Colors.CYAN}[*] Input terminated (Ctrl+D){Colors.ENDC}")
                    return None
                    
            print(f"\n{Colors.WARNING}[!] Maximum attempts reached. Cancelling operation{Colors.ENDC}")
            return None
            
        finally:
            # Restore the original handler no matter what
            signal.signal(signal.SIGINT, original_handler)


    def _use_tool(self, tool_name: str) -> None:
        """Method to execute a tool"""
        module = self.modules.get(tool_name.lower())
        if not module:
            print(f"{Colors.FAIL}[!] Error: Tool '{tool_name}' not found{Colors.ENDC}")
            return

        if not module.installed:
            print(f"{Colors.FAIL}[!] Error: Tool {tool_name} is not installed{Colors.ENDC}")
            print(f"{Colors.CYAN}[*] You can install it with the command: install {tool_name}{Colors.ENDC}")
            return

        # Show initial information to user
        print(f"\n{Colors.CYAN}[*] Initializing {module.name} in a new tmux session{Colors.ENDC}")
        print(f"\n{Colors.GREEN}Choose execution mode:{Colors.ENDC}")
        print(f"{Colors.GREEN}1:{Colors.ENDC} Guided mode")
        print(f"{Colors.GREEN}2:{Colors.ENDC} Direct mode")
        print(f"{Colors.GREEN}0:{Colors.ENDC} Cancel")
        
        # Get mode selection with proper error handling
        mode = self._get_mode_selection()
        if not mode:
            return

        # Create and initialize session
        session = self.session_manager.create_session(module.name, module)
        session.start_logging()

        try:
            framework_root = Path(__file__).parent.parent
            
            # Get module path components
            module_path = module.__class__.__module__.split('.')
            module_name = module_path[-1]
            
            # Handle module in category directory
            if len(module_path) > 2:  # modules.Category.module_name
                category = module_path[-2]
                import_path = f"modules.{category}.{module_name}"
            else:  # modules.module_name
                import_path = f"modules.{module_name}"
                
            class_name = module.__class__.__name__

            # Build the command with proper import path
            cmd = (f"cd {framework_root} && "
                f"TERM=xterm-256color python3 -u -c \""
                f"import sys; "
                f"import readline; "
                f"sys.path.append('{framework_root}'); "
                f"from {import_path} import {class_name}; "
                f"tool = {class_name}(); "
                f"tool.{'run_guided' if mode == '1' else 'run_direct'}()\"; "
                f"exec bash -l")

            print(f"\n{Colors.CYAN}[*] Initializing tmux session...{Colors.ENDC}")
            print(f"{Colors.CYAN}[*] Remember:{Colors.ENDC}")
            print(f" • Use {Colors.BOLD}Ctrl+b d{Colors.ENDC} to return to the framework")
            print(f" • Use {Colors.BOLD}sessions use {session.session_id}{Colors.ENDC} to reconnect")
            
            success = TerminalManager.run_in_tmux(
                cmd, 
                session.name,
                f"{module.name} - {'Guided' if mode == '1' else 'Direct'}"
            )
            
            if success:
                print(f"\n{Colors.GREEN}[✓] You have returned to the framework{Colors.ENDC}")
                session.add_to_history(f"Tmux session: {'Guided' if mode == '1' else 'Direct'}")
            else:
                print(f"{Colors.FAIL}[!] Error creating tmux session{Colors.ENDC}")
                session.active = False
                            
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error executing tool: {e}{Colors.ENDC}")
            session.active = False
            session.log(f"Error: {str(e)}")
            import traceback
            print(traceback.format_exc())
        finally:
            if not session.active:
                session.stop_logging()
                session.kill_terminal()
                del self.session_manager.sessions[int(session.session_id)]

    def do_kill(self, arg: str) -> None:
        """
        Termina sesiones.
        Uso: kill session <id> | kill all sessions
        """
        args = arg.split()
        if not args:
            print(f"{Colors.FAIL}[!] Error: incorrect command{Colors.ENDC}")
            print("Usage: kill session <id> | kill all sessions")
            return

        if args[0].lower() == "all" and len(args) > 1 and args[1].lower() == "sessions":
            self.session_manager.kill_all_sessions()
        elif args[0].lower() == "session" and len(args) > 1:
            session_id = args[1]
            self.session_manager.kill_session(session_id)
        else:
            print(f"{Colors.FAIL}[!] Error: Incorrect command{Colors.ENDC}")
            print("Usage: kill session <id> | kill all sessions")

    def do_clear(self, arg: str) -> None:
        """
        Limpia la pantalla o sesiones.
        Uso: clear (limpia pantalla) | clear sessions
        """
        if not arg:
            TerminalManager.clear_screen()
            print(self.intro)
        elif arg.lower() == "sessions":
            self.session_manager.clear_sessions()
        else:
            print(f"{Colors.FAIL}[!] Error: Incorrect command{Colors.ENDC}")
            print("Usage: clear (clear screen) | clear sessions")

    def do_sessions(self, arg: str) -> None:
        """Gestiona las sesiones activas"""
        args = arg.split()
        command = args[0] if args else "list"

        if command == "list" or not command:
            self.session_manager.list_sessions()
        elif command == "kill" and len(args) > 1:
            if args[1].lower() == "all":
                self.session_manager.kill_all_sessions()
            else:
                self.session_manager.kill_session(args[1])
        elif command == "clear":
            self.session_manager.clear_sessions()
        elif command == "use" and len(args) > 1:
            self.session_manager.use_session(args[1])
        else:
            print(f"\n{Colors.CYAN}Sessions usage:{Colors.ENDC}")
            print(" sessions           - List all sessions")
            print(" sessions use <id>  - Connect to a specific session")
            print(" sessions kill <id> - Terminate a specific session")
            print(" sessions kill all  - Terminate all sessions")
            print(" sessions clear     - Manage sessions cleanup")

    def do_terminal(self, arg: str) -> None:
            """
            Opens a clean tmux terminal session.
            Usage: terminal
            """
            # Generate unique terminal name
            terminal_id = len(self.session_manager.sessions) + 1
            terminal_name = f"terminal_{terminal_id}"
            
            print(f"\n{Colors.CYAN}[*] Opening new terminal session...{Colors.ENDC}")
            
            # Create and initialize session
            session = self.session_manager.create_session(terminal_name, None)
            session.start_logging()
            
            try:
                print(f"\n{Colors.CYAN}[*] Starting terminal...{Colors.ENDC}")
                print(f"{Colors.CYAN}[*] Basic tmux commands:{Colors.ENDC}")
                print(f" • {Colors.BOLD}Ctrl+b d{Colors.ENDC}    - Return to framework")
                print(f" • {Colors.BOLD}Ctrl+b c{Colors.ENDC}    - Create new window")
                print(f" • {Colors.BOLD}Ctrl+b w{Colors.ENDC}    - List windows")
                print(f" • {Colors.BOLD}Ctrl+b %{Colors.ENDC}    - Split vertically")
                print(f" • {Colors.BOLD}Ctrl+b \"{Colors.ENDC}    - Split horizontally")
                
                # Basic shell command with environment setup
                cmd = f"cd {Path.home()} && TERM=xterm-256color exec $SHELL -l"
                
                success = TerminalManager.run_in_tmux(
                    cmd,
                    session.name,
                    "Terminal Session"
                )
                
                if success:
                    print(f"\n{Colors.GREEN}[✓] You have returned to the framework{Colors.ENDC}")
                    print(f"{Colors.CYAN}[*] To reconnect use: {Colors.BOLD}sessions use {session.session_id}{Colors.ENDC}")
                    session.add_to_history("Clean terminal session started")
                else:
                    print(f"{Colors.FAIL}[!] Error creating terminal session{Colors.ENDC}")
                    session.active = False
                    
            except Exception as e:
                print(f"{Colors.FAIL}[!] Error opening terminal: {e}{Colors.ENDC}")
                session.active = False
                session.log(f"Error: {str(e)}")
            finally:
                if not session.active:
                    session.stop_logging()
                    session.kill_terminal()
                    del self.session_manager.sessions[int(session.session_id)]

    def help_terminal(self):
        """Provides help information for the terminal command"""
        print(f'''
{Colors.PRIMARY}╔════════════════════════════════════════════════════════════╗
║  {Colors.SECONDARY}Terminal Session{Colors.PRIMARY}                                          ║
╚════════════════════════════════════════════════════════════╝{Colors.ENDC}
              
{Colors.BOLD}USAGE:{Colors.ENDC}
  terminal

{Colors.BOLD}DESCRIPTION:{Colors.ENDC}
  Opens a clean terminal session in tmux that can be used for any system operations.
  The session will be managed by the framework and can be reconnected to using the
  sessions command.

{Colors.BOLD}FEATURES:{Colors.ENDC}
  • Full tmux functionality
  • Session persistence
  • Window and pane management
  • Session logging
  • Easy reconnection

{Colors.BOLD}COMMON COMMANDS:{Colors.ENDC}
  • Ctrl+b d          - Detach from session (return to framework)
  • Ctrl+b c          - Create new window
  • Ctrl+b w          - List windows
  • Ctrl+b %          - Split vertically
  • Ctrl+b "          - Split horizontally
  • Ctrl+b arrows     - Navigate between panes

{Colors.BOLD}FRAMEWORK COMMANDS:{Colors.ENDC}
  • sessions          - List all sessions including terminals
  • sessions use <id> - Reconnect to a specific terminal
  • help tmux         - Show detailed tmux help''')
        print(f"\n")


    def complete_kill(self, text, line, begidx, endidx):
        """Autocompletado para el comando kill"""
        words = line.split()
        if len(words) <= 2:
            options = ['session', 'all']
            if not text:
                return options
            return [opt for opt in options if opt.startswith(text)]
        elif len(words) == 3 and words[1] == "all":
            return ['sessions'] if not text or 'sessions'.startswith(text) else []
        return []

    def complete_clear(self, text, line, begidx, endidx):
        """Autocompletado para el comando clear"""
        if not text:
            return ['sessions']
        return ['sessions'] if 'sessions'.startswith(text) else []

    def complete_use(self, text, line, begidx, endidx):
        """Autocompletado para el comando use"""
        words = line.split()
        if len(words) <= 2:
            options = ['session'] + list(self.modules.keys())
            if not text:
                return options
            return [opt for opt in options if opt.startswith(text)]
        return []

    def complete_install(self, text, line, begidx, endidx):
        """Tab completion for install command"""
        # List of module names that aren't installed yet
        available_modules = [name for name, module in self.modules.items() 
                            if not module.installed]
        if not text:
            return available_modules
        return [mod for mod in available_modules 
                if mod.startswith(text.lower())]

    def complete_remove(self, text, line, begidx, endidx):
        """Tab completion for remove command"""
        # List of installed module names
        installed_modules = [name for name, module in self.modules.items() 
                            if module.installed]
        if not text:
            return installed_modules
        return [mod for mod in installed_modules 
                if mod.startswith(text.lower())]

    def complete_update(self, text, line, begidx, endidx):
        """Tab completion for update command"""
        # List of installed module names (can only update installed modules)
        installed_modules = [name for name, module in self.modules.items() 
                            if module.installed]
        if not text:
            return installed_modules
        return [mod for mod in installed_modules 
                if mod.startswith(text.lower())]

    def complete_download(self, text, line, begidx, endidx):
        """Tab completion for download command"""
        from .shop import ModuleShop
        repo_url = "https://github.com/CoreSecFrame/CoreSecFrame-Modules"
        shop = ModuleShop(repo_url, self)
        
        # Get all available remote modules that aren't downloaded
        remote_modules = [name for name, module in shop.modules.items() 
                        if not module.downloaded]
        
        if not text:
            return remote_modules
        return [mod for mod in remote_modules 
                if mod.startswith(text.lower())]

    def _show_tmux_help(self):
        """Muestra ayuda sobre el uso de tmux"""
        print(f"\n{Colors.CYAN}[*] Useful tmux commands:{Colors.ENDC}")
        print(" • Ctrl+b d          - Detach from current session (return to framework)")
        print(" • Ctrl+b c          - Create a new window")
        print(" • Ctrl+b n          - Go to next window") 
        print(" • Ctrl+b p          - Go to previous window")
        print(" • Ctrl+b [0-9]      - Go to window number [0-9]")
        print(" • Ctrl+b %          - Split window vertically")
        print(" • Ctrl+b \"          - Split window horizontally")
        print(" • Ctrl+b arrows     - Move between panes")
        print(f"\n{Colors.CYAN}[*] From the framework:{Colors.ENDC}")
        print(" • sessions          - View all sessions")
        print(" • sessions use <id> - Connect to a specific session")
        print(" • sessions kill <id>- Terminate a session")
        print(" • help tmux         - Show this help")
        print(f"\n{Colors.CYAN}[*] For more information:{Colors.ENDC}")
        print(" • https://tmuxcheatsheet.com/")
        print(f"\n")

    def do_help(self, arg: str) -> None:
        """Muestra ayuda sobre comandos: help [comando]"""
        
        def print_main_header():
            """Imprime el encabezado principal del framework"""
            print(f'''
{Colors.PRIMARY}╔════════════════════════════════════════════════════════════╗
║  {Colors.SECONDARY}CoreSecurityFramework{Colors.PRIMARY} - Help Panel                        ║
╚════════════════════════════════════════════════════════════╝{Colors.ENDC}''')

        def print_section_header(title: str):
            """Imprime el encabezado de una sección"""
            print(f'''
{Colors.PRIMARY}╭────────────────────────────────────────────────────────────╮
│  {Colors.SECONDARY}{title}{Colors.ENDC}{Colors.PRIMARY}                                   │                                       
╰────────────────────────────────────────────────────────────╯{Colors.ENDC}''')

        def print_command(cmd: str, desc: str):
            """Imprime un comando con su descripción"""
            print(f"  {Colors.HIGHLIGHT}{cmd:<15}{Colors.ENDC} {desc}")

        def print_option(opt: str, desc: str):
            """Imprime una opción con su descripción"""
            print(f"    {Colors.SECONDARY}{opt:<20}{Colors.ENDC} {Colors.TEXT}{desc}{Colors.ENDC}")

        def print_example(example: str):
            """Imprime un ejemplo de uso"""
            print(f"    {Colors.SUCCESS}▶{Colors.ENDC} {example}")

        def print_note(note: str):
            """Imprime una nota"""
            print(f"    {Colors.WARNING}•{Colors.ENDC} {note}")

        if arg:
            arg = arg.lower()
            if arg == "tmux":
                self._show_tmux_help()
                return

            # Buscar primero en módulos
            for name, module in self.modules.items():
                if module._get_name().lower() == arg:
                    try:
                        help_data = module.get_help()
                        print(f'''
{Colors.PRIMARY}╔════════════════════════════════════════════════════════════╗
║  {Colors.SECONDARY}{help_data["title"]}{Colors.PRIMARY}                     ║
╚════════════════════════════════════════════════════════════╝{Colors.ENDC}''')
                        
                        print(f"\n{Colors.BOLD}USO:{Colors.ENDC}")
                        print(f"  {help_data['usage']}")
                        
                        print(f"\n{Colors.BOLD}DESCRIPCIÓN:{Colors.ENDC}")
                        print(f"  {help_data['desc']}")
                        
                        if "modes" in help_data:
                            print_section_header("MODOS DE USO           ")
                            for mode, desc in help_data["modes"].items():
                                print_option(mode, desc)
                        
                        if "options" in help_data:
                            print_section_header("OPCIONES               ")
                            for opt, desc in help_data["options"].items():
                                print_option(opt, desc)
                        
                        if "examples" in help_data:
                            print_section_header("EJEMPLOS               ")
                            for example in help_data["examples"]:
                                print_example(example)
                        
                        if "notes" in help_data:
                            print_section_header("NOTAS                  ")
                            for note in help_data["notes"]:
                                print_note(note)
                        return
                    except Exception as e:
                        print(f"{Colors.ERROR}[!] Error al obtener la ayuda del módulo: {e}{Colors.ENDC}")
                        return

            # Comandos del framework
            command_help = {
                "install": {
                    "title": "Tool Installation              ",
                    "usage": "install <tool name>",
                    "desc": "Install a tool in the system.",
                    "examples": [
                        "install nmap",
                        "install john",
                    ]
                },
                # ... resto de comandos ...
            }

            if arg in command_help:
                help_data = command_help[arg]
                print(f'''
{Colors.PRIMARY}╔════════════════════════════════════════════════════════════╗
║  {Colors.SECONDARY}{help_data["title"]}{Colors.PRIMARY}                           ║
╚════════════════════════════════════════════════════════════╝{Colors.ENDC}''')
                
                print(f"\n{Colors.BOLD}Usage:{Colors.ENDC}")
                print(f"  {help_data['usage']}")
                
                print(f"\n{Colors.BOLD}Description:{Colors.ENDC}")
                print(f"  {help_data['desc']}")
                
                if "options" in help_data:
                    print_section_header("OPTIONS               ")
                    for opt, desc in help_data["options"].items():
                        print_option(opt, desc)
                
                if "examples" in help_data:
                    print_section_header("Examples               ")
                    for example in help_data["examples"]:
                        print_example(example)
            else:
                super().do_help(arg)
        
        else:
            # Menú principal de ayuda
            print_main_header()
            
            print_section_header("Tools Management       ")
            print_command("show category", "Show all categories")
            print_command("show <category>", "Show all tools in a specific category")
            print_command("search <tool name>", "Search for a tool by name or description")
            print_command("install <tool name>", "Install a specific tool")
            print_command("remove <tool name>", "Remove a specific tool")
            print_command("update <tool name>", "Update a specific tool")
            
            print_section_header("Download new modules   ")
            print_command("shop or show_remote", "Show available modules to download")
            print_command("show_remote category", "Show available categories")
            print_command("show_remote <category name>", "Show avaiable tools on a specified category")
            print_command("search_remote <name>", "Search for a tool by name or description")
            print_command("download <module>", "Download the specified module .eg <download anonip_module>")
            
            print_section_header("Tools Usage            ")
            print_command("use <tool name>", "Run a tool in interactive mode")
            print_command("sessions", "Manage active sessions")
            
            print_section_header("System                 ")
            print_command("terminal", "Open a clean tmux terminal session to manage the system")
            print_command("clear", "Clear the screen")
            print_command("exit", "Exit the framework")
            print_command("help", "Show this help panel")


            print(f'''
{Colors.PRIMARY}╭────────────────────────────────────────────────────────────╮
│  {Colors.TEXT}For more information about a specific command:{Colors.ENDC}{Colors.PRIMARY}            │
│  {Colors.SECONDARY}help <command>{Colors.PRIMARY}                                            │
│                                                            │      
│  {Colors.TEXT}To view tmux shortcuts:{Colors.ENDC}{Colors.PRIMARY}                                   │
│  {Colors.SECONDARY}help tmux{Colors.PRIMARY}                                                 │
╰────────────────────────────────────────────────────────────╯{Colors.ENDC}''')
            print("\n")


    def _calculate_description_width(self, tools: List[ToolModule]) -> int:
        """
        Calcula el ancho óptimo para la columna de descripción
        
        Args:
            tools: Lista de herramientas
            
        Returns:
            int: Ancho óptimo para la columna de descripción
        """
        # Obtener la longitud de la descripción más larga
        max_desc_length = max(len(tool.description) for tool in tools)
        
        # Definir límites
        MIN_WIDTH = 33  # Ancho mínimo
        MAX_WIDTH = 60  # Ancho máximo
        
        # Calcular ancho óptimo
        optimal_width = min(max(max_desc_length, MIN_WIDTH), MAX_WIDTH)
        
        return optimal_width

    def _create_table_border(self, desc_width: int, border_char: str) -> str:
        """
        Crea una línea de borde para la tabla
        
        Args:
            desc_width: Ancho de la columna de descripción
            border_char: Carácter para el borde (═, ╔, ╚, etc)
            
        Returns:
            str: Línea de borde formateada
        """
        return f"{Colors.CYAN}{border_char}══════════════════{border_char}═══════════════{border_char}{'═' * desc_width}═{border_char}════════════════════{border_char}"

    def _create_separator_line(self, desc_width: int) -> str:
        """
        Crea una línea separadora entre herramientas
        
        Args:
            desc_width: Ancho de la columna de descripción
            
        Returns:
            str: Línea separadora formateada
        """
        return f"{Colors.CYAN}╟──────────────────╫───────────────╫{'─' * desc_width}─╫────────────────────╢"

    def _display_tools_table(self, tools_to_show: List[ToolModule], page: int = 1, items_per_page: int = 5) -> None:
        """
        Muestra una tabla paginada de herramientas con descripción ajustable
        
        Args:
            tools_to_show: Lista de herramientas a mostrar
            page: Número de página actual
            items_per_page: Número de items por página
        """
        if not tools_to_show:
            print(f"{Colors.WARNING}[!] No tools were found{Colors.ENDC}")
            return
            
        # Calcular ancho de descripción y paginación
        desc_width = self._calculate_description_width(tools_to_show)
        total_items = len(tools_to_show)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        
        if page > total_pages:
            page = total_pages
        
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        
        # Crear encabezado dinámico
        top_border = self._create_table_border(desc_width, "╔")
        header_text = f"{Colors.CYAN}║ {Colors.ACCENT}Name{Colors.ENDC}             {Colors.CYAN}║ {Colors.ACCENT}Status{Colors.ENDC}        {Colors.CYAN}║ {Colors.ACCENT}Description{' ' * (desc_width - 11)}{Colors.ENDC}{Colors.CYAN}║ {Colors.ACCENT}Category{Colors.ENDC}           {Colors.CYAN}║"
        mid_border = self._create_table_border(desc_width, "╠")
        bottom_border = self._create_table_border(desc_width, "╚")
        separator = self._create_separator_line(desc_width)
        
        print(f"\n{top_border}")
        print(header_text)
        print(mid_border)
        
        # Mostrar herramientas
        tools_in_page = list(tools_to_show[start_idx:end_idx])
        for i, tool in enumerate(tools_in_page):
            # Preparar estado con color
            if tool.installed:
                status = f"{Colors.GREEN}Installed{Colors.ENDC}".ljust(22)
            else:
                status = f"{Colors.FAIL}Not installed{Colors.ENDC}".ljust(22)
                
            # Formatear descripción para ajustarse al ancho
            description = tool.description
            desc_lines = []
            while description:
                if len(description) <= desc_width:
                    desc_lines.append(description.ljust(desc_width))
                    break
                # Buscar el último espacio antes del límite
                split_point = description[:desc_width].rfind(' ')
                if split_point == -1:  # No hay espacios, cortar en el límite
                    split_point = desc_width
                desc_lines.append(description[:split_point].ljust(desc_width))
                description = description[split_point:].lstrip()
            
            # Si no hay líneas (descripción vacía), añadir una línea en blanco
            if not desc_lines:
                desc_lines = [' ' * desc_width]
                
            # Imprimir primera línea con toda la información
            name_trunc = tool.name[:16].ljust(16)
            cat_trunc = tool._get_category()[:20].ljust(17)
            print(f"{Colors.CYAN}║ {Colors.SECONDARY}{name_trunc}{Colors.ENDC} {Colors.CYAN}║ {status} {Colors.CYAN}║ {Colors.TEXT}{desc_lines[0]}{Colors.ENDC}{Colors.CYAN}║ {Colors.SECONDARY}{cat_trunc}{Colors.ENDC}  {Colors.CYAN}║")
            
            # Imprimir líneas adicionales de descripción si existen
            for line in desc_lines[1:]:
                print(f"║ {'':16} {Colors.CYAN}║ {'':13} {Colors.CYAN}║ {Colors.TEXT}{line}{Colors.ENDC}{Colors.CYAN}║ {'':17}  {Colors.CYAN}║")
                
            # Agregar separador si no es la última herramienta de la página
            if i < len(tools_in_page) - 1:
                print(separator)
        
        print(bottom_border)
        print(f"\n")
        
        # Mostrar información de paginación
        if total_pages > 1:
            print(f"\n{Colors.WARNING}Page {page}/{total_pages} ({total_items} tools){Colors.ENDC}")
            print(f"{Colors.SUBTLE}Use 'n' for next page, 'p' for previous, any other key to exit{Colors.ENDC}")
            
            key = input().lower()
            if key == 'n' and page < total_pages:
                self._display_tools_table(tools_to_show, page + 1, items_per_page)
            elif key == 'p' and page > 1:
                self._display_tools_table(tools_to_show, page - 1, items_per_page)

    def _display_categories_table(self, categories: List[str], page: int = 1, items_per_page: int = 10) -> None:
        """
        Muestra una tabla paginada de categorías
        
        Args:
            categories: Lista de categorías a mostrar
            page: Número de página actual
            items_per_page: Número de items por página
        """
        if not categories:
            print(f"{Colors.WARNING}[!] No categories were found{Colors.ENDC}")
            return
            
        total_items = len(categories)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        
        if page > total_pages:
            page = total_pages
        
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        
        # Crear tabla
        header = f'''
{Colors.CYAN}╔══════════════════════════════════╦═══════════════════════╗
║ {Colors.ACCENT}Category    {Colors.ENDC}                     {Colors.CYAN}║ {Colors.ACCENT}Tools       {Colors.ENDC}          {Colors.CYAN}║
{Colors.CYAN}╠══════════════════════════════════╬═══════════════════════╣'''
        print(header)

        for category in sorted(categories)[start_idx:end_idx]:
            # Contar herramientas en esta categoría
            tools_count = len([
                tool for tool in self.modules.values()
                if tool._get_category().lower() == category.lower()
            ])
            
            # Truncar el nombre de la categoría si es necesario
            cat_trunc = category[:30].ljust(30)
            count_str = str(tools_count).ljust(15)
            
            print(f"{Colors.CYAN}║ {Colors.SECONDARY}{cat_trunc}{Colors.ENDC}   {Colors.CYAN}║ {Colors.SUCCESS}{count_str}{Colors.ENDC}       {Colors.CYAN}║")

        footer = f"{Colors.CYAN}╚══════════════════════════════════╩═══════════════════════╝"
        print(footer)
        print(f"\n")

        
        if total_pages > 1:
            print(f"\n{Colors.CYAN}Page {page}/{total_pages} ({total_items} categories){Colors.ENDC}")
            print(f"{Colors.SUBTLE}Use 'n' for next page, 'p' for previous, any other key to exit{Colors.ENDC}")
            
            key = input().lower()
            if key == 'n' and page < total_pages:
                self._display_categories_table(categories, page + 1, items_per_page)
            elif key == 'p' and page > 1:
                self._display_categories_table(categories, page - 1, items_per_page)

    def _update_installation_status(self, tools: list) -> None:
        """
        Actualiza el estado de instalación de todas las herramientas
        
        Args:
            tools: Lista de herramientas a actualizar
        """
        for tool in tools:
            tool.check_installation()

    def do_show(self, arg: str) -> None:
        """
        Muestra categorías o herramientas de una categoría específica
        Uso: show category | show <nombre_categoria>
        """
        if not arg:
            print(f"{Colors.FAIL}[!] Error: Correct usage: show category | show <category name>{Colors.ENDC}")
            return
            
        args = arg.split()
        
        # Actualizar estado de instalación de todos los módulos
        self._update_installation_status(self.modules.values())
        TerminalManager.clear_screen()
        
        # Obtener todas las categorías disponibles
        all_categories = {tool._get_category().lower() for tool in self.modules.values()}
        
        # Si el argumento es "category", mostrar lista de categorías
        if args[0].lower() == 'category':
            if not all_categories:
                print(f"{Colors.WARNING}[!] No categories were found{Colors.ENDC}")
                return
                
            print(f"\n{Colors.SUCCESS}[*] Available categories:{Colors.ENDC}")
            self._display_categories_table(list(all_categories))
            return
        
        # Si no, buscar herramientas en la categoría especificada
        category = ' '.join(args).lower()
        if category not in all_categories:
            print(f"{Colors.FAIL}[!] Category not found: {category}{Colors.ENDC}")
            print(f"\n{Colors.CYAN}[*] Use 'show category' to view available categories{Colors.ENDC}")
            return
            
        # Filtrar herramientas por categoría
        tools_in_category = [
            tool for tool in self.modules.values()
            if tool._get_category().lower() == category
        ]
        
        print(f"\n{Colors.CYAN}[*] Tools in category '{category}':{Colors.ENDC}")
        self._display_tools_table(tools_in_category)

    def do_search(self, arg: str) -> None:
        """
        Busca herramientas por nombre o descripción
        Uso: search <término>
        """
        if not arg:
            print(f"{Colors.FAIL}[!] Error: Correct usage: search <term>{Colors.ENDC}")
            return
            
        # Actualizar estado de instalación de todos los módulos
        self._update_installation_status(self.modules.values())
        TerminalManager.clear_screen()
        
        search_term = arg.lower()
        
        # Buscar coincidencias
        matching_tools = [
            tool for tool in self.modules.values()
            if search_term in tool.name.lower() or search_term in tool.description.lower()
        ]
        
        if not matching_tools:
            print(f"{Colors.WARNING}[!] No Tools were found that match: {search_term}{Colors.ENDC}")
            return
            
        print(f"\n{Colors.SUCCESS}[*] Results for '{search_term}':{Colors.ENDC}")
        self._display_tools_table(matching_tools)

    def complete_show(self, text, line, begidx, endidx):
        """Autocompletado para el comando show"""
        words = line.split()
        if len(words) <= 2:
            categories = {'category'} | {
                tool._get_category().lower() 
                for tool in self.modules.values()
            }
            if not text:
                return list(categories)
            return [cat for cat in categories if cat.startswith(text.lower())]
        return []

    def complete_search(self, text, line, begidx, endidx):
        """Autocompletado para el comando search"""
        words = line.split()
        if len(words) <= 2:
            if not text:
                return ['tools']
            return ['tools'] if 'tools'.startswith(text) else []
        return []



    def do_shop(self, arg: str) -> None:
            """Opens the module shop"""
            from .shop import ModuleShop
            
            # Default repo or use provided
            repo_url = arg if arg else "https://github.com/CoreSecFrame/CoreSecFrame-Modules"
            
            # Create shop instance
            shop = ModuleShop(repo_url)
            
            # Show default view (all modules)
            shop.show_category()

    def do_show_remote(self, arg: str) -> None:
            """Show remote modules
            Usage: show_remote [category]"""
            from .shop import ModuleShop
            repo_url = "https://github.com/yourusername/yourrepo"  # Default repo
            shop = ModuleShop(repo_url, self)
            shop.show_category(arg if arg else None)

    def do_search_remote(self, arg: str) -> None:
        """Search remote modules
        Usage: search_remote <term>"""
        if not arg:
            print(f"{Colors.FAIL}[!] Error: Search term required{Colors.ENDC}")
            return

        from .shop import ModuleShop
        repo_url = "https://github.com/yourusername/yourrepo"  # Default repo
        shop = ModuleShop(repo_url, self)
        shop.search(arg)

    def do_download(self, arg: str) -> None:
        """Downloads a module from the shop
        Usage: download <module_name>"""
        if not arg:
            print(f"{Colors.FAIL}[!] Error: Module name required{Colors.ENDC}")
            return

        from .shop import ModuleShop
        repo_url = "https://github.com/CoreSecFrame/CoreSecFrame-Modules"  # Default repo
        shop = ModuleShop(repo_url, self)
        shop.download_module(arg)



    def do_status(self, arg: str) -> None:
        """
        Opens btop system monitor in a tmux session
        Usage: status
        """
        if not PackageManager.check_package_installed('btop'):
            print(f"\n{Colors.WARNING}[!] btop is not installed. Would you like to install it? (y/N){Colors.ENDC}")
            if input().lower() != 'y':
                return
            
            if not PackageManager.install_package('btop'):
                return

        # Generate unique session name
        session_id = len(self.session_manager.sessions) + 1
        session_name = f"status_{session_id}"
        
        print(f"\n{Colors.CYAN}[*] Opening btop system monitor...{Colors.ENDC}")
        
        # Create and initialize session
        session = self.session_manager.create_session(session_name, None)
        session.start_logging()
        
        try:
            print(f"\n{Colors.CYAN}[*] Starting btop...{Colors.ENDC}")
            print(f"{Colors.CYAN}[*] Press Q to quit btop{Colors.ENDC}")
            print(f"{Colors.CYAN}[*] Use {Colors.BOLD}Ctrl+b d{Colors.ENDC}{Colors.CYAN} to detach and return to framework{Colors.ENDC}")
            
            cmd = f"TERM=xterm-256color btop"
            
            success = TerminalManager.run_in_tmux(
                cmd,
                session.name,
                "System Monitor"
            )
            
            if success:
                print(f"\n{Colors.GREEN}[✓] You have returned to the framework{Colors.ENDC}")
                print(f"{Colors.CYAN}[*] To reconnect use: {Colors.BOLD}sessions use {session.session_id}{Colors.ENDC}")
                session.add_to_history("System monitor session started")
            else:
                print(f"{Colors.FAIL}[!] Error creating btop session{Colors.ENDC}")
                session.active = False
                
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error opening btop: {e}{Colors.ENDC}")
            session.active = False
            session.log(f"Error: {str(e)}")
        finally:
            if not session.active:
                session.stop_logging()
                session.kill_terminal()
                del self.session_manager.sessions[int(session.session_id)]

    def do_files(self, arg: str) -> None:
        """
        Opens fzf file finder in a tmux session
        Usage: files
        """
        if not PackageManager.check_package_installed('fzf'):
            print(f"\n{Colors.WARNING}[!] fzf is not installed. Would you like to install it? (y/N){Colors.ENDC}")
            if input().lower() != 'y':
                return
            
            if not PackageManager.install_package('fzf'):
                return

        # Generate unique session name
        session_id = len(self.session_manager.sessions) + 1
        session_name = f"files_{session_id}"
        
        print(f"\n{Colors.CYAN}[*] Opening file finder...{Colors.ENDC}")
        
        # Create and initialize session
        session = self.session_manager.create_session(session_name, None)
        session.start_logging()
        
        try:
            print(f"\n{Colors.CYAN}[*] Starting fzf...{Colors.ENDC}")
            print(f"{Colors.CYAN}[*] Basic fzf commands:{Colors.ENDC}")
            print(f" • {Colors.BOLD}Enter{Colors.ENDC}     - Select file")
            print(f" • {Colors.BOLD}Ctrl+c{Colors.ENDC}    - Exit fzf")
            print(f" • {Colors.BOLD}Ctrl+r{Colors.ENDC}    - Reload")
            print(f" • {Colors.BOLD}Ctrl+b d{Colors.ENDC}  - Return to framework")
            
            # Command to show hidden files and execute in current directory
            cmd = f"cd {Path.home()} && TERM=xterm-256color find . -type f 2>/dev/null | fzf --preview 'cat {{}}'"
            
            success = TerminalManager.run_in_tmux(
                cmd,
                session.name,
                "File Finder"
            )
            
            if success:
                print(f"\n{Colors.GREEN}[✓] You have returned to the framework{Colors.ENDC}")
                print(f"{Colors.CYAN}[*] To reconnect use: {Colors.BOLD}sessions use {session.session_id}{Colors.ENDC}")
                session.add_to_history("File finder session started")
            else:
                print(f"{Colors.FAIL}[!] Error creating fzf session{Colors.ENDC}")
                session.active = False
                
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error opening fzf: {e}{Colors.ENDC}")
            session.active = False
            session.log(f"Error: {str(e)}")
        finally:
            if not session.active:
                session.stop_logging()
                session.kill_terminal()
                del self.session_manager.sessions[int(session.session_id)]


    def help_status(self):
        """Provides help information for the status command"""
        print(f'''
{Colors.PRIMARY}╔════════════════════════════════════════════════════════════╗
║  {Colors.SECONDARY}System Monitor{Colors.PRIMARY}                                            ║
╚════════════════════════════════════════════════════════════╝{Colors.ENDC}
              
{Colors.BOLD}USAGE:{Colors.ENDC}
  status

{Colors.BOLD}DESCRIPTION:{Colors.ENDC}
  Opens btop system monitor in a tmux session. btop is a resource monitor that
  shows usage and stats for processor, memory, disks, network and processes.

{Colors.BOLD}FEATURES:{Colors.ENDC}
  • Real-time system monitoring
  • Process management
  • Resource usage graphs
  • Session persistence
  • Automatic installation if not present

{Colors.BOLD}CONTROLS:{Colors.ENDC}
  • Q            - Quit btop
  • Ctrl+b d     - Detach from session (return to framework)
  • M            - Show memory stats
  • P            - Show CPU stats
  • N            - Show network stats
  • Esc          - Go back/exit menus''')
        print(f"\n")

    def help_files(self):
        """Provides help information for the files command"""
        print(f'''
{Colors.PRIMARY}╔════════════════════════════════════════════════════════════╗
║  {Colors.SECONDARY}File Finder{Colors.PRIMARY}                                              ║
╚════════════════════════════════════════════════════════════╝{Colors.ENDC}
              
{Colors.BOLD}USAGE:{Colors.ENDC}
  files

{Colors.BOLD}DESCRIPTION:{Colors.ENDC}
  Opens fzf (fuzzy finder) in a tmux session. fzf is an interactive finder that
  makes it easy to search and navigate through files and directories.

{Colors.BOLD}FEATURES:{Colors.ENDC}
  • Fuzzy searching
  • File preview
  • Interactive navigation
  • Session persistence
  • Automatic installation if not present

{Colors.BOLD}CONTROLS:{Colors.ENDC}
  • Enter        - Select file
  • Ctrl+c       - Exit fzf
  • Ctrl+r       - Reload file list
  • Ctrl+b d     - Detach from session (return to framework)
  • ↑/↓          - Navigate through files
  • /            - Start search''')
        print(f"\n")