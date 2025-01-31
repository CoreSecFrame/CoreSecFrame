from core.base import ToolModule
import subprocess
import os
import shutil
from pathlib import Path

class AnonIPModule(ToolModule):
    def __init__(self):
        # Llamar al inicializador padre primero
        super().__init__()
        
        # Configurar la ruta del script después
        script_path = Path(__file__).parent.parent / "modules" / "scripts" / "anonip_ES.sh"
        self.set_custom_install_path(str(script_path))

    def _get_name(self):
        return "anonip"  # En minúsculas para coincidir con el patrón de búsqueda

    def _get_command(self):
        return "anonip"

    def _get_description(self):
        return "Herramienta para anonimizar la conexión mediante cambios de IP, MAC y enrutamiento por TOR"

    def _get_dependencies(self):
        return ["tor", "curl", "dhclient", "iptables"]

    def get_help(self) -> dict:
        """
        Proporciona la documentación de ayuda específica de anonip
        """
        return {
            "title": "TEST",
            "usage": "TEST",
            "desc": "TEST",
            "modes": {
                "Guiado": "Modo interactivo que solicita la información necesaria paso a paso",
                "Directo": "Modo que acepta todos los parámetros en la línea de comandos"
            },
            "options": {
                "TEST"
            },
            "examples": [
                "TEST"
            ],
            "notes": [
                "TEST"
            ]
        }

    def check_installation(self) -> bool:
        """Verifica si la herramienta y sus dependencias están instaladas"""
        # Verificar el script primero
        script_exists = super().check_installation()
        if not script_exists:
            return False
            
        # Verificar dependencias
        for dep in self._get_dependencies():
            if not shutil.which(dep):
                print(f"Dependencia no encontrada: {dep}")
                return False
                
        return True


    def get_package_install(self) -> dict:
        """
        Diccionario de comandos de instalación por gestor de paquetes
        """
        base_script_path = Path(__file__).parent.parent / "modules" / "scripts"
        script_url = "https://github.com/sPROFFEs/AnonIP/releases/download/English/AnonIP_ES.sh"  # Ajusta esta URL
        
        # Usando curl
        return {
            'apt': [
                "sudo apt-get update",
                "sudo apt-get install -y tor curl iptables",
                f"mkdir -p {base_script_path}",
                f"curl -o {base_script_path}/anonip_ES.sh {script_url}",
                f"chmod +x {base_script_path}/anonip_ES.sh"
            ],
            'yum': [
                "sudo yum update -y",
                "sudo yum install -y tor curl dhclient iptables",
                f"mkdir -p {base_script_path}",
                f"curl -o {base_script_path}/anonip_ES.sh {script_url}",
                f"chmod +x {base_script_path}/anonip_ES.sh"
            ],
            'dnf': [
                "sudo dnf update -y",
                "sudo dnf install -y tor curl dhclient iptables",
                f"mkdir -p {base_script_path}",
                f"curl -o {base_script_path}/anonip_ES.sh {script_url}",
                f"chmod +x {base_script_path}/anonip_ES.sh"
            ],
            'pacman': [
                "sudo pacman -Sy",
                "sudo pacman -S tor curl dhclient iptables",
                f"mkdir -p {base_script_path}",
                f"curl -o {base_script_path}/anonip_ES.sh {script_url}",
                f"chmod +x {base_script_path}/anonip_ES.sh"
            ]
        }

    def get_package_update(self) -> dict:
        """
        Diccionario de comandos de actualización por gestor de paquetes
        """
        return {
            'apt': [
                "sudo apt update",
                "sudo apt install -y tor curl dhclient iptables"
            ],
            'yum': [
                "sudo yum update -y tor curl dhclient iptables"
            ],
            'dnf': [
                "sudo dnf update -y tor curl dhclient iptables"
            ],
            'pacman': [
                "sudo pacman -Syu tor curl dhclient iptables"
            ]
        }

    def get_package_remove(self) -> dict:
        """
        Diccionario de comandos de desinstalación por gestor de paquetes
        """
        base_script_path = Path(__file__).parent.parent / "modules" / "scripts"
        
        return {
            'apt': [
                "sudo systemctl stop tor",
                "sudo systemctl disable tor",
                "sudo apt-get autoremove -y",
                f"rm -f {base_script_path}/anonip_ES.sh"
            ],
            'yum': [
                "sudo systemctl stop tor",
                "sudo systemctl disable tor",
                "sudo yum remove -y tor curl dhclient iptables",
                "sudo yum autoremove -y",
                f"rm -f {base_script_path}/anonip_ES.sh"
            ],
            'dnf': [
                "sudo systemctl stop tor",
                "sudo systemctl disable tor",
                "sudo dnf remove -y tor curl dhclient iptables",
                "sudo dnf autoremove -y",
                f"rm -f {base_script_path}/anonip_ES.sh"
            ],
            'pacman': [
                "sudo systemctl stop tor",
                "sudo systemctl disable tor",
                "sudo pacman -R tor curl dhclient iptables",
                f"rm -f {base_script_path}/anonip_ES.sh"
            ]
        }

    def get_script_path(self) -> str:
        """Retorna la ruta al script bash"""
        return str(Path(__file__).parent / "scripts" / "AnonIP_ES.sh")

    def run_guided(self) -> None:
        """Ejecuta la herramienta en modo guiado"""
        options = []
        
        print("\nConfiguración de AnonIP")
        print("----------------------")
        
        # Solicitar interfaz de red
        interface = input("\nInterfaz de red (Enter para autodetectar): ").strip()
        if interface:
            options.extend(["-i", interface])
        
        # Solicitar intervalo de tiempo
        interval = input("\nIntervalo en segundos entre cambios (Enter para 1800): ").strip()
        if interval:
            options.extend(["-t", interval])
        
        # Opciones booleanas
        if input("\n¿Cambiar dirección MAC? (s/N): ").lower() == 's':
            options.append("-m")
        
        if input("¿Cambiar dirección IP? (s/N): ").lower() == 's':
            options.append("-p")
        
        if input("¿Usar TOR? (s/N): ").lower() == 's':
            options.append("-T")
        
        # Ejecutar el script con las opciones seleccionadas
        self._execute_script(options)

    def run_direct(self) -> None:
        """Ejecuta la herramienta en modo directo"""
        print("\nOpciones disponibles:")
        print("  -h, --help           Muestra esta ayuda")
        print("  -i, --interface      Especifica la interfaz de red (ej: wlan0)")
        print("  -t, --time           Intervalo en segundos entre cambios")
        print("  -m, --mac            Activa el cambio de dirección MAC")
        print("  -p, --ip             Activa el cambio de dirección IP")
        print("  -T, --tor            Activa el enrutamiento por TOR")
        print("  -s, --switch-tor     Cambia el nodo de salida de TOR")
        print("  -x, --stop           Detiene todos los servicios")
        
        options = input("\nIngresa las opciones deseadas: ").split()
        self._execute_script(options)

    def _execute_script(self, options: list) -> None:
        """Ejecuta el script bash con las opciones especificadas"""
        try:
            script_path = self.get_script_path()
            
            # Construir el comando completo
            cmd = ["sudo", script_path] + options
            
            # Ejecutar el script
            print("\nEjecutando AnonIP...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1  # Line buffered
            )
            
            # Mostrar la salida en tiempo real
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                    
            # Comprobar si hubo errores
            if process.returncode != 0:
                stderr = process.stderr.read()
                if stderr:
                    print(f"Error: {stderr}")
                    
        except Exception as e:
            print(f"Error al ejecutar el script: {e}")
            
    def stop(self) -> None:
        """Detiene los servicios de la herramienta"""
        try:
            subprocess.run([self.get_script_path(), "-x"], check=True)
            print("Servicios detenidos correctamente")
        except subprocess.CalledProcessError as e:
            print(f"Error al detener los servicios: {e}")