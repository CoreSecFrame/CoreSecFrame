#!/usr/bin/env python3

# IMPORTANTE: El monkey patching debe ser lo primero
import eventlet
eventlet.monkey_patch()

import sys
import os
from pathlib import Path
from core.colors import Colors
from core.base import ToolModule
from core.framework_interface import FrameworkInterface

def setup_environment():
    """Configura el entorno para el servidor web"""
    try:
        # Añadir el directorio raíz al PYTHONPATH
        root_dir = Path(__file__).parent
        if str(root_dir) not in sys.path:
            sys.path.append(str(root_dir))
        
        # Crear directorios necesarios si no existen
        static_dir = root_dir / 'static'
        js_dir = static_dir / 'js'
        css_dir = static_dir / 'css'
        
        for directory in [static_dir, js_dir, css_dir]:
            directory.mkdir(exist_ok=True)
            
        # Verificar archivos necesarios
        if not (js_dir / 'app.js').exists():
            print(f"{Colors.WARNING}[!] Warning: app.js not found in {js_dir}{Colors.ENDC}")
            
        if not (css_dir / 'styles.css').exists():
            print(f"{Colors.WARNING}[!] Warning: styles.css not found in {css_dir}{Colors.ENDC}")
            
        if not (root_dir / 'index.html').exists():
            print(f"{Colors.WARNING}[!] Warning: index.html not found in {root_dir}{Colors.ENDC}")
            
        return True
            
    except Exception as e:
        print(f"{Colors.FAIL}[!] Error setting up environment: {e}{Colors.ENDC}")
        return False

def main():
    """Punto de entrada para el servidor web"""
    try:
        # Configurar entorno
        if not setup_environment():
            sys.exit(1)
        
        from core.web_server import WebServer
        
        # Cargar módulos sin mostrar banner
        print(f"\n{Colors.CYAN}[*] Loading framework modules...{Colors.ENDC}")
        modules = ToolModule.load_modules(initial_load=False)
        if not modules:
            print(f"{Colors.FAIL}[!] No modules were loaded. Cannot start web server.{Colors.ENDC}")
            sys.exit(1)
            
        # Inicializar framework sin interfaz de terminal
        framework = FrameworkInterface()
        framework.modules = modules
        
        # Iniciar servidor web
        web_server = WebServer(framework)
        print(f"\n{Colors.SUCCESS}[*] Starting web interface...{Colors.ENDC}")
        web_server.start()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}[!] Web server stopped.{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.FAIL}[!] Critical error: {e}{Colors.ENDC}")
        sys.exit(1)

if __name__ == '__main__':
    main()