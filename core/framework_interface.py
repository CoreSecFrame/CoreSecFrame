import cmd
import importlib
import pkgutil
import subprocess
from pathlib import Path
import shutil
from typing import Dict, Optional, List
import platform
from .terminal_management import TerminalManager
from .sessions_manager import SessionManager
from .colors import Colors
from core.base import ToolModule


class FrameworkInterface(cmd.Cmd):
    intro = f'''{Colors.PRIMARY}
    ╔══════════════════════════════════════════════════════════════════╗
    ║  {Colors.ACCENT}╭─────────────────────────────────────────────────────────╮{Colors.PRIMARY}     ║
    ║  {Colors.ACCENT}│{Colors.SECONDARY}                  H4CK3R T00LS FR4MEW0RK                 {Colors.ACCENT}│{Colors.PRIMARY}     ║
    ║  {Colors.ACCENT}╰─────────────────────────────────────────────────────────╯{Colors.PRIMARY}     ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║  {Colors.SUCCESS}●{Colors.PRIMARY} Sistema   {Colors.TEXT}Presiona {Colors.HIGHLIGHT}'help'{Colors.TEXT} o {Colors.HIGHLIGHT}'?'{Colors.TEXT} para ver comandos    {Colors.PRIMARY}         ║
    ║  {Colors.WARNING}●{Colors.PRIMARY} Tools     {Colors.TEXT}Escribe {Colors.HIGHLIGHT}'list'{Colors.TEXT} para ver herramientas       {Colors.PRIMARY}         ║
    ║  {Colors.ERROR}●{Colors.PRIMARY} Sessions  {Colors.TEXT}Usa {Colors.HIGHLIGHT}'sessions'{Colors.TEXT} para gestionar sesiones     {Colors.PRIMARY}         ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝

    {Colors.SUBTLE}Versión 1.0 - Developed with ♥ by pr0ff3{Colors.ENDC}
    '''

    prompt = f'{Colors.PRIMARY}╭─{Colors.SECONDARY}({Colors.HIGHLIGHT}M41N C0NS0L3{Colors.SECONDARY}){Colors.PRIMARY}─{Colors.SUBTLE}[{Colors.TEXT}#{Colors.SUBTLE}]{Colors.PRIMARY}\n╰─{Colors.ACCENT}≫ {Colors.TEXT}'

    def __init__(self):
        super().__init__()
        self.modules: Dict[str, ToolModule] = {}
        self.session_manager = SessionManager()
        TerminalManager.check_tmux_installed()
        self.load_modules()

    def load_modules(self) -> None:
        """Carga dinámicamente todos los módulos disponibles"""
        modules_dir = Path(__file__).parent.parent / 'modules'
        if not modules_dir.exists():
            print(f"{Colors.WARNING}[!] Directorio de módulos no encontrado en {modules_dir}{Colors.ENDC}")
            return

        for module_info in pkgutil.iter_modules([str(modules_dir)]):
            if module_info.name.startswith('_'):
                continue

            try:
                module = importlib.import_module(f'modules.{module_info.name}')
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                            issubclass(attr, ToolModule) and
                            attr != ToolModule):
                        tool = attr()
                        self.modules[tool.name.lower()] = tool
                        break
            except ImportError as e:
                print(f"{Colors.FAIL}[!] Error cargando módulo {module_info.name}: {e}{Colors.ENDC}")

    def get_package_manager(self) -> tuple:
        """
        Detecta el gestor de paquetes del sistema
        Returns:
            tuple: (package_manager, commands_dict)
        """
        if platform.system() == 'Linux':
            if os.path.exists('/usr/bin/apt'):
                return 'apt', {
                    'install': 'sudo apt-get install -y',
                    'update': 'sudo apt-get update && sudo apt-get upgrade -y',
                    'remove': 'sudo apt-get remove -y',
                    'autoremove': 'sudo apt-get autoremove -y',
                    'show_cmd': 'apt show'
                }
            elif os.path.exists('/usr/bin/yum'):
                return 'yum', {
                    'install': 'sudo yum install -y',
                    'update': 'sudo yum update -y',
                    'remove': 'sudo yum remove -y',
                    'autoremove': 'sudo yum autoremove -y',
                    'show_cmd': 'yum info'
                }
            elif os.path.exists('/usr/bin/pacman'):
                return 'pacman', {
                    'install': 'sudo pacman -S --noconfirm',
                    'update': 'sudo pacman -Syu --noconfirm',
                    'remove': 'sudo pacman -R --noconfirm',
                    'autoremove': 'sudo pacman -Rns --noconfirm',
                    'show_cmd': 'pacman -Si'
                }
        return None, None

    def _run_command(self, cmd: str) -> bool:
        """Ejecuta un comando y retorna si fue exitoso"""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error ejecutando {cmd}")
            print(f"Salida de error: {e.stderr}")
            return False

    def _execute_package_commands(self, tool_name: str, command_type: str) -> None:
        """Ejecuta comandos de gestión de paquetes"""
        module = self.modules.get(tool_name.lower())
        if not module:
            print(f"{Colors.FAIL}[!] Error: Herramienta '{tool_name}' no encontrada{Colors.ENDC}")
            return

        pkg_manager = self.get_package_manager()[0]
        
        command_getters = {
            'install': module.get_package_install,
            'update': module.get_package_update,
            'remove': module.get_package_remove
        }
        
        getter = command_getters.get(command_type)
        if not getter:
            print(f"{Colors.FAIL}[!] Tipo de comando no válido: {command_type}{Colors.ENDC}")
            return
            
        package_commands = getter()
        
        if pkg_manager not in package_commands:
            print(f"{Colors.FAIL}[!] Gestor de paquetes '{pkg_manager}' no soportado para {tool_name}{Colors.ENDC}")
            print(f"{Colors.CYAN}Gestores soportados: {', '.join(package_commands.keys())}{Colors.ENDC}")
            return

        # Ejecutar comandos secuencialmente
        all_commands_successful = True
        for cmd in package_commands[pkg_manager]:
            if not self._run_command(cmd):
                print(f"{Colors.FAIL}[!] Operación {command_type} interrumpida{Colors.ENDC}")
                all_commands_successful = False
                break
        
        # Verificar el estado después de la operación
        if all_commands_successful and hasattr(module, 'check_installation'):
            module._installed = None  # Resetear el estado
            is_installed = module.check_installation()
            
            if command_type == 'install':
                if is_installed:
                    print(f"{Colors.OKGREEN}[+] {tool_name} ha sido instalado correctamente{Colors.ENDC}")
                else:
                    print(f"{Colors.WARNING}[!] {tool_name} no parece estar instalado correctamente{Colors.ENDC}")
            elif command_type == 'remove':
                if not is_installed:
                    print(f"{Colors.OKGREEN}[+] {tool_name} ha sido desinstalado correctamente{Colors.ENDC}")
                else:
                    print(f"{Colors.WARNING}[!] {tool_name} parece que aún está instalado{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}[!] No se pudo verificar el estado de la operación{Colors.ENDC}")

    # Comandos del framework
    def do_exit(self, arg: str) -> bool:
        """Salir del framework"""
        if self.session_manager.sessions:
            print(f"\n{Colors.WARNING}[!] Hay sesiones activas. ¿Deseas salir? (s/N){Colors.ENDC}")
            if input().lower() != 's':
                return False

        print(f"\n{Colors.CYAN}[*] Should we fear hackers? Intention is at the heart of this discussion.{Colors.ENDC}")
        return True

    def do_clear(self, arg: str) -> None:
        """Limpia la pantalla"""
        TerminalManager.clear_screen()
        print(self.intro)

    def do_list(self, arg: str) -> None:
        """Lista todas las herramientas disponibles y su estado"""
        print(f"\n{Colors.CYAN}[*] Herramientas disponibles:{Colors.ENDC}")
        for name, module in self.modules.items():
            status = f"{Colors.GREEN}[✓] Instalado{Colors.ENDC}" if module.installed else f"{Colors.FAIL}[✗] No instalado{Colors.ENDC}"
            print(f"\n{Colors.BOLD}{module.name}:{Colors.ENDC}")
            print(f"  Estado: {status}")
            print(f"  Descripción: {module.description}")
            print(f"  Comando: {module.command}")
            if module.dependencies:
                print(f"  Dependencias: {', '.join(module.dependencies)}")

    def do_install(self, arg: str) -> None:
        """Instala una herramienta"""
        args = arg.split()
        if not args:
            print(f"{Colors.FAIL}[!] Error: Debes especificar una herramienta{Colors.ENDC}")
            return
        self._execute_package_commands(args[0], 'install')

    def do_update(self, arg: str) -> None:
        """Actualiza una herramienta"""
        args = arg.split()
        if not args:
            print(f"{Colors.FAIL}[!] Error: Debes especificar una herramienta{Colors.ENDC}")
            return
        self._execute_package_commands(args[0], 'update')

    def do_remove(self, arg: str) -> None:
        """Desinstala una herramienta"""
        args = arg.split()
        if not args:
            print(f"{Colors.FAIL}[!] Error: Debes especificar una herramienta{Colors.ENDC}")
            return
        self._execute_package_commands(args[0], 'remove')

    def do_use(self, arg: str) -> None:
        """Ejecuta una herramienta específica"""
        if not arg:
            print(f"{Colors.FAIL}[!] Error: Debes especificar una herramienta{Colors.ENDC}")
            return

        module = self.modules.get(arg.lower())
        if not module:
            print(f"{Colors.FAIL}[!] Error: Herramienta '{arg}' no encontrada{Colors.ENDC}")
            return

        if not module.installed:
            print(f"{Colors.FAIL}[!] Error: La herramienta {arg} no está instalada{Colors.ENDC}")
            print(f"{Colors.CYAN}[*] Puedes instalarla con el comando: install {arg}{Colors.ENDC}")
            return

        # Mostramos la información inicial al usuario
        print(f"\n{Colors.CYAN}[*] Iniciando {module.name} en una nueva sesión tmux{Colors.ENDC}")
        print(f"\n{Colors.GREEN}Selecciona el modo de ejecución:{Colors.ENDC}")
        print(f"{Colors.GREEN}1:{Colors.ENDC} Modo Guiado")
        print(f"{Colors.GREEN}2:{Colors.ENDC} Modo Directo")
        print(f"{Colors.GREEN}3:{Colors.ENDC} Volver al menú principal")
        
        while True:
            try:
                mode = input(f"\n{Colors.BOLD}Selecciona modo (1/2/3): {Colors.ENDC}").strip()
                if mode in ('1', '2', '3'):
                    break
                print(f"{Colors.FAIL}[!] Opción no válida{Colors.ENDC}")
            except KeyboardInterrupt:
                print("\n")
                return

        if mode == "3":
            return

        # Crear y inicializar sesión
        session = self.session_manager.create_session(module.name, module)
        session.start_logging()

        try:
            framework_root = Path(__file__).parent.parent
            module_name = module.__class__.__module__.split('.')[-1]
            class_name = module.__class__.__name__
            
            python_cmd = (
                f"python3 -c \"import sys; "
                f"sys.path.append('{framework_root}'); "
                f"from modules.{module_name} import {class_name}; "
                f"tool = {class_name}(); "
                f"tool.{'run_guided' if mode == '1' else 'run_direct'}()\""
            )

            cmd = f"cd {framework_root} && {python_cmd}; exec bash -i"   

            print(f"\n{Colors.CYAN}[*] Iniciando sesión tmux...{Colors.ENDC}")
            print(f"{Colors.CYAN}[*] Recuerda:{Colors.ENDC}")
            print(f"  • Usa {Colors.BOLD}Ctrl+b d{Colors.ENDC} para volver al framework")
            print(f"  • Usa {Colors.BOLD}sessions use {session.session_id}{Colors.ENDC} para reconectar")
            
            success = TerminalManager.run_in_tmux(
                cmd, 
                session.name,
                f"{module.name} - {'Guiado' if mode == '1' else 'Directo'}"
            )
            
            if success:
                print(f"\n{Colors.GREEN}[✓] Has vuelto al framework{Colors.ENDC}")
                session.add_to_history(f"Sesión tmux: {'Guiado' if mode == '1' else 'Directo'}")
            else:
                print(f"{Colors.FAIL}[!] Error al crear sesión tmux{Colors.ENDC}")
                session.active = False
                            
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error al ejecutar la herramienta: {e}{Colors.ENDC}")
            session.active = False
            session.log(f"Error: {str(e)}")
            import traceback
            print(traceback.format_exc())
        finally:
            if not session.active:
                session.stop_logging()
                session.kill_terminal()
                del self.session_manager.sessions[int(session.session_id)]

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
            print(f"\n{Colors.CYAN}Uso de sessions:{Colors.ENDC}")
            print("  sessions           - Lista todas las sesiones")
            print("  sessions use <id>  - Conecta a una sesión específica")
            print("  sessions kill <id> - Termina una sesión específica")
            print("  sessions kill all  - Termina todas las sesiones")
            print("  sessions clear     - Gestiona la limpieza de sesiones")

    def complete_sessions(self, text, line, begidx, endidx):
        """Autocompletado para el comando sessions"""
        commands = ['list', 'kill', 'use', 'clear']
        if not text:
            return commands
        return [c for c in commands if c.startswith(text)]

    def _show_tmux_help(self):
        """Muestra ayuda sobre el uso de tmux"""
        print(f"\n{Colors.CYAN}[*] Comandos útiles de tmux:{Colors.ENDC}")
        print("  • Ctrl+b d          - Desconectar de la sesión actual (volver al framework)")
        print("  • Ctrl+b c          - Crear una nueva ventana")
        print("  • Ctrl+b n          - Ir a la siguiente ventana")
        print("  • Ctrl+b p          - Ir a la ventana anterior")
        print("  • Ctrl+b [0-9]      - Ir a la ventana número [0-9]")
        print("  • Ctrl+b %          - Dividir la ventana verticalmente")
        print("  • Ctrl+b \"          - Dividir la ventana horizontalmente")
        print("  • Ctrl+b flechas    - Moverse entre paneles")
        print(f"\n{Colors.CYAN}[*] Desde el framework:{Colors.ENDC}")
        print("  • sessions          - Ver todas las sesiones")
        print("  • sessions use <id> - Conectar a una sesión específica")
        print("  • sessions kill <id>- Terminar una sesión")
        print("  • help tmux         - Mostrar esta ayuda")

    def do_help(self, arg: str) -> None:
        """Muestra ayuda sobre comandos: help [comando]"""
        
        def print_header(text: str):
            """Imprime un encabezado con formato especial"""
            print(f"\n{Colors.CYAN}╭{'─' * (len(text) + 2)}╮{Colors.ENDC}")
            print(f"{Colors.CYAN}│ {Colors.BOLD}{text} {Colors.ENDC}{Colors.CYAN}│{Colors.ENDC}")
            print(f"{Colors.CYAN}╰{'─' * (len(text) + 2)}╯{Colors.ENDC}\n")

        def print_section(title: str):
            """Imprime un título de sección"""
            print(f"\n{Colors.GREEN}▓▒░ {title} ░▒▓{Colors.ENDC}")

        def print_command(cmd: str, desc: str):
            """Imprime un comando con su descripción"""
            print(f"  {Colors.BOLD}{cmd:<12}{Colors.ENDC} {desc}")

        def print_option(opt: str, desc: str):
            """Imprime una opción con su descripción"""
            print(f"  {Colors.CYAN}{opt:<15}{Colors.ENDC} {desc}")

        def print_example(example: str):
            """Imprime un ejemplo"""
            print(f"  {Colors.GREEN}▶{Colors.ENDC} {example}")

        if arg:
            arg = arg.lower()
            if arg == "tmux":
                self._show_tmux_help()
                return

            # Primero intentar obtener ayuda del módulo si existe
            try:
                # Buscar el módulo por nombre
                for name, module in self.modules.items():
                    if module._get_name().lower() == arg:
                        help_data = module.get_help()
                        print_header(help_data["title"])
                        print(f"{Colors.CYAN}Uso:{Colors.ENDC} {help_data['usage']}")
                        print(f"\n{help_data['desc']}")
                        
                        if "modes" in help_data:
                            print_section("Modos de Uso")
                            for mode, desc in help_data["modes"].items():
                                print_option(mode, desc)
                                
                        if "options" in help_data:
                            print_section("Opciones")
                            for opt, desc in help_data["options"].items():
                                print_option(opt, desc)
                        
                        if "examples" in help_data:
                            print_section("Ejemplos")
                            for example in help_data["examples"]:
                                print_example(example)
                                
                        if "notes" in help_data:
                            print_section("Notas")
                            for note in help_data["notes"]:
                                print(f"  • {note}")
                        return
                        
            except Exception as e:
                print(f"Error al obtener la ayuda del módulo: {e}")
  
            command_help = {
                "install": {
                    "title": "Instalación de Herramientas",
                    "usage": "install <nombre> [--show-cmd]",
                    "desc": "Instala una herramienta en el sistema.",
                    "options": {
                        "--show-cmd": "Muestra el comando que se ejecutaría sin realizarlo"
                    },
                    "examples": [
                        "install nmap",
                        "install john --show-cmd"
                    ]
                },
                "remove": {
                    "title": "Desinstalación de Herramientas",
                    "usage": "remove <nombre> [--show-cmd] [--no-autoremove]",
                    "desc": "Desinstala una herramienta del sistema.",
                    "options": {
                        "--show-cmd": "Muestra el comando que se ejecutaría sin realizarlo",
                        "--no-autoremove": "No ejecuta autoremove después de la desinstalación"
                    },
                    "examples": [
                        "remove nmap",
                        "remove john --show-cmd"
                    ]
                },
                "update": {
                    "title": "Actualización de Herramientas",
                    "usage": "update [nombre] [--show-cmd]",
                    "desc": "Actualiza una herramienta específica o todo el sistema.",
                    "options": {
                        "--show-cmd": "Muestra el comando que se ejecutaría sin realizarlo"
                    },
                    "examples": [
                        "update",
                        "update nmap",
                        "update nmap --show-cmd"
                    ]
                },
                "use": {
                    "title": "Uso de Herramientas",
                    "usage": "use <nombre>",
                    "desc": "Ejecuta una herramienta en modo guiado o directo.",
                    "examples": [
                        "use nmap",
                        "use john"
                    ]
                },
                "sessions": {
                    "title": "Gestión de Sesiones",
                    "usage": "sessions [list|use|kill|clear] [id]",
                    "desc": "Administra las sesiones activas del framework.",
                    "options": {
                        "list": "Lista todas las sesiones activas",
                        "use": "Conecta a una sesión específica",
                        "kill": "Termina una sesión específica",
                        "clear": "Limpia todas las sesiones inactivas"
                    },
                    "examples": [
                        "sessions",
                        "sessions use 1",
                        "sessions kill 2"
                    ]
                }
            }

            if arg in command_help:
                help_data = command_help[arg]
                print_header(help_data["title"])
                print(f"{Colors.CYAN}Uso:{Colors.ENDC} {help_data['usage']}")
                print(f"\n{help_data['desc']}")
                
                if "options" in help_data:
                    print_section("Opciones")
                    for opt, desc in help_data["options"].items():
                        print_option(opt, desc)
                
                if "examples" in help_data:
                    print_section("Ejemplos")
                    for example in help_data["examples"]:
                        print_example(example)
            else:
                super().do_help(arg)
        
        else:
            print_header("Panel de Ayuda del Framework")
            
            print_section("Gestión de Herramientas")
            print_command("list", "Lista todas las herramientas disponibles")
            print_command("install", "Instala una herramienta")
            print_command("remove", "Desinstala una herramienta")
            print_command("update", "Actualiza una herramienta o el sistema")
            
            print_section("Uso de Herramientas")
            print_command("use", "Ejecuta una herramienta")
            print_command("sessions", "Gestiona sesiones activas")
            
            print_section("Sistema")
            print_command("clear", "Limpia la pantalla")
            print_command("exit", "Sale del framework")
            print_command("help", "Muestra esta ayuda")
            
            print(f"\n{Colors.CYAN}▶{Colors.ENDC} Usa '{Colors.BOLD}help <comando>{Colors.ENDC}' para más información sobre un comando específico")
            print(f"{Colors.CYAN}▶{Colors.ENDC} Usa '{Colors.BOLD}help tmux{Colors.ENDC}' para ver los comandos de tmux")