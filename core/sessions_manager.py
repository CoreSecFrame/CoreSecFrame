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
        print(f"{Colors.GREEN}[+] Nueva sesión creada: {self.session_count} ({module_name}){Colors.ENDC}")
        return session

    def check_sessions_initialized(self) -> bool:
        """Verifica y actualiza el estado de todas las sesiones
        
        Returns:
            bool: True si las sesiones están correctamente inicializadas
        """
        tmux_sessions, error = TerminalManager.list_tmux_sessions()
        
        if error and "No hay servidor tmux" in error:
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
        # Encabezado de la tabla
        print(f"\n╔{'═' * 14}╦{'═' * 20}╦{'═' * 15}╦{'═' * 14}╗")
        print(f"║ {'ID':12} ║ {'Herramienta':18} ║ {'Tipo':13} ║ {'Estado':12} ║")
        print(f"╠{'═' * 14}╬{'═' * 20}╬{'═' * 15}╬{'═' * 14}╣")

        if not self.sessions:
            print(f"║ {Colors.SUBTLE}No hay sesiones activas{Colors.ENDC}".ljust(68) + "              ║")
            print(f"╚{'═' * 14}╩{'═' * 20}╩{'═' * 15}╩{'═' * 14}╝")
            return

        for session_id, session in self.sessions.items():
            
            # Truncar valores largos
            id_str = str(session_id)[:12].ljust(12)
            # Usar module_name en lugar de host
            module_name = (session.module_name if hasattr(session, 'module_name') and session.module_name else "N/A")[:18].ljust(18)
            # Determinar el tipo (puede ser Guiado o Directo)
            tipo = (session.last_command if session.last_command else "N/A")[:13].ljust(13)
            # Estado basado en active
            status = ("ACTIVA" if session.active else "INACTIVA")[:12].ljust(12)
            
            # Colorear estado
            if session.active:
                status = f"{Colors.GREEN}{status}{Colors.ENDC}"
            else:
                status = f"{Colors.FAIL}{status}{Colors.ENDC}"

            print(f"║ {id_str} ║ {module_name} ║ {tipo} ║ {status} ║")

        # Pie de la tabla
        print(f"╚{'═' * 14}╩{'═' * 20}╩{'═' * 15}╩{'═' * 14}╝")

    def clear_sessions(self) -> None:
        """Limpia las sesiones inactivas"""
        self.check_sessions_initialized()
        
        if not self.inactive_sessions:
            print(f"\n{Colors.GREEN}[✓] No hay sesiones inactivas para limpiar{Colors.ENDC}")
            return

        # Eliminar las sesiones inactivas
        for session_id in self.inactive_sessions:
            if session_id in self.sessions:
                del self.sessions[session_id]
                print(f"{Colors.WARNING}[!] Eliminada sesión inactiva {session_id}{Colors.ENDC}")

        print(f"\n{Colors.GREEN}[✓] Se han eliminado {len(self.inactive_sessions)} sesiones inactivas{Colors.ENDC}")
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
                print(f"{Colors.GREEN}[✓] Sesión {sid} terminada{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}[!] Sesión no encontrada{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.FAIL}[!] ID de sesión inválido{Colors.ENDC}")

    def kill_all_sessions(self) -> None:
        """Mata todas las sesiones registradas"""
        if not self.sessions:
            print(f"\n{Colors.WARNING}[!] No hay sesiones para eliminar{Colors.ENDC}")
            return

        # Mostrar resumen de sesiones a eliminar
        active = sum(1 for session in self.sessions.values() if session.active)
        inactive = len(self.sessions) - active
        print(f"\n{Colors.WARNING}[!] Se eliminarán todas las sesiones:{Colors.ENDC}")
        print(f"  - Sesiones activas: {active}")
        print(f"  - Sesiones inactivas: {inactive}")
        print(f"  - Total: {len(self.sessions)}")

        # Pedir confirmación
        response = input(f"\n{Colors.WARNING}¿Está seguro de eliminar todas las sesiones? (s/N): {Colors.ENDC}").lower()
        if response != 's':
            print(f"\n{Colors.GREEN}[✓] Operación cancelada{Colors.ENDC}")
            return

        try:
            # Intentar matar cada sesión
            for session in list(self.sessions.values()):
                try:
                    session.stop_logging()
                    session.kill_terminal()
                except Exception:
                    pass  # Ignoramos errores individuales

            # Limpiar el diccionario de sesiones
            self.sessions.clear()
            self.session_count = 0
            print(f"\n{Colors.GREEN}[✓] Todas las sesiones han sido eliminadas{Colors.ENDC}")

        except Exception as e:
            print(f"\n{Colors.FAIL}[!] Error al eliminar las sesiones: {e}{Colors.ENDC}")

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
                    print(f"\n{Colors.CYAN}[*] Conectando a la sesión {sid} ({session.name}){Colors.ENDC}")
                    print(f"{Colors.CYAN}[*] Usa Ctrl+b d para volver al framework{Colors.ENDC}")
                    if session.attach_to_tmux():
                        print(f"\n{Colors.GREEN}[✓] Volviste al framework{Colors.ENDC}")
                    else:
                        print(f"{Colors.FAIL}[!] No se pudo conectar a la sesión{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}[!] La sesión no está activa{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}[!] Sesión no encontrada{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.FAIL}[!] ID de sesión inválido{Colors.ENDC}")