import sys
import os
import pkgutil
import importlib
import platform
from pathlib import Path
from abc import ABC, abstractmethod
import shutil
import subprocess
from typing import List, Optional, Dict

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
        self.check_installation()
        
    @abstractmethod
    def _get_name(self) -> str:
        """Retorna el nombre de la herramienta"""
        raise NotImplementedError("Subclasses must implement this method")

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
            print(f"Error ejecutando {self.name}: {e}")
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario")

    def cleanup_tmux_session(self):
        """
        Cierra la sesión de tmux al finalizar el proceso.
        Este método está disponible para todos los módulos que hereden de GetModule.
        """
        try:
            # Verificar si hay una sesión de tmux activa
            result = subprocess.run(['tmux', 'list-sessions'], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                print("\nSe ha detectado una sesión de tmux activa.")
                close_session = input("¿Desea cerrar la sesión de tmux? (s/N): ").lower() == 's'
                
                if close_session:
                    print("Cerrando sesión de tmux...")
                    subprocess.run(['tmux', 'kill-session'], check=True)
                    print("Sesión de tmux cerrada correctamente.")
                else:
                    print("La sesión de tmux permanecerá activa.")
                    
        except subprocess.CalledProcessError as e:
            print(f"Error al intentar gestionar la sesión de tmux: {e}")
        except Exception as e:
            print(f"Error inesperado al gestionar tmux: {e}")

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
            print(f"Error al ejecutar el script: {e}")
            return False
        finally:
            self.cleanup_tmux_session()


class ToolModule(GetModule):
    modules = {}  # Variable de clase compartida
    
    @classmethod
    def load_modules(cls) -> Dict[str, 'ToolModule']:
        """
        Carga dinámicamente todos los módulos disponibles
        Returns:
            Dict[str, ToolModule]: Diccionario con los módulos cargados
        """
        cls.modules = {}  # Reset modules
        modules_dir = Path(__file__).parent.parent / 'modules'
        
        if not modules_dir.exists():
            print(f"[!] Directorio de módulos no encontrado en {modules_dir}")
            return cls.modules
            
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
                        cls.modules[tool.name.lower()] = tool  # Usar cls.modules
                        break
            except ImportError as e:
                print(f"[!] Error cargando módulo {module_info.name}: {e}")
                
        return cls.modules

    def check_installation(self) -> bool:
        """
        Verifica la instalación de forma inteligente basándose en el tipo de herramienta.
        La detección del tipo se hace automáticamente según los atributos y rutas proporcionados.
        """
        try:
            # 1. Verificar dependencias primero
            missing_deps = []
            for dep in self._get_dependencies():
                if not shutil.which(dep):
                    missing_deps.append(dep)
            
            if missing_deps:
                return False

            # 2. Determinar el tipo de herramienta
            is_command_based = bool(self.command and self.command != self._get_name())
            is_script_based = bool(self._get_script_path())
            
            # 3. Verificación basada en comando (binarios instalados)
            if is_command_based:
                command_path = shutil.which(self.command)
                if command_path:
                    self._installed = True
                    return True
                    
            # 4. Verificación basada en script
            if is_script_based:
                script_path = Path(self._get_script_path())
                
                # 4.1 Verificar existencia del script
                if not script_path.exists():
                    return False
                    
                # 4.2 Verificar permisos
                if not os.access(script_path, os.X_OK):
                    try:
                        os.chmod(script_path, 0o755)
                        print(f"[*] Permisos de ejecución agregados a: {script_path}")
                    except Exception as e:
                        print(f"[!] No se pudieron establecer permisos de ejecución: {e}")
                        return False
                
                # 4.3 Verificar estructura de directorios
                script_dir = script_path.parent
                if not script_dir.exists():
                    print(f"[!] Directorio de scripts no encontrado: {script_dir}")
                    return False
                    
                # 4.4 Buscar archivos comunes según el tipo de script
                if script_path.suffix == '.sh':
                    # Scripts bash suelen tener estos archivos
                    common_files = ['.git', 'README.md', 'config', 'install.sh']
                elif script_path.suffix == '.py':
                    # Scripts Python suelen tener estos archivos
                    common_files = ['requirements.txt', 'setup.py', '.git', 'README.md']
                else:
                    common_files = ['.git', 'README.md']
                
                found_files = []
                for file in common_files:
                    file_path = script_dir / file
                    if file_path.exists():
                        found_files.append(file)
                
                if found_files:
                    print(f"[*] Archivos adicionales encontrados: {', '.join(found_files)}")
                
                # 4.5 Para scripts, si tiene todas las dependencias y el script existe, consideramos que está instalado
                self._installed = True
                return True
                
            # 5. Si no es ni command_based ni script_based, verificar si el módulo define verificación específica
            if hasattr(self, '_verify_tool_specific_requirements'):
                return self._verify_tool_specific_requirements()
                
            # 6. Si llegamos aquí y no hay forma de verificar, asumimos que no está instalado
            print("[!] No se pudo determinar el estado de instalación")
            return False
            
        except Exception as e:
            print(f"[!] Error durante la verificación de instalación: {e}")
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
            print(f"Error ejecutando {cmd}")
            print(f"Salida de error: {e.stderr}")
            return False

    def _execute_package_commands(self, tool_name: str, command_type: str) -> None:
        """Ejecuta comandos de gestión de paquetes"""
        module = ToolModule.modules.get(tool_name.lower())
        if not module:
            print(f"[!] Error: Herramienta '{tool_name}' no encontrada")
            return

        # Verificar estado de instalación según el comando
        is_installed = module.check_installation()
        
        if command_type in ['update', 'remove'] and not is_installed:
            print(f"[!] Error: La herramienta '{tool_name}' no está instalada")
            return
        elif command_type == 'install' and is_installed:
            print(f"[!] La herramienta '{tool_name}' ya está instalada")
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
            print(f"[!] Tipo de comando no válido: {command_type}")
            return
            
        # Obtener el comando específico para este gestor de paquetes
        commands = getattr(module, method_name)(pkg_manager)
        if not commands:
            print(f"[!] No hay comando de {command_type} para el gestor {pkg_manager}")
            return
        
        # Convertir un único comando a lista
        if isinstance(commands, str):
            commands = [commands]
        
        # Ejecutar los comandos
        success = True
        for cmd in commands:
            print(f"\n[*] Ejecutando: {cmd}")
            if not self._run_command(cmd):
                print(f"[!] Error al ejecutar: {cmd}")
                success = False
                break
        
        if not success:
            print(f"[!] Operación {command_type} interrumpida")
        else:
            # Verificar instalación después del comando
            if hasattr(module, 'check_installation'):
                module._installed = None  # Reset estado
                is_installed = module.check_installation()
                
                if command_type == 'install':
                    print(f"[+] {tool_name} {'instalado' if is_installed else 'no instalado'} correctamente")
                elif command_type == 'remove':
                    print(f"[+] {tool_name} {'desinstalado' if not is_installed else 'no desinstalado'} correctamente")

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