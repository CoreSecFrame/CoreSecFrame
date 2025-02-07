#!/usr/bin/env python3
import sys
import os
import signal
from pathlib import Path
import subprocess
from getpass import getpass
from core.colors import Colors
from core.terminal_management import TerminalManager

def signal_handler(sig, frame):
    """Manejador de señal para Ctrl+C"""
    print("\n\n[!] Exiting the framework...")
    sys.exit(0)

def get_sudo_permission():
    """Obtiene permisos de sudo si es necesario"""
    if os.geteuid() == 0:
        return True
            
    try:
        # Intentamos ejecutar sudo -v para verificar si ya tenemos permisos de sudo
        result = subprocess.run(['sudo', '-n', 'true'], capture_output=True)
        if result.returncode == 0:
            return True
            
        print(f"{Colors.FAIL}[!] This framework requires administrator privileges{Colors.ENDC}")    
        # Si no tenemos permisos, pedimos la contraseña
        password = getpass("[?] Introduce your sudo password: ")
        
        # Verificamos si la contraseña es correcta
        cmd = ['sudo', '-S', 'true']
        process = subprocess.Popen(
            cmd, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        output, error = process.communicate(input=password.encode())
        
        if process.returncode == 0:
            TerminalManager.clear_screen()
            return True
        else:
            print(f"{Colors.FAIL}[!] Incorrect password{Colors.ENDC}")
            return False
            
    except KeyboardInterrupt:
        print("\n[!] Canceled operation")
        return False
    except Exception as e:
        print(f"{Colors.WARNING}[!] Error checking privileges: {e}{Colors.ENDC}")
        return False

def setup_environment():
    """Configura el entorno para el framework"""
    # Configurar el manejador de señal para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Añadir el directorio actual al PYTHONPATH
    root_dir = Path(__file__).parent
    sys.path.append(str(root_dir))
    
    # Crear directorios necesarios si no existen
    try:
        (root_dir / 'modules').mkdir(exist_ok=True)
        (root_dir / 'core').mkdir(exist_ok=True)
        (root_dir / 'cache').mkdir(exist_ok=True)
        
        # Crear archivos __init__.py si no existen
        for dir_path in [root_dir, root_dir / 'core', root_dir / 'modules']:
            dir_path.mkdir(exist_ok=True)
            init_file = dir_path / '__init__.py'
            if not init_file.exists():
                init_file.touch()
                
        # Update modules cache if needed
        from core.module_cache import ModuleCache
        repo_url = "https://github.com/CoreSecFrame/CoreSecFrame-Modules"  # Default repository URL
        
        if ModuleCache.needs_update():
            ModuleCache.update_cache(repo_url=repo_url)
            
    except PermissionError:
        print(f"{Colors.FAIL}[!] No enough permissions to create directories{Colors.ENDC}")
        return False
    except Exception as e:
        print(f"{Colors.FAIL}[!] Error setting up environment: {e}{Colors.ENDC}")
        return False
        
    return True
    
def main():
    """Main entry point for the framework"""
    from core.terminal_management import TerminalManager
    
    # Verify root privileges
    if not get_sudo_permission():
        sys.exit(1)

    # Configure environment
    if not setup_environment():
        sys.exit(1)
    
    try:
        from core.framework_interface import FrameworkInterface
        from core.base import ToolModule
        
        # Check module compatibility before loading
        compatibility_status = ToolModule.check_module_compatibility()
        
        # Display compatibility results
        if compatibility_status['Compatible']:
            print(f"\n{Colors.GREEN}[✓] Compatible modules:{Colors.ENDC}")
            for module in compatibility_status['Compatible']:
                print(f"{Colors.CYAN}  ├─ {module}{Colors.ENDC}")
                
        if compatibility_status['Incompatible']:
            print(f"\n{Colors.WARNING}[!] Incompatible modules detected:{Colors.ENDC}")
            for module in compatibility_status['Incompatible']:
                print(f"{Colors.FAIL}  ├─ {module['name']}: {module['reason']}{Colors.ENDC}")
        
        # Verify and load modules with initial_load=True
        try:
            if compatibility_status['Incompatible']:
                print(f"\n{Colors.CYAN}[*] Press Enter to continue...{Colors.ENDC}")
                input()

            modules = ToolModule.load_modules(initial_load=True)
            if not modules:
                print(f"\n{Colors.WARNING}[!] No modules are currently loaded{Colors.ENDC}")
                print(f"{Colors.CYAN}[*] You can use the 'shop' command to download modules{Colors.ENDC}")
                print(f"\n{Colors.CYAN}[*] Press Enter to continue...{Colors.ENDC}")
                input()
                
                if input(f"\n{Colors.WARNING}Continue without modules? (y/N): {Colors.ENDC}").lower() != 'y':
                    print(f"\n{Colors.FAIL}[!] Exiting due to no modules loaded{Colors.ENDC}")
                    sys.exit(1)
                    
        except Exception as e:
            print(f"{Colors.WARNING}[!] Error loading modules: {e}{Colors.ENDC}")
            print(f"{Colors.CYAN}[*] You can use the 'shop' command to download modules{Colors.ENDC}")
            print(f"\n{Colors.CYAN}[*] Press Enter to continue...{Colors.ENDC}")
            input()
            
            if input(f"\n{Colors.WARNING}Continue anyway? (y/N): {Colors.ENDC}").lower() != 'y':
                print(f"\n{Colors.FAIL}[!] Exiting due to module loading errors{Colors.ENDC}")
                sys.exit(1)
        
        # Clear screen only after user has seen all messages and decided to continue
        TerminalManager.clear_screen()
        framework = FrameworkInterface()
        framework.cmdloop()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}[!] Exiting the framework...{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.FAIL}[!] Critical error: {e}{Colors.ENDC}")
        sys.exit(1)

if __name__ == '__main__':
    main()
