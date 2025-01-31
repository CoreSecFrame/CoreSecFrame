#!/usr/bin/env python3
import sys
import os
import signal
from pathlib import Path

def signal_handler(sig, frame):
    """Manejador de señal para Ctrl+C"""
    print("\n\n[!] Saliendo del framework...")
    sys.exit(0)

def setup_environment():
    """Configura el entorno para el framework"""
    # Configurar el manejador de señal para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Añadir el directorio actual al PYTHONPATH
    root_dir = Path(__file__).parent
    sys.path.append(str(root_dir))
    
    # Crear directorios necesarios si no existen
    (root_dir / 'modules').mkdir(exist_ok=True)
    (root_dir / 'core').mkdir(exist_ok=True)
    
    # Crear archivos __init__.py si no existen
    for dir_path in [root_dir, root_dir / 'core', root_dir / 'modules', root_dir / 'config']:
        dir_path.mkdir(exist_ok=True)
        init_file = dir_path / '__init__.py'
        if not init_file.exists():
            init_file.touch()

def main():
    """Punto de entrada principal del framework"""
    setup_environment()
    try:
        from core.framework import Framework  # Cambiado de FrameworkManager a Framework
        framework = Framework()  # Usando la nueva clase Framework
        framework.cmdloop()
    except KeyboardInterrupt:
        print("\n[!] Saliendo del framework...")
        sys.exit(0)
    except Exception as e:
        print(f"[!] Error crítico: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()