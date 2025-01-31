from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO


class LogManager:
    """Gestiona el logging de las sesiones del framework"""
    
    def __init__(self, session_id: str, name: str):
        self.session_id = session_id
        self.name = name
        self.output_file: Optional[TextIO] = None
        self.log_path: Optional[Path] = None

    def start_logging(self, filename: str = None) -> None:
        """Inicia el logging de la sesión
        
        Args:
            filename: Nombre del archivo de log opcional. Si no se proporciona,
                     se genera automáticamente.
        """
        if not filename:
            # Create logs directory if it doesn't exist
            logs_dir = Path('logs')
            logs_dir.mkdir(exist_ok=True)
            
            filename = logs_dir / f"session_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.log_path = Path(filename)
        self.output_file = open(self.log_path, 'a')
        self._write_header()

    def stop_logging(self) -> None:
        """Detiene el logging de la sesión"""
        if self.output_file:
            self._write_footer()
            self.output_file.close()
            self.output_file = None

    def log(self, message: str) -> None:
        """Registra un mensaje en el archivo de log
        
        Args:
            message: Mensaje a registrar
        """
        if self.output_file:
            self.output_file.write(f"{datetime.now()}: {message}\n")
            self.output_file.flush()  # Ensure immediate write

    def _write_header(self) -> None:
        """Escribe la cabecera del archivo de log"""
        self.output_file.write(f"=== Session Started: {datetime.now()} ===\n")
        self.output_file.write(f"Tool: {self.name}\n")
        self.output_file.write(f"Session ID: {self.session_id}\n")
        self.output_file.flush()

    def _write_footer(self) -> None:
        """Escribe el pie del archivo de log"""
        self.output_file.write(f"=== Session Ended: {datetime.now()} ===\n")
        self.output_file.write(f"Duration: {self.get_session_duration()}\n")
        self.output_file.flush()

    def get_session_duration(self) -> str:
        """Calcula y retorna la duración de la sesión
        
        Returns:
            str: Duración en formato HH:MM:SS
        """
        if not hasattr(self, 'start_time'):
            return "00:00:00"
            
        duration = datetime.now() - self.start_time
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        seconds = duration.seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"