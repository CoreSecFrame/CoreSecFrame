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
from .base import ToolModule

class FrameworkInterface(cmd.Cmd):
    # Obtener nombre de usuario
    username = getpass.getuser()
    current_time = datetime.now().strftime("%H:%M:%S")

    intro = f'''{Colors.PRIMARY}
    ╔══════════════════════════════════════════════════════════════════════╗
    ║    {Colors.ACCENT}╭───────────────────────────────────────────────────────────╮{Colors.PRIMARY}     ║
    ║    {Colors.ACCENT}│{Colors.SECONDARY}              CoreSecurityFramework v1.0                   {Colors.ACCENT}│     {Colors.PRIMARY}║
    ║    {Colors.ACCENT}╰───────────────────────────────────────────────────────────╯{Colors.PRIMARY}     ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║                                                                      ║
    ║ {Colors.SUCCESS}●{Colors.PRIMARY} Sistema  {Colors.TEXT}Presiona {Colors.HIGHLIGHT}'help'{Colors.TEXT} o {Colors.HIGHLIGHT}'?'{Colors.TEXT} para ver comandos     {Colors.PRIMARY}              ║
    ║ {Colors.WARNING}●{Colors.PRIMARY} Tools    {Colors.TEXT}Escribe {Colors.HIGHLIGHT}'list'{Colors.TEXT} para ver herramientas        {Colors.PRIMARY}              ║
    ║ {Colors.ERROR}●{Colors.PRIMARY} Sessions {Colors.TEXT}Usa {Colors.HIGHLIGHT}'sessions'{Colors.TEXT} para gestionar sesiones    {Colors.PRIMARY}                ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    {Colors.WARNING}Started at {Colors.TEXT} {current_time}  |  Licensed under MIT{Colors.ENDC}
    {Colors.TEXT}CoreSecurityFramework v1.0 - Developed with {Colors.ACCENT} ♥ {Colors.PRIMARY}by {Colors.SECONDARY} pr0ff3{Colors.ENDC}
    '''

    prompt = f'{Colors.PRIMARY}╭─{Colors.SECONDARY}({Colors.HIGHLIGHT}{username}@CoreSec{Colors.SECONDARY}){Colors.PRIMARY}─{Colors.SUBTLE}[{Colors.TEXT}#{Colors.SUBTLE}]{Colors.PRIMARY}\n╰─{Colors.ACCENT}≫ {Colors.TEXT}'
    
    def __init__(self):

        super().__init__()
        self.modules = ToolModule.load_modules()
        self.session_manager = SessionManager()
        TerminalManager.check_tmux_installed()
        signal.signal(signal.SIGINT, self.handle_sigint)
        ToolModule.load_modules()

    def execute_pkg(self, tool_name: str, command_type: str) -> None:
        # Usar el primer módulo disponible para ejecutar el comando
        if self.modules:
            first_module = next(iter(self.modules.values()))
            first_module._execute_package_commands(tool_name, command_type)
        else:
            print("[!] Error: No hay módulos cargados")

    def handle_sigint(self, signum, frame):
        """Manejador personalizado para Ctrl+C"""
        print("\n\n[!] Usa 'exit' para salir del framework")
        return

    def default(self, line: str) -> None:
        """Manejador de comandos desconocidos"""
        print(f"{Colors.FAIL}[!] Comando desconocido: {line}{Colors.ENDC}")
        print(f"{Colors.CYAN}[*] Usa 'help' para ver los comandos disponibles{Colors.ENDC}")
        
    def emptyline(self) -> bool:
        """No hacer nada cuando se presiona Enter sin comando"""
        return False

    # Comandos del framework
    def do_exit(self, arg: str) -> bool:
        """Salir del framework"""
        if self.session_manager.sessions:
            print(f"\n{Colors.WARNING}[!] Hay sesiones activas. ¿Deseas salir? (s/N){Colors.ENDC}")
            if input().lower() != 's':
                return False

        print(f"\n{Colors.CYAN}[*] Should we fear hackers? Intention is at the heart of this discussion.{Colors.ENDC}")
        return True

    def do_list(self, arg: str) -> None:
        """
        Lista elementos del framework en formato de tabla.
        Uso: list [tools|sessions]
        """
        args = arg.split()
        if not args:
            print(f"{Colors.FAIL}[!] Error: Especifica qué quieres listar (tools|sessions){Colors.ENDC}")
            return

        if args[0].lower() == "tools":
            print(f"\n{Colors.CYAN}[*] Herramientas disponibles:{Colors.ENDC}")
            
            # Actualizar módulos
            self.modules = ToolModule.load_modules()
            
            # Crear tabla
            header = f'''
╔══════════════════╦═══════════════╦═══════════════════════════════════╦════════════════════════╗
║ {Colors.BOLD}Nombre{Colors.ENDC}           ║ {Colors.BOLD}Estado{Colors.ENDC}        ║ {Colors.BOLD}Descripción{Colors.ENDC}                       ║ {Colors.BOLD}Dependencias{Colors.ENDC}           ║
╠══════════════════╬═══════════════╬═══════════════════════════════════╬════════════════════════╣'''
            print(header)

            for name, module in self.modules.items():
                # Actualizar estado de instalación
                module.check_installation()
                
                # Preparar estado con color y padding específico
                if module.installed:
                    status = f"{Colors.GREEN}Instalado{Colors.ENDC}".ljust(22)  # 8 chars + color codes
                else:
                    status = f"{Colors.FAIL}No instalado{Colors.ENDC}".ljust(22)  # 11 chars + color codes
                
                # Preparar dependencias
                deps = ', '.join(module.dependencies) if module.dependencies else "Ninguna"
                
                # Truncar textos largos
                name_trunc = module.name[:16].ljust(16)
                desc_trunc = module.description[:33].ljust(33)
                deps_trunc = deps[:20].ljust(20)
                
                # Imprimir fila
                print(f"║ {name_trunc} ║ {status} ║ {desc_trunc} ║ {deps_trunc}   ║")

            # Pie de tabla
            footer = "╚══════════════════╩═══════════════╩═══════════════════════════════════╩════════════════════════╝"
            print(footer)
            
            # Mostrar información adicional de comando
            print(f"\n{Colors.SUBTLE}Para usar una herramienta: {Colors.HIGHLIGHT}use <nombre>{Colors.ENDC}")

        elif args[0].lower() == "sessions":
            print(f"\n{Colors.CYAN}[*] Sesiones activas:{Colors.ENDC}")
            
            # Llamar al manejador de sesiones modificado para usar este formato
            self.session_manager.list_sessions()
                        
            # Información adicional
            print(f"\n{Colors.SUBTLE}Para interactuar con una sesión: {Colors.HIGHLIGHT}session <id>{Colors.ENDC}")
            
        else:
            print(f"{Colors.FAIL}[!] Error: Opción no válida. Usa 'tools' o 'sessions'{Colors.ENDC}")

    def do_install(self, arg: str) -> None:
        """Instala una herramienta"""
        args = arg.split()
        if not args:
            print(f"{Colors.FAIL}[!] Error: Debes especificar una herramienta{Colors.ENDC}")
            return
        self.execute_pkg(args[0], 'install')

    def do_update(self, arg: str) -> None:
        """Actualiza una herramienta"""
        args = arg.split()
        if not args:
            print(f"{Colors.FAIL}[!] Error: Debes especificar una herramienta{Colors.ENDC}")
            return
        self.execute_pkg(args[0], 'update')

    def do_remove(self, arg: str) -> None:
        """Desinstala una herramienta"""
        args = arg.split()
        if not args:
            print(f"{Colors.FAIL}[!] Error: Debes especificar una herramienta{Colors.ENDC}")
            return
        self.execute_pkg(args[0], 'remove')


    def do_use(self, arg: str) -> None:
        """Ejecuta una herramienta o conecta a una sesión
        Uso: use <tool> | use session <id>"""
        args = arg.split()
        if not args:
            print(f"{Colors.FAIL}[!] Error: Comando incompleto{Colors.ENDC}")
            print("Uso: use <tool> | use session <id>")
            return

        if args[0].lower() == "session" and len(args) > 1:
            self.session_manager.use_session(args[1])
        else:
            self._use_tool(args[0])

    def _use_tool(self, tool_name: str) -> None:
        """Método auxiliar para ejecutar una herramienta"""
        module = self.modules.get(tool_name.lower())
        if not module:
            print(f"{Colors.FAIL}[!] Error: Herramienta '{tool_name}' no encontrada{Colors.ENDC}")
            return

        if not module.installed:
            print(f"{Colors.FAIL}[!] Error: La herramienta {tool_name} no está instalada{Colors.ENDC}")
            print(f"{Colors.CYAN}[*] Puedes instalarla con el comando: install {tool_name}{Colors.ENDC}")
            return

        # Mostramos la información inicial al usuario
        print(f"\n{Colors.CYAN}[*] Iniciando {module.name} en una nueva sesión tmux{Colors.ENDC}")
        print(f"\n{Colors.GREEN}Selecciona el modo de ejecución:{Colors.ENDC}")
        print(f"{Colors.GREEN}1:{Colors.ENDC} Modo Guiado")
        print(f"{Colors.GREEN}2:{Colors.ENDC} Modo Directo")
        print(f"{Colors.GREEN}0:{Colors.ENDC} Volver al menú principal")
        
        while True:
            try:
                mode = input(f"\n{Colors.BOLD}Selecciona modo (1/2/3): {Colors.ENDC}").strip()
                if mode in ('1', '2', '0'):
                    break
                print(f"{Colors.FAIL}[!] Opción no válida{Colors.ENDC}")
            except KeyboardInterrupt:
                print("\n")
                return

        if mode == "0":
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

    def do_kill(self, arg: str) -> None:
        """
        Termina sesiones.
        Uso: kill session <id> | kill all sessions
        """
        args = arg.split()
        if not args:
            print(f"{Colors.FAIL}[!] Error: Comando incompleto{Colors.ENDC}")
            print("Uso: kill session <id> | kill all sessions")
            return

        if args[0].lower() == "all" and len(args) > 1 and args[1].lower() == "sessions":
            self.session_manager.kill_all_sessions()
        elif args[0].lower() == "session" and len(args) > 1:
            session_id = args[1]
            self.session_manager.kill_session(session_id)
        else:
            print(f"{Colors.FAIL}[!] Error: Comando incorrecto{Colors.ENDC}")
            print("Uso: kill session <id> | kill all sessions")

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
            print(f"{Colors.FAIL}[!] Error: Comando incorrecto{Colors.ENDC}")
            print("Uso: clear (limpia pantalla) | clear sessions")

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

    def complete_list(self, text, line, begidx, endidx):
        """Autocompletado para el comando list"""
        options = ['tools', 'sessions']
        if not text:
            return options
        return [opt for opt in options if opt.startswith(text)]

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
        print(f"\n{Colors.CYAN}[*] Para más información:{Colors.ENDC}")
        print("  • https://tmuxcheatsheet.com/")
        print(f"\n")

    def do_help(self, arg: str) -> None:
        """Muestra ayuda sobre comandos: help [comando]"""
        
        def print_main_header():
            """Imprime el encabezado principal del framework"""
            print(f'''
{Colors.PRIMARY}╔════════════════════════════════════════════════════════════╗
║  {Colors.SECONDARY}CoreSecurityFramework{Colors.PRIMARY} - Panel de Ayuda                    ║
╚════════════════════════════════════════════════════════════╝{Colors.ENDC}''')

        def print_section_header(title: str):
            """Imprime el encabezado de una sección"""
            print(f'''
{Colors.PRIMARY}╭────────────────────────────────────────────────────────────╮
│  {Colors.BOLD}{title}{Colors.ENDC}{Colors.PRIMARY}                                   │                                       
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
                    "title": "Instalación de Herramientas    ",
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
                # ... resto de comandos ...
            }

            if arg in command_help:
                help_data = command_help[arg]
                print(f'''
{Colors.PRIMARY}╔════════════════════════════════════════════════════════════╗
║  {Colors.SECONDARY}{help_data["title"]}{Colors.PRIMARY}                           ║
╚════════════════════════════════════════════════════════════╝{Colors.ENDC}''')
                
                print(f"\n{Colors.BOLD}USO:{Colors.ENDC}")
                print(f"  {help_data['usage']}")
                
                print(f"\n{Colors.BOLD}DESCRIPCIÓN:{Colors.ENDC}")
                print(f"  {help_data['desc']}")
                
                if "options" in help_data:
                    print_section_header("OPCIONES               ")
                    for opt, desc in help_data["options"].items():
                        print_option(opt, desc)
                
                if "examples" in help_data:
                    print_section_header("EJEMPLOS               ")
                    for example in help_data["examples"]:
                        print_example(example)
            else:
                super().do_help(arg)
        
        else:
            # Menú principal de ayuda
            print_main_header()
            
            print_section_header("GESTIÓN DE HERRAMIENTAS")
            print_command("list", "Lista todas las herramientas disponibles")
            print_command("install", "Instala una herramienta específica")
            print_command("remove", "Desinstala una herramienta")
            print_command("update", "Actualiza herramientas o el sistema")
            
            print_section_header("USO DE HERRAMIENTAS    ")
            print_command("use", "Ejecuta una herramienta en modo interactivo")
            print_command("sessions", "Gestiona las sesiones activas")
            
            print_section_header("SISTEMA                ")
            print_command("clear", "Limpia la pantalla")
            print_command("exit", "Sale del framework")
            print_command("help", "Muestra este panel de ayuda")

            print(f'''
{Colors.PRIMARY}╭────────────────────────────────────────────────────────────╮
│  {Colors.TEXT}Para más información sobre un comando específico:{Colors.ENDC}{Colors.PRIMARY}         │
│  {Colors.SECONDARY}help <comando>{Colors.PRIMARY}                                            │
│                                                            │      
│  {Colors.TEXT}Para ver los atajos de tmux:{Colors.ENDC}{Colors.PRIMARY}                              │
│  {Colors.SECONDARY}help tmux{Colors.PRIMARY}                                                 │
╰────────────────────────────────────────────────────────────╯{Colors.ENDC}''')
