import subprocess
import sys
import platform
from typing import Optional, Tuple
from .colors import Colors


class TerminalManager:
    """Gestiona las operaciones relacionadas con terminales y tmux"""
    
    @staticmethod
    def check_tmux_installed() -> None:
        """Verifica que tmux esté instalado en el sistema"""
        try:
            subprocess.run(['tmux', '-V'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            print(f"{Colors.FAIL}[!] tmux no está instalado. Por favor, instálalo primero:{Colors.ENDC}")
            print(f"{Colors.CYAN}   - En Debian/Ubuntu: sudo apt install tmux{Colors.ENDC}")
            print(f"{Colors.CYAN}   - En Fedora: sudo dnf install tmux{Colors.ENDC}")
            print(f"{Colors.CYAN}   - En Arch: sudo pacman -S tmux{Colors.ENDC}")
            sys.exit(1)

    @staticmethod
    def run_in_tmux(cmd: str, session_name: str, title: str = None) -> bool:
        """Ejecuta un comando en una nueva sesión de tmux
        
        Args:
            cmd: Comando a ejecutar
            session_name: Nombre de la sesión
            title: Título opcional para la ventana
            
        Returns:
            bool: True si la operación fue exitosa
        """
        try:
            # Verificar si ya existe la sesión
            has_session = subprocess.run(
                ['tmux', 'has-session', '-t', session_name],
                capture_output=True
            ).returncode == 0

            if has_session:
                print(f"{Colors.WARNING}[!] Ya existe una sesión con ese nombre{Colors.ENDC}")
                return False

            # Crear nueva sesión
            create_cmd = [
                'tmux', 'new-session',
                '-d',  # Iniciar en modo detached
                '-s', session_name,  # Nombre de la sesión
            ]
            
            if title:
                create_cmd.extend(['-n', title])
            
            create_cmd.extend(['sh', '-c', cmd])
            
            subprocess.run(create_cmd, check=True)
            
            if title:
                subprocess.run([
                    'tmux', 'rename-window', 
                    '-t', f'{session_name}:0', 
                    title
                ], check=True)
            
            # Conectar a la sesión
            subprocess.run([
                'tmux', 'attach-session',
                '-t', session_name
            ], check=True)
            
            return True

        except Exception as e:
            print(f"{Colors.FAIL}[!] Error con tmux: {e}{Colors.ENDC}")
            return False

    @staticmethod
    def attach_to_tmux(session_name: str) -> bool:
        """Conecta a una sesión tmux existente
        
        Args:
            session_name: Nombre de la sesión
            
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            result = subprocess.run(
                ['tmux', 'has-session', '-t', session_name],
                capture_output=True
            )
            
            if result.returncode == 0:
                subprocess.run(['tmux', 'attach-session', '-t', session_name])
                return True
            else:
                print(f"{Colors.FAIL}[!] La sesión tmux no existe{Colors.ENDC}")
                return False
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error al conectar con la sesión tmux: {e}{Colors.ENDC}")
            return False

    @staticmethod
    def detach_from_tmux() -> bool:
        """Desconecta de la sesión tmux actual sin cerrarla
        
        Returns:
            bool: True si la desconexión fue exitosa
        """
        try:
            subprocess.run(['tmux', 'detach-client'])
            return True
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error al desconectar de tmux: {e}{Colors.ENDC}")
            return False

    @staticmethod
    def kill_tmux_session(session_name: str) -> bool:
        """Cierra una sesión tmux
        
        Args:
            session_name: Nombre de la sesión a cerrar
            
        Returns:
            bool: True si la operación fue exitosa
        """
        try:
            subprocess.run(
                ['tmux', 'kill-session', '-t', session_name], 
                check=True, 
                stderr=subprocess.PIPE
            )
            print(f"{Colors.GREEN}[✓] Sesión tmux cerrada: {session_name}{Colors.ENDC}")
            return True
        except subprocess.CalledProcessError as e:
            if b"session not found" in e.stderr:
                print(f"{Colors.WARNING}[!] La sesión tmux ya estaba cerrada{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}[!] Error al cerrar la sesión tmux: {e}{Colors.ENDC}")
            return False

    @staticmethod
    def list_tmux_sessions() -> Tuple[list, Optional[str]]:
        """Lista todas las sesiones tmux activas
        
        Returns:
            Tuple[list, Optional[str]]: Lista de sesiones y posible mensaje de error
        """
        try:
            result = subprocess.run(
                ['tmux', 'list-sessions'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return result.stdout.splitlines(), None
            elif "no server running" in result.stderr:
                return [], "No hay servidor tmux ejecutándose"
            else:
                return [], f"Error: {result.stderr}"
                
        except Exception as e:
            return [], f"Error al listar sesiones: {e}"

    @staticmethod
    def clear_screen() -> None:
        """Limpia la pantalla según el sistema operativo"""
        try:
            if platform.system() == 'Windows':
                subprocess.run('cls', shell=True)
            else:
                # Intenta primero con el comando clear
                result = subprocess.run('clear', shell=True)
                if result.returncode != 0:
                    # Si clear falla, usa secuencias de escape ANSI
                    print('\033[2J\033[H', end='')
        except Exception as e:
            print(f"\n{Colors.FAIL}[!] Error al limpiar la pantalla: {e}{Colors.ENDC}")