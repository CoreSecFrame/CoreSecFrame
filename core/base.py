import sys
import os
from pathlib import Path
from abc import ABC, abstractmethod
import shutil
import subprocess
from typing import List, Optional, Dict

# Añadir el directorio raíz al path si no está ya
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

class ToolModule(ABC):
    def __init__(self):
        self.name: str = self._get_name()
        self.command: str = self._get_command()
        self.description: str = self._get_description()
        self.dependencies: List[str] = self._get_dependencies()
        self._custom_install_path: Optional[str] = None
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
        """
        Retorna la documentación de ayuda del módulo.
        Debe ser implementado por cada herramienta.
        
        Returns:
            Dict: Diccionario con la información de ayuda estructurada que debe incluir:
                - title: Título de la herramienta
                - usage: Sintaxis de uso
                - desc: Descripción detallada
                - options: Diccionario de opciones y sus descripciones
                - examples: Lista de ejemplos de uso
                - notes: Lista de notas adicionales (opcional)
        """
        raise NotImplementedError("Cada herramienta debe implementar su propia ayuda")

    def _get_update_command(self, pkg_manager: str) -> str:
        """
        Método genérico de actualización que ejecuta el comando proporcionado por el módulo específico
        
        :param pkg_manager: Gestor de paquetes actual
        :return: Comando de actualización personalizado por el módulo
        """
        return ''

    def _get_install_command(self, pkg_manager: str) -> str:
        """
        Método genérico de instalación que ejecuta el comando proporcionado por el módulo específico
        
        :param pkg_manager: Gestor de paquetes actual
        :return: Comando de instalación personalizado por el módulo
        """
        return ''

    def _get_uninstall_command(self, pkg_manager: str) -> str:
        """
        Método genérico de desinstalación que ejecuta el comando proporcionado por el módulo específico
        
        :param pkg_manager: Gestor de paquetes actual
        :return: Comando de desinstalación personalizado por el módulo
        """
        return ''

    def set_custom_install_path(self, path: str):
        """
        Establece una ruta personalizada para verificar la instalación
        
        :param path: Ruta completa al script o ejecutable
        """
        self._custom_install_path = path

    @abstractmethod
    def run_guided(self) -> None:
        """Implementa el modo guiado de la herramienta"""
        pass

    def run_direct(self) -> None:
        """Ejecuta la herramienta en modo directo"""
        try:
            subprocess.run(self.command, shell=True)
        except subprocess.SubprocessError as e:
            print(f"Error ejecutando {self.name}: {e}")
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario")

    def check_installation(self) -> bool:
        """
        Verifica la instalación de manera básica
        """
        # Verificación por comando
        command_path = shutil.which(self.command)
        if command_path:
            self._installed = True
            return True
        # Verificación por ruta personalizada
        if self._custom_install_path:
            if os.path.exists(self._custom_install_path):
                self._installed = True
                return True
                
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
