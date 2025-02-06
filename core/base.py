import sys
import os
import pkgutil
import importlib
import platform
from pathlib import Path
from abc import ABC, abstractmethod
import shutil
import subprocess
from typing import List, Optional, Dict, Tuple
from .terminal_management import TerminalManager
from .colors import Colors
from .ssh_manager import SSHManager, SSHCredentials 

# Añadir el directorio raíz al path si no está ya
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

class GetModule(ABC):
    def __init__(self):
        self.name: str = self._get_name()
        self.command: str = self._get_command()
        self.description: str = self._get_description()
        self.dependencies: List[str] = self._get_dependencies()
        self._installed: Optional[bool] = None
        self._ssh_manager: Optional[SSHManager] = None
        self.check_installation()
        
    @abstractmethod
    def _get_name(self) -> str:
        """Retorna el nombre de la herramienta"""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def _get_category(self) -> str:
        """Retorna la categoría de la herramienta"""
        raise NotImplementedError("Cada herramienta debe implementar su propia categoría")

    @abstractmethod
    def _get_command(self) -> str:
        """Retorna el comando principal de la herramienta"""
        pass

    @abstractmethod
    def _get_description(self) -> str:
        """Retorna la descripción de la herramienta"""
        pass

    @abstractmethod
    def _get_dependencies(self) -> List[str]:
        """Retorna lista de dependencias"""
        pass
    
    @abstractmethod
    def get_help(self) -> Dict:
        """Retorna la documentación de ayuda del módulo"""
        raise NotImplementedError("Cada herramienta debe implementar su propia ayuda")
    
    @abstractmethod
    def _get_update_command(self, pkg_manager: str) -> str:
        """Retorna comando de actualización para el gestor de paquetes"""
        return ''

    @abstractmethod
    def _get_install_command(self, pkg_manager: str) -> str:
        """Retorna comando de instalación para el gestor de paquetes"""
        return ''

    @abstractmethod
    def _get_uninstall_command(self, pkg_manager: str) -> str:
        """Retorna comando de desinstalación para el gestor de paquetes"""
        return ''

    @abstractmethod
    def _get_script_path(self) -> str:
        """Retorna la ruta al script específico de la herramienta"""
        pass
        
    @abstractmethod
    def run_guided(self) -> None:
        """Implementa el modo guiado de la herramienta"""
        pass
    @abstractmethod
    def run_direct(self) -> None:
        """Ejecuta la herramienta en modo directo"""
        try:
            subprocess.run(self.command, shell=True)
        except subprocess.SubprocessError as e:
            print(f"Error running {self.name}: {e}")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")

    def cleanup_tmux_session(self):
        """
        Cierra la sesión de tmux al finalizar el proceso.
        Este método está disponible para todos los módulos que hereden de GetModule.
        """
        try:
            # Verificar si hay una sesión de tmux activa
            result = subprocess.run(['tmux', 'list-sessions'], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                print("\nA tmux session has been detected.")
                close_session = input("¿Do you want to close the tmux session? (y/N): ").lower() == 'y'
                
                if close_session:
                    print("Closing tmux session...")
                    subprocess.run(['tmux', 'kill-session'], check=True)
                    print("Session closed successfully.")
                else:
                    print("Session will remain active.")
                    
        except subprocess.CalledProcessError as e:
            print(f"Error trying to manage tmux session: {e}")
        except Exception as e:
            print(f"Unexpected error managing tmux: {e}")

    def execute_with_cleanup(self, func, *args, **kwargs):
        """
        Wrapper para ejecutar cualquier función y asegurar la limpieza de tmux después.
        
        Args:
            func: La función a ejecutar
            *args: Argumentos posicionales para la función
            **kwargs: Argumentos con nombre para la función
        """
        try:
            # Ejecutar la función original
            return func(*args, **kwargs)
        finally:
            # Asegurar la limpieza de tmux
            self.cleanup_tmux_session()

    def run_script(self, cmd: list, show_output: bool = True) -> bool:
        """
        Ejecuta un script y maneja la limpieza de tmux.
        
        Args:
            cmd: Lista con el comando y sus argumentos
            show_output: Si se debe mostrar la salida en tiempo real
        
        Returns:
            bool: True si la ejecución fue exitosa, False en caso contrario
        """
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )

            if show_output:
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        print(output.strip())

            process.wait()

            if process.returncode != 0:
                stderr = process.stderr.read()
                if stderr:
                    print(f"Error: {stderr}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Error running script: {e}")
            return False
        finally:
            self.cleanup_tmux_session()


class ToolModule(GetModule):
    modules = {}  # Variable de clase compartida
    
    @classmethod
    def check_module_compatibility(cls) -> dict:
        """
        Verifica la compatibilidad de todos los módulos cargados.
        
        Returns:
            dict: Diccionario con el estado de compatibilidad de los módulos
            {
                'compatible': [lista de módulos compatibles],
                'incompatible': [lista de módulos incompatibles con sus razones]
            }
        """
        compatibility_status = {
            'Compatible': [],
            'Incompatible': []
        }
        
        modules_dir = Path(__file__).parent.parent / 'modules'
        
        if not modules_dir.exists():
            return compatibility_status
            
        for module_info in pkgutil.iter_modules([str(modules_dir)]):
            if module_info.name.startswith('_'):
                continue
                
            try:
                # Intentar importar el módulo
                module = importlib.import_module(f'modules.{module_info.name}')
                module_class = None
                
                # Buscar la clase que hereda de ToolModule
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, ToolModule) and
                        attr != ToolModule):
                        module_class = attr
                        break
                
                if not module_class:
                    compatibility_status['Incompatible'].append({
                        'name': module_info.name,
                        'reason': 'No class found that inherits from ToolModule'
                    })
                    continue
                    
                # Verificar métodos abstractos requeridos
                missing_methods = []
                required_methods = [
                    '_get_name',
                    '_get_category',
                    '_get_command',
                    '_get_description',
                    '_get_dependencies',
                    'get_help',
                    '_get_update_command',
                    '_get_install_command',
                    '_get_uninstall_command',
                    '_get_script_path',
                    'run_guided',
                    'run_direct'
                ]
                
                for method in required_methods:
                    if not hasattr(module_class, method) or \
                    not callable(getattr(module_class, method)):
                        missing_methods.append(method)
                
                if missing_methods:
                    compatibility_status['Incompatible'].append({
                        'name': module_info.name,
                        'reason': f'Missing the following required methods: {", ".join(missing_methods)}'
                    })
                    continue
                    
                # Verificar que los métodos devuelven los tipos correctos
                try:
                    instance = module_class()
                    
                    # Verificar tipos de retorno
                    if not isinstance(instance._get_name(), str):
                        raise TypeError('_get_name debe devolver str')
                    if not isinstance(instance._get_command(), str):
                        raise TypeError('_get_command debe devolver str')
                    if not isinstance(instance._get_description(), str):
                        raise TypeError('_get_description debe devolver str')
                    if not isinstance(instance._get_dependencies(), list):
                        raise TypeError('_get_dependencies debe devolver list')
                    if not isinstance(instance.get_help(), dict):
                        raise TypeError('get_help debe devolver dict')
                        
                    compatibility_status['Compatible'].append(module_info.name)
                    
                except Exception as e:
                    compatibility_status['Incompatible'].append({
                        'name': module_info.name,
                        'reason': f'Error instantiating or verifying types: {str(e)}'
                    })
                    
            except ImportError as e:
                compatibility_status['Incompatible'].append({
                    'name': module_info.name,
                    'reason': f'Error importing module: {str(e)}'
                })
            except Exception as e:
                compatibility_status['Incompatible'].append({
                    'name': module_info.name,
                    'reason': f'Unexpected error: {str(e)}'
                })
                
        return compatibility_status


    @classmethod
    def load_modules(cls, initial_load: bool = False) -> Dict[str, 'ToolModule']:
        """
        Loads all compatible modules dynamically
        
        Args:
            initial_load (bool): Indicates if this is the framework's initial load
            
        Returns:
            Dict[str, ToolModule]: Dictionary with loaded modules
        """
        cls.modules = {}  # Reset modules
        
        try:
            modules_dir = Path(__file__).parent.parent / 'modules'
            if not modules_dir.exists():
                if initial_load:
                    print(f"{Colors.WARNING}[!] Modules directory not found{Colors.ENDC}")
                return cls.modules

            # Ensure base __init__.py exists
            base_init = modules_dir / "__init__.py"
            if not base_init.exists():
                base_init.touch()

            def load_module_file(file_path: Path, import_path: str):
                """Helper function to load a single module file"""
                try:
                    if initial_load:
                        print(f"{Colors.SUBTLE}[*] Attempting to load: {import_path}{Colors.ENDC}")
                    
                    # Import the module
                    spec = importlib.util.spec_from_file_location(import_path, str(file_path))
                    if spec is None:
                        if initial_load:
                            print(f"{Colors.FAIL}[!] Could not create spec for {file_path}{Colors.ENDC}")
                        return
                        
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[import_path] = module
                    spec.loader.exec_module(module)
                    
                    # Find the class that inherits from ToolModule
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, ToolModule) and 
                            attr != ToolModule):
                            try:
                                tool = attr()
                                cls.modules[tool.name.lower()] = tool
                                if initial_load:
                                    print(f"{Colors.CYAN}[+] Loaded module: {tool.name} ({import_path}){Colors.ENDC}")
                                return True
                            except Exception as e:
                                if initial_load:
                                    print(f"{Colors.FAIL}[!] Error instantiating module {attr_name}: {e}{Colors.ENDC}")
                            break
                            
                except Exception as e:
                    if initial_load:
                        print(f"{Colors.FAIL}[!] Error loading module {import_path}: {e}{Colors.ENDC}")
                        import traceback
                        print(traceback.format_exc())
                return False

            # Load modules from base directory
            for file_path in modules_dir.glob("*.py"):
                if file_path.name != "__init__.py":
                    import_path = f"modules.{file_path.stem}"
                    load_module_file(file_path, import_path)

            # Load modules from category directories
            for category_dir in modules_dir.glob("*"):
                if category_dir.is_dir() and category_dir.name != "__pycache__":
                    # Ensure category __init__.py exists
                    category_init = category_dir / "__init__.py"
                    if not category_init.exists():
                        category_init.touch()
                    
                    for file_path in category_dir.glob("*.py"):
                        if file_path.name != "__init__.py":
                            import_path = f"modules.{category_dir.name}.{file_path.stem}"
                            load_module_file(file_path, import_path)

            if initial_load:
                if cls.modules:
                    print(f"\n{Colors.GREEN}[✓] Successfully loaded {len(cls.modules)} modules{Colors.ENDC}")
                else:
                    print(f"\n{Colors.WARNING}[!] No modules were loaded{Colors.ENDC}")
                    print(f"{Colors.CYAN}[*] You can use the 'shop' command to download new modules{Colors.ENDC}")
                    
        except Exception as e:
            if initial_load:
                print(f"{Colors.FAIL}[!] Error during module loading: {e}{Colors.ENDC}")
                import traceback
                print(traceback.format_exc())
                
        return cls.modules

    def check_installation(self) -> bool:
        """
        Verifies installation intelligently based on tool type.
        Installation detection is done automatically based on attributes and paths.
        """
        try:
            # 1. Verify dependencies first
            missing_deps = []
            for dep in self._get_dependencies():
                if not shutil.which(dep):
                    missing_deps.append(dep)
            
            if missing_deps:
                self._installed = False
                return False

            # 2. Determine tool type
            is_command_based = bool(self.command and self.command != self._get_name())
            is_script_based = bool(self._get_script_path())
            
            # 3. Command-based verification (installed binaries)
            if is_command_based:
                command_path = shutil.which(self.command)
                if command_path:
                    self._installed = True
                    return True
                    
            # 4. Script-based verification
            if is_script_based:
                script_path = Path(self._get_script_path())
                
                # Get category from class path
                module_category = self._get_category()
                scripts_base_dir = Path(__file__).parent.parent / "scripts"
                category_scripts_dir = scripts_base_dir / module_category
                
                # 4.1 Verify script existence
                if not script_path.exists():
                    self._installed = False
                    return False
                    
                # 4.2 Verify permissions
                if not os.access(script_path, os.X_OK):
                    try:
                        os.chmod(script_path, 0o755)
                    except Exception as e:
                        print(f"{Colors.WARNING}[!] Could not set permissions: {e}{Colors.ENDC}")
                        self._installed = False
                        return False
                
                # 4.3 Verify directory structure
                script_dir = script_path.parent
                if not script_dir.exists():
                    print(f"{Colors.WARNING}[!] Script directory not found: {script_dir}{Colors.ENDC}")
                    self._installed = False
                    return False
                    
                # 4.4 Look for common files based on script type
                if script_path.suffix == '.sh':
                    common_files = ['.git', 'README.md', 'config', 'install.sh']
                elif script_path.suffix == '.py':
                    common_files = ['requirements.txt', 'setup.py', '.git', 'README.md']
                else:
                    common_files = ['.git', 'README.md']
                
                found_files = [file for file in common_files if (script_dir / file).exists()]
                
                if found_files:
                    print(f"{Colors.CYAN}[*] Found additional files: {', '.join(found_files)}{Colors.ENDC}")
                
                # 4.5 For scripts, if all dependencies and script exist, consider it installed
                self._installed = True
                return True
                    
            # 5. If not command_based or script_based, check for tool-specific requirements
            if hasattr(self, '_verify_tool_specific_requirements'):
                return self._verify_tool_specific_requirements()
                    
            # 6. If no verification method available, assume not installed
            print(f"{Colors.WARNING}[!] Could not determine installation status{Colors.ENDC}")
            self._installed = False
            return False
                
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error checking installation: {e}{Colors.ENDC}")
            self._installed = False
            return False

    @property
    def installed(self) -> bool:
        """Propiedad que indica si la herramienta está instalada"""
        if self._installed is None:
            self.check_installation()
        return self._installed

    def get_status(self) -> Dict[str, any]:
        """Retorna el estado actual del módulo"""
        return {
            "name": self.name,
            "command": self.command,
            "description": self.description,
            "installed": self.installed,
            "dependencies": self.dependencies
        }

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
            print(f"Error executing {cmd}")
            print(f"Error output: {e.stderr}")
            return False

    def _execute_package_commands(self, tool_name: str, command_type: str) -> None:
        """Ejecuta comandos de gestión de paquetes"""
        module = ToolModule.modules.get(tool_name.lower())
        if not module:
            print(f"[!] Error: Tool '{tool_name}' not found")
            return

        # Verificar estado de instalación según el comando
        is_installed = module.check_installation()
        
        if command_type in ['update', 'remove'] and not is_installed:
            print(f"[!] Error: Tool '{tool_name}' is not installed")
            return
        elif command_type == 'install' and is_installed:
            print(f"[!] Tool '{tool_name}' is already installed")
            return

        pkg_manager = self.get_package_manager()[0]
        
        # Mapeo de comandos a métodos
        command_type_to_method = {
            'install': '_get_install_command',
            'update': '_get_update_command',
            'remove': '_get_uninstall_command'
        }
        
        method_name = command_type_to_method.get(command_type)
        if not method_name:
            print(f"[!] Invalid command type: {command_type}")
            return
            
        # Obtener el comando específico para este gestor de paquetes
        commands = getattr(module, method_name)(pkg_manager)
        if not commands:
            print(f"[!] There is no {command_type} command for {pkg_manager}")
            return
        
        # Convertir un único comando a lista
        if isinstance(commands, str):
            commands = [commands]
        
        # Ejecutar los comandos
        success = True
        for cmd in commands:
            print(f"\n[*] Executing: {cmd}")
            if not self._run_command(cmd):
                print(f"[!] Error running: {cmd}")
                success = False
                break
        
        if not success:
            print(f"[!] Operation {command_type} interrupted")
        else:
            # Verificar instalación después del comando
            if hasattr(module, 'check_installation'):
                module._installed = None  # Reset estado
                is_installed = module.check_installation()
                
                if command_type == 'install':
                    print(f"[+] {tool_name} {'installed' if is_installed else 'not installed'} successfully")
                elif command_type == 'remove':
                    print(f"[+] {tool_name} {'uninstalled' if not is_installed else 'not uninstalled'} successfully")

    def get_package_manager(self) -> tuple:
        """Detecta el gestor de paquetes del sistema"""
        if platform.system() == 'Linux':
            package_managers = {
                '/usr/bin/apt': ('apt', {
                    'install': 'sudo apt-get install -y',
                    'update': 'sudo apt-get update && sudo apt-get upgrade -y',
                    'remove': 'sudo apt-get remove -y',
                    'autoremove': 'sudo apt-get autoremove -y',
                    'show_cmd': 'apt show'
                }),
                '/usr/bin/yum': ('yum', {
                    'install': 'sudo yum install -y',
                    'update': 'sudo yum update -y',
                    'remove': 'sudo yum remove -y',
                    'autoremove': 'sudo yum autoremove -y',
                    'show_cmd': 'yum info'
                }),
                '/usr/bin/pacman': ('pacman', {
                    'install': 'sudo pacman -S --noconfirm',
                    'update': 'sudo pacman -Syu --noconfirm',
                    'remove': 'sudo pacman -R --noconfirm',
                    'autoremove': 'sudo pacman -Rns --noconfirm',
                    'show_cmd': 'pacman -Si'
                })
            }
            
            for path, manager_info in package_managers.items():
                if os.path.exists(path):
                    return manager_info
                    
        return None, None

    @property
    def ssh_manager(self) -> SSHManager:
        """Lazy initialization of SSH manager"""
        if self._ssh_manager is None:
            self._ssh_manager = SSHManager()
        return self._ssh_manager

    def connect_ssh(self, host: str, user: str, use_password: bool = False, key_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Establishes SSH connection with specified credentials
        
        Args:
            host: Remote host
            user: Remote user
            use_password: Whether to use password authentication
            key_path: Path to SSH key file (optional)
            
        Returns:
            Tuple[bool, Optional[str]]: (Success status, Error message if any)
        """
        credentials = SSHCredentials(
            host=host,
            user=user,
            use_password=use_password,
            key_path=key_path
        )
        return self.ssh_manager.connect(credentials)

    def execute_remote_command(self, command: str, use_sudo: bool = False) -> Tuple[int, str, str]:
        """
        Executes a command on the remote host
        
        Args:
            command: Command to execute
            use_sudo: Whether to execute with sudo
            
        Returns:
            Tuple[int, str, str]: (Exit status, stdout, stderr)
        """
        return self.ssh_manager.execute_command(command, use_sudo)

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Uploads a file to the remote host
        
        Args:
            local_path: Path to local file
            remote_path: Path where to store file on remote host
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.ssh_manager.upload_file(local_path, remote_path)

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Downloads a file from the remote host
        
        Args:
            remote_path: Path to remote file
            local_path: Path where to store file locally
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.ssh_manager.download_file(remote_path, local_path)

    def close_ssh(self):
        """Closes the SSH connection if active"""
        if self._ssh_manager:
            self._ssh_manager.close()
            self._ssh_manager = None


    def open_interactive_terminal(self, session_name: str = "framework-terminal") -> bool:
        """
        Opens a clean tmux terminal session for user interaction.
        
        Args:
            session_name: Name for the tmux session. Default is "framework-terminal"
            
        Returns:
            bool: True if terminal was opened successfully, False otherwise
        """
        try:
            # Check if tmux is installed
            if not shutil.which('tmux'):
                print(f"{Colors.FAIL}[!] Error: tmux is not installed{Colors.ENDC}")
                return False
                
            # Check if session already exists
            check_session = subprocess.run(
                ['tmux', 'has-session', '-t', session_name],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            
            if check_session.returncode == 0:
                print(f"{Colors.WARNING}[!] Session '{session_name}' already exists{Colors.ENDC}")
                attach = input("Do you want to attach to the existing session? (y/N): ").lower() == 'y'
                if attach:
                    subprocess.run(['tmux', 'attach-session', '-t', session_name])
                return True

            # Create new session
            print(f"{Colors.CYAN}[*] Creating new tmux session: {session_name}{Colors.ENDC}")
            
            # Start detached session with custom settings
            subprocess.run([
                'tmux', 'new-session',
                '-d',  # Start detached
                '-s', session_name,  # Session name
                '-n', 'main'  # Window name
            ])
            
            # Configure session
            subprocess.run([
                'tmux', 'set-option',
                '-t', session_name,
                'status-style', 'bg=black,fg=white'
            ])
            
            # Set window title
            subprocess.run([
                'tmux', 'rename-window',
                '-t', f'{session_name}:0',
                'Framework Terminal'
            ])
            
            # Add helpful message
            subprocess.run([
                'tmux', 'send-keys',
                '-t', session_name,
                f'echo "{Colors.CYAN}Welcome to Framework Terminal{Colors.ENDC}"\n'
            ])
            
            print(f"\n{Colors.CYAN}[*] Terminal session created successfully{Colors.ENDC}")
            print(f"{Colors.CYAN}[*] Commands to manage the session:{Colors.ENDC}")
            print("    - Exit session: Ctrl+B then D (detach)")
            print("    - Reattach: tmux attach -t", session_name)
            print("    - Kill session: tmux kill-session -t", session_name)
            
            # Attach to session
            subprocess.run(['tmux', 'attach-session', '-t', session_name])
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}[!] Error creating tmux session: {e}{Colors.ENDC}")
            return False
        except Exception as e:
            print(f"{Colors.FAIL}[!] Unexpected error: {e}{Colors.ENDC}")
            return False
        finally:
            # No cleanup here - we want the session to persist until user closes it
            pass


class PackageManager:
    @staticmethod
    def check_package_installed(package_name: str) -> bool:
        """
        Check if a package is installed using 'which' command
        
        Args:
            package_name: Name of the package to check
            
        Returns:
            bool: True if package is installed, False otherwise
        """
        try:
            result = subprocess.run(['which', package_name], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def install_package(package_name: str) -> bool:
        """
        Install a package using apt
        
        Args:
            package_name: Name of the package to install
            
        Returns:
            bool: True if installation was successful, False otherwise
        """
        try:
            print(f"\n{Colors.CYAN}[*] Installing {package_name}...{Colors.ENDC}")
            result = subprocess.run(['sudo', 'apt', 'install', '-y', package_name], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{Colors.SUCCESS}[✓] Installation successful{Colors.ENDC}")
                return True
            else:
                print(f"{Colors.FAIL}[!] Installation failed: {result.stderr}{Colors.ENDC}")
                return False
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error during installation: {str(e)}{Colors.ENDC}")
            return False

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