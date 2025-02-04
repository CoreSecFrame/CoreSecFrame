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
            print(f"{Colors.FAIL}[!] tmux is not installed. Please install it before continuing.{Colors.ENDC}")
            print(f"{Colors.CYAN}   - On Debian/Ubuntu: sudo apt install tmux{Colors.ENDC}")
            print(f"{Colors.CYAN}   - On Fedora: sudo dnf install tmux{Colors.ENDC}")
            print(f"{Colors.CYAN}   - On Arch: sudo pacman -S tmux{Colors.ENDC}")
            sys.exit(1)

    @staticmethod
    def run_in_tmux(cmd: str, session_name: str, window_name: str = None) -> bool:
        """
        Ejecuta un comando en una nueva sesión tmux
        
        Args:
            cmd: Comando a ejecutar
            session_name: Nombre de la sesión
            window_name: Nombre de la ventana (opcional)
        
        Returns:
            bool: True si la ejecución fue exitosa
        """
        try:
            # Crear nueva sesión con terminal interactiva
            subprocess.run([
                'tmux', 'new-session',
                '-d',  # Detached
                '-s', session_name,  # Nombre de sesión
                '-n', window_name or 'main',  # Nombre de ventana
                '-e', 'TERM=xterm-256color',  # Terminal type
                '-e', 'LANG=en_US.UTF-8',     # Locale setting
                cmd
            ], check=True)

            # Configurar la ventana para modo interactivo
            subprocess.run([
                'tmux', 'set-option', '-t', session_name,
                'status-right', f'#{session_name}'
            ], check=True)

            # Habilitar mouse y otras opciones útiles
            subprocess.run([
                'tmux', 'set-window-option', '-t', session_name,
                'mode-keys', 'vi'
            ], check=True)

            subprocess.run([
                'tmux', 'set-option', '-t', session_name,
                'mouse', 'on'
            ], check=True)

            # Atachar a la sesión
            subprocess.run(['tmux', 'attach', '-t', session_name], check=True)
            return True

        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}[!] Error running tmux command: {e}{Colors.ENDC}")
            return False
        except Exception as e:
            print(f"{Colors.FAIL}[!] Unexpected error: {e}{Colors.ENDC}")
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
                print(f"{Colors.FAIL}[!] The tmux session does not exist{Colors.ENDC}")
                return False
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error connecting to tmux session: {e}{Colors.ENDC}")
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
            print(f"{Colors.FAIL}[!] Error detaching from tmux: {e}{Colors.ENDC}")
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
            print(f"{Colors.GREEN}[✓] tmux session closed: {session_name}{Colors.ENDC}")
            return True
        except subprocess.CalledProcessError as e:
            if b"session not found" in e.stderr:
                print(f"{Colors.WARNING}[!] tmux session is already closed{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}[!] Error closing tmux session: {e}{Colors.ENDC}")
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
                return [], "There is no tmux server"
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
            print(f"\n{Colors.FAIL}[!] Error clearing screen: {e}{Colors.ENDC}")