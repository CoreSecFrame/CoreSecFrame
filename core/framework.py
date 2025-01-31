import signal
from .framework_interface import FrameworkInterface
from .colors import Colors
from pathlib import Path


class Framework(FrameworkInterface):
    def __init__(self):
        super().__init__()
        signal.signal(signal.SIGINT, self.handle_sigint)        

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