import os
import platform


class Colors:
    """Clase para manejar colores en la terminal"""
    
    def __init__(self):
        self.has_colors = os.getenv('TERM') is not None or \
                         os.getenv('COLORTERM') is not None or \
                         platform.system() == 'Windows'

    def __getattr__(self, name):
        # Esquema de colores modernizado
        color_codes = {
            # Colores principales
            'PRIMARY': '\033[38;5;87m',    # Azul claro brillante
            'SECONDARY': '\033[38;5;141m', # Púrpura suave
            'ACCENT': '\033[38;5;219m',    # Rosa suave
            
            # Colores de estado
            'SUCCESS': '\033[38;5;84m',    # Verde brillante
            'WARNING': '\033[38;5;221m',   # Amarillo suave
            'ERROR': '\033[38;5;203m',     # Rojo suave
            
            # Colores de texto
            'TEXT': '\033[38;5;252m',      # Blanco suave
            'SUBTLE': '\033[38;5;242m',    # Gris oscuro
            'HIGHLIGHT': '\033[38;5;159m', # Azul muy claro
            
            # Efectos
            'BOLD': '\033[1m',
            'DIM': '\033[2m',
            'ITALIC': '\033[3m',
            'UNDERLINE': '\033[4m',
            'BLINK': '\033[5m',
            'ENDC': '\033[0m',
            
            # Compatibilidad con nombres antiguos
            'HEADER': '\033[95m',
            'BLUE': '\033[94m',
            'CYAN': '\033[96m',
            'GREEN': '\033[92m',
            'FAIL': '\033[91m',
            'OKGREEN': '\033[92m'
        }
        return color_codes.get(name, '') if self.has_colors else ''


# Instancia global de Colors
Colors = Colors()