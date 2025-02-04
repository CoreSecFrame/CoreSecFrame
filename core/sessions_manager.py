from datetime import datetime
from typing import Dict, List, Optional, Set
from .terminal_management import TerminalManager
from .logs_manager import LogManager
from .colors import Colors


class Session:
    """Representa una sesión individual del framework"""
    
    def __init__(self, session_id: str, module_name: str = None):
        self.session_id = session_id
        self.name = session_id
        self.module_name = module_name  # Añadimos el nombre del módulo
        self.start_time = datetime.now()
        self.active = True
        self.last_command = None
        self.history: List[dict] = []
        self.log_manager = LogManager(session_id, session_id)

    def attach_to_tmux(self) -> bool:
        """Conecta a la sesión tmux existente"""
        return TerminalManager.attach_to_tmux(self.name)

    def detach_from_tmux(self) -> bool:
        """Desconecta de la sesión tmux actual"""
        return TerminalManager.detach_from_tmux()

    def kill_terminal(self) -> bool:
        """Cierra la sesión de tmux asociada"""
        return TerminalManager.kill_tmux_session(self.name)

    def add_to_history(self, command: str, output: str = None) -> None:
        """Añade un comando al historial de la sesión"""
        entry = {
            'timestamp': datetime.now(),
            'command': command,
            'output': output
        }
        self.history.append(entry)
        self.last_command = command
        
        # También registrar en el log si está activo
        self.log_manager.log(f"Command: {command}")
        if output:
            self.log_manager.log(f"Output: {output}")

    def start_logging(self, filename: str = None) -> None:
        """Inicia el logging de la sesión"""
        self.log_manager.start_logging(filename)

    def stop_logging(self) -> None:
        """Detiene el logging de la sesión"""
        self.log_manager.stop_logging()

    def log(self, message: str) -> None:
        """Registra un mensaje en el log"""
        self.log_manager.log(message)

    def get_duration(self) -> str:
        """Retorna la duración de la sesión"""
        return self.log_manager.get_session_duration()


class SessionManager:
    """Gestiona todas las sesiones del framework"""
    
    def __init__(self):
        self.sessions: Dict[int, Session] = {}
        self.session_count = 0
        self.inactive_sessions: Set[int] = set()

    def create_session(self, name: str, tool=None) -> Session:
        """
        Crea una nueva sesión
        
        Args:
            name: Nombre de la sesión
            tool: Herramienta asociada (opcional)
            
        Returns:
            Session: Nueva sesión creada
        """
        self.check_sessions_initialized()
        self.session_count += 1
        
        # Obtener el nombre del módulo si tool está presente
        module_name = tool._get_name() if tool else name
        
        session = Session(str(self.session_count), module_name)
        self.sessions[self.session_count] = session
        print(f"{Colors.GREEN}[+] New session created: {self.session_count} ({module_name}){Colors.ENDC}")
        return session

    def check_sessions_initialized(self) -> bool:
        """Verifica y actualiza el estado de todas las sesiones
        
        Returns:
            bool: True si las sesiones están correctamente inicializadas
        """
        tmux_sessions, error = TerminalManager.list_tmux_sessions()
        
        if error and "There is no tmux server" in error:
            # Si no hay servidor tmux, marcar todas las sesiones como inactivas
            for session in self.sessions.values():
                session.active = False
                self.inactive_sessions.add(int(session.name))
            return True
            
        # Procesar las sesiones existentes
        tmux_sessions_dict = {}
        self.inactive_sessions.clear()
        
        if not error:
            for line in tmux_sessions:
                if ':' in line:
                    session_id = int(line.split(':')[0].strip())
                    tmux_sessions_dict[session_id] = True
            
            # Actualizar el estado de las sesiones existentes
            for session in self.sessions.values():
                if session.name.isdigit():
                    session_id = int(session.name)
                    if session_id not in tmux_sessions_dict:
                        session.active = False
                        self.inactive_sessions.add(session_id)
                    else:
                        session.active = True
            
            # Actualizar el contador al máximo ID encontrado
            if tmux_sessions_dict:
                self.session_count = max(tmux_sessions_dict.keys())
        
        return True

    def list_sessions(self):
        """
        Lista las sesiones activas en formato de tabla
        """
        self.check_sessions_initialized()

        if not self.sessions:
            print(f"{Colors.WARNING}[!] No active sessions{Colors.ENDC}")
            return

        # Encabezado de la tabla
        print(f"\n{Colors.CYAN}╔{'═' * 14}╦{'═' * 20}╦{'═' * 37}╦{'═' * 14}╗{Colors.ENDC}")
        print(f"{Colors.CYAN}║ {Colors.ACCENT}{'ID':12} {Colors.CYAN}║ {Colors.ACCENT}{'Tool':18} {Colors.CYAN}║ {Colors.ACCENT}{'Type':35} {Colors.CYAN}║ {Colors.ACCENT}{'Status':12} {Colors.CYAN}║{Colors.ENDC}")
        print(f"{Colors.CYAN}╠{'═' * 14}╬{'═' * 20}╬{'═' * 37}╬{'═' * 14}╣{Colors.ENDC}")

        for session_id, session in self.sessions.items():
            
            # Truncar valores largos
            id_str = str(session_id)[:12].ljust(12)
            # Usar module_name en lugar de host
            module_name = (session.module_name if hasattr(session, 'module_name') and session.module_name else "N/A")[:18].ljust(18)
            # Determinar el tipo (puede ser Guiado o Directo)
            tipo = (session.last_command if session.last_command else "N/A")[:35].ljust(35)
            # Estado basado en active
            status = ("ACTIVE" if session.active else "INACTIVE")[:12].ljust(12)
            
            # Colorear estado
            if session.active:
                status = f"{Colors.GREEN}{status}{Colors.ENDC}"
            else:
                status = f"{Colors.FAIL}{status}{Colors.ENDC}"

            print(f"{Colors.CYAN}║ {id_str} ║ {module_name} ║ {tipo} ║ {status} {Colors.CYAN}║{Colors.ENDC}")

        # Pie de la tabla
        print(f"{Colors.CYAN}╚{'═' * 14}╩{'═' * 20}╩{'═' * 37}╩{'═' * 14}╝")
        

    def clear_sessions(self) -> None:
        """Limpia las sesiones inactivas"""
        self.check_sessions_initialized()
        
        if not self.inactive_sessions:
            print(f"\n{Colors.GREEN}[✓] There are no inactive sessions to clear{Colors.ENDC}")
            return

        # Eliminar las sesiones inactivas
        for session_id in self.inactive_sessions:
            if session_id in self.sessions:
                del self.sessions[session_id]
                print(f"{Colors.WARNING}[!] Deleted inactive session {session_id}{Colors.ENDC}")

        print(f"\n{Colors.GREEN}[✓] {len(self.inactive_sessions)} inactive sessions deleted{Colors.ENDC}")
        self.inactive_sessions.clear()

    def kill_session(self, session_id: str) -> None:
        """Termina una sesión específica
        
        Args:
            session_id: ID de la sesión a terminar
        """
        try:
            sid = int(session_id)
            if sid in self.sessions:
                session = self.sessions[sid]
                session.active = False
                session.stop_logging()
                session.kill_terminal()
                del self.sessions[sid]
                print(f"{Colors.GREEN}[✓] Session {sid} terminated{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}[!] Session not found{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.FAIL}[!] Invalid session ID{Colors.ENDC}")

    def kill_all_sessions(self) -> None:
            """Kills all registered sessions"""
            if not self.sessions:
                print(f"\n{Colors.WARNING}[!] There are no sessions to kill{Colors.ENDC}")
                return

            # Show summary of sessions to kill
            active = sum(1 for session in self.sessions.values() if session.active)
            inactive = len(self.sessions) - active
            print(f"\n{Colors.WARNING}[!] All sessions will be killed:{Colors.ENDC}")
            print(f" - Active sessions: {active}")
            print(f" - Inactive sessions: {inactive}")
            print(f" - Total: {len(self.sessions)}")

            # Ask for confirmation
            response = input(f"\n{Colors.WARNING}Are you sure you want to kill all sessions? (y/N): {Colors.ENDC}").lower()
            if response != 'y':
                print(f"\n{Colors.GREEN}[✓] Operation cancelled{Colors.ENDC}")
                return

            try:
                # Try to kill each session
                for session in list(self.sessions.values()):
                    try:
                        # Verify if tmux session exists before trying to kill it
                        result = subprocess.run(
                            ['tmux', 'has-session', '-t', session.name],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        
                        if result.returncode == 0:  # Session exists
                            session.stop_logging()
                            session.kill_terminal()
                        else:
                            # Session doesn't exist, just cleanup the object
                            session.stop_logging()
                    except Exception:
                        continue  # Skip to next session if there's any error
                
                # Clear the sessions dictionary
                self.sessions.clear()
                self.session_count = 0
                print(f"\n{Colors.GREEN}[✓] All sessions killed{Colors.ENDC}")
                
            except Exception as e:
                print(f"\n{Colors.FAIL}[!] Error killing sessions: {e}{Colors.ENDC}")

    def use_session(self, session_id: str) -> None:
        """Conecta a una sesión específica
        
        Args:
            session_id: ID de la sesión a la que conectar
        """
        try:
            sid = int(session_id)
            if sid in self.sessions:
                session = self.sessions[sid]
                if session.active:
                    print(f"\n{Colors.CYAN}[*] Session {sid} ({session.name}) connected{Colors.ENDC}")
                    print(f"{Colors.CYAN}[*] Use Ctrl+b d to return to the framework{Colors.ENDC}")
                    if session.attach_to_tmux():
                        print(f"\n{Colors.GREEN}[✓] You have returned to the framework{Colors.ENDC}")
                    else:
                        print(f"{Colors.FAIL}[!] It was not possible to connect to the session{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}[!] Session is not active{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}[!] Session not found{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.FAIL}[!] Invalid session ID{Colors.ENDC}")