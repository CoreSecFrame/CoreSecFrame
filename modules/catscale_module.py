from core.base import ToolModule
from core.colors import Colors
import subprocess
import os
import shutil
from pathlib import Path
import paramiko
import getpass

class CatScaleModule(ToolModule):
    def __init__(self):
        self.repo_url = "https://github.com/sPROFFEs/LinuxCatScale"
        self.base_script_path = Path(__file__).parent.parent / "modules" / "scripts"
        super().__init__()
  
    def _get_name(self):
        return "catscale"

    def _get_category(self) -> str:
        return "Forensics"

    def _get_command(self):
        return "catscale"

    def _get_description(self):
        return "Forensics tool for Linux that captures mobile data, logs, configurations and hashes files"

    def _get_dependencies(self):
        return ["tar", "sha1sum", "find", "grep"]

    def _get_script_path(self) -> str:
        """Retorna la ruta al script bash"""
        return str(Path(__file__).parent.parent / "modules" / "scripts" / "LinuxCatScale" / "Cat-Scale.sh")

    def get_help(self) -> dict:
        """
        Proporciona la documentación de ayuda específica de Cat-Scale
        """
        return {
            "title": "Cat-Scale - Recolección Forense Linux",
            "usage": "use catscale",
            "desc": "Herramienta para recolección forense en sistemas Linux que captura datos volátiles, logs, configuraciones y realiza hashes de archivos.",
            "modes": {
                "Guiado": "Modo interactivo que solicita la información necesaria paso a paso",
                "Directo": "Modo que acepta todos los parámetros en la línea de comandos"
            },
            "options": {
                "-o OUTDIR": "Directorio donde guardar el archivo comprimido",
                "--remote HOST": "Host remoto para recolección",
                "--user USER": "Usuario SSH para conexión remota",
                "--key KEY": "Ruta a la clave SSH (opcional)",
                "--password": "Usar autenticación por contraseña"
            },
            "examples": [
                "use catscale",
                "catscale -o /forensics",
                "catscale --remote 192.168.1.10 --user admin --password"
            ],
            "notes": [
                "La herramienta generará un archivo comprimido con la evidencia recolectada",
                "En modo remoto, el archivo se descargará automáticamente al sistema local",
                "Se incluye un script de descompresión para organizar la evidencia"
            ]
        }

    def check_installation(self) -> bool:
        """
        Verifica la instalación comprobando la existencia del repositorio y sus archivos
        """
        scripts_dir = Path(__file__).parent.parent / "modules" / "scripts"
        repo_dir = scripts_dir / "LinuxCatScale"  # Directorio del repositorio clonado
        
        # Lista de archivos requeridos
        required_files = [
            "Cat-Scale.sh",
            "patterns",
            "Cat-Scale-logstash.conf"
        ]
        
        # Verificar que existe el directorio del repositorio
        if not repo_dir.exists() or not repo_dir.is_dir():
            self._installed = False
            return False
            
        # Verificar que existen todos los archivos necesarios
        for file in required_files:
            if not (repo_dir / file).exists():
                self._installed = False
                return False
                
        # Verificar que el script principal tiene permisos de ejecución
        script_path = repo_dir / "Cat-Scale.sh"
        if not os.access(script_path, os.X_OK):
            try:
                os.chmod(script_path, 0o755)
            except:
                self._installed = False
                return False
        
        # Si todo está correcto, actualizar la ruta de instalación y retornar True
        self._installed = True
        self._custom_install_path = str(script_path)
        return True


    def _get_install_command(self, pkg_manager: str) -> dict:
        """Diccionario de comandos de instalación por gestor de paquetes"""
        commands = {
            'apt': [
                "sudo apt-get update",
                "sudo apt-get install -y coreutils findutils grep git rename",
                f"mkdir -p {self.base_script_path}",
                f"cd {self.base_script_path} && git clone {self.repo_url}"
            ],
            'yum': [
                "sudo yum update -y",
                "sudo yum install -y coreutils findutils grep git rename",
                f"mkdir -p {self.base_script_path}",
                f"cd {self.base_script_path} && git clone {self.repo_url}"
            ],
            'dnf': [
                "sudo dnf update -y",
                "sudo dnf install -y coreutils findutils grep git rename",
                f"mkdir -p {self.base_script_path}",
                f"cd {self.base_script_path} && git clone {self.repo_url}"
            ],
            'pacman': [
                "sudo pacman -Sy",
                "sudo pacman -S coreutils findutils grep git rename",
                f"mkdir -p {self.base_script_path}",
                f"cd {self.base_script_path} && git clone {self.repo_url}"
            ]
        }
        return commands.get(pkg_manager, {})

    def _get_update_command(self, pkg_manager: str) -> dict:
        """Diccionario de comandos de actualización por gestor de paquetes"""
        commands = {
            'apt': [
                "sudo apt-get update",
                "sudo apt-get install -y coreutils findutils grep git rename",
                f"mkdir -p {self.base_script_path}",
                f"rm -rf {self.base_script_path}/LinuxCatScale",
                f"cd {self.base_script_path} && git clone {self.repo_url}"
            ],
            'yum': [
                "sudo yum update -y",
                "sudo yum install -y coreutils findutils grep git rename",
                f"mkdir -p {self.base_script_path}",
                f"rm -rf {self.base_script_path}/LinuxCatScale",
                f"cd {self.base_script_path} && git clone {self.repo_url}"
            ],
            'dnf': [
                "sudo dnf update -y",
                "sudo dnf install -y coreutils findutils grep git rename",
                f"mkdir -p {self.base_script_path}",
                f"rm -rf {self.base_script_path}/LinuxCatScale",
                f"cd {self.base_script_path} && git clone {self.repo_url}"
            ],
            'pacman': [
                "sudo pacman -Sy",
                "sudo pacman -S coreutils findutils grep git rename",
                f"mkdir -p {self.base_script_path}",
                f"rm -rf {self.base_script_path}/LinuxCatScale",
                f"cd {self.base_script_path} && git clone {self.repo_url}"
            ]
        }
        return commands.get(pkg_manager, {})

    def _get_uninstall_command(self, pkg_manager: str) -> dict:
        """Diccionario de comandos de desinstalación por gestor de paquetes"""
        commands = {
            'apt': [
                f"rm -rf {self.base_script_path}/LinuxCatScale",
            ],
            'yum': [
                f"rm -rf {self.base_script_path}/LinuxCatScale",
            ],
            'dnf': [
                f"rm -rf {self.base_script_path}/LinuxCatScale",
            ],
            'pacman': [
                f"rm -rf {self.base_script_path}/LinuxCatScale",
            ]
        }
        return commands.get(pkg_manager, {})

    def run_guided(self) -> None:
        """Ejecuta la herramienta en modo guiado"""
        print("\nConfiguración de Cat-Scale")
        print("------------------------")
        
        # Preguntar si es ejecución local o remota
        is_remote = input("\n¿Desea ejecutar la recolección en un sistema remoto? (s/N): ").lower() == 's'
        
        if is_remote:
            # Solicitar información para conexión remota
            host = input("\nIngrese el host remoto: ").strip()
            user = input("Ingrese el usuario SSH: ").strip()
            
            # Preguntar método de autenticación
            auth_method = input("¿Usar autenticación por contraseña? (s/N): ").lower() == 's'
            
            options = ["--remote", host, "--user", user]
            if auth_method:
                options.append("--password")
            else:
                key_path = input("Ingrese la ruta a la clave SSH: ").strip()
                options.extend(["--key", key_path])
                
            self._execute_remote(options)
        else:
            # Para ejecución local, solo preguntar dónde guardar el archivo
            save_path = input("\nIngrese la ruta donde guardar el archivo comprimido (Enter para usar el directorio actual): ").strip()
            options = ["-o", save_path] if save_path else []
            
            self._execute_script(options)

    def run_direct(self) -> None:
        """Ejecuta la herramienta en modo directo"""
        print(f"\n{Colors.CYAN}[*] ATENTION: This commands are only avaiable on LOCAL EXECUTION{Colors.ENDC}")
        print("  -d OUTDIR           Output directory")
        print("  -o OUTROOT          Output root directory")
        print("  -p PREFIX           Output file prefix")
        print(f"\n{Colors.CYAN}[*] ATENTION: This commands are only avaiable on REMOTE EXECUTION{Colors.ENDC}")
        print("  --remote <HOST>       Remote host")
        print("  --user <USER>         Remote user")
        print("  --key <KEY>           Remote key path (optional)")
        print("  --password (press enter and write your password)")
        
        options = input(f"\n{Colors.BOLD}Insert options: {Colors.ENDC}").split()
        
        # Verificar si es una ejecución remota
        if "--remote" in options:
            self._execute_remote(options)
        else:
            self._execute_script(options)

    def _execute_script(self, options: list) -> None:
        """Ejecuta el script localmente con las opciones especificadas"""
        script_path = self._get_script_path()
        cmd = ["sudo", script_path] + options
        
        print("\nEjecutando Cat-Scale localmente...")
        if self.run_script(cmd):  # Usar el método heredado de GetModule
            # Si la ejecución fue exitosa, obtener el archivo generado
            try:
                # Buscar prefijo personalizado
                prefix = None
                for i in range(len(options)):
                    if options[i] == '-p' and i + 1 < len(options):
                        prefix = options[i + 1]
                        break
                
                # Buscar el archivo generado en el directorio actual
                if prefix:
                    pattern = f"{prefix}*.tar.gz"
                else:
                    pattern = "catscale_*.tar.gz"
                    
                matches = list(Path(".").glob(pattern))
                if matches:
                    # Ordenar por fecha de modificación y tomar el más reciente
                    latest_file = max(matches, key=lambda p: p.stat().st_mtime)
                    print(f"\nArchivo generado: {latest_file}")
                    # Manejar la descompresión
                    self._handle_decompression_script(str(latest_file))
                else:
                    print("No se encontró el archivo generado.")
            except Exception as e:
                print(f"Error al manejar el archivo generado: {e}")

    def _try_ssh_connect(self, remote_host: str, remote_user: str, use_password: bool = False, key_path: str = None, max_attempts: int = 3) -> tuple:
        """Intenta conectar por SSH con reintentos de contraseña
        
        Returns:
            tuple: (ssh_client, sudo_password) o (None, None) si falla
        """
        attempts = 0
        while attempts < max_attempts:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if use_password:
                    password = getpass.getpass(f"Contraseña SSH (intento {attempts + 1}/{max_attempts}): ")
                    try:
                        ssh.connect(remote_host, username=remote_user, password=password)
                        print("Conexión SSH establecida correctamente.")
                    except paramiko.AuthenticationException:
                        print("Error: Contraseña SSH incorrecta.")
                        attempts += 1
                        if attempts == max_attempts:
                            print("Número máximo de intentos alcanzado.")
                            return None, None
                        continue
                elif key_path:
                    try:
                        key = paramiko.RSAKey.from_private_key_file(key_path)
                        ssh.connect(remote_host, username=remote_user, pkey=key)
                        print("Conexión SSH establecida correctamente usando clave privada.")
                    except (paramiko.SSHException, IOError) as e:
                        print(f"Error con la clave privada: {e}")
                        return None, None
                else:
                    ssh.connect(remote_host, username=remote_user)
                    print("Conexión SSH establecida correctamente.")
                
                # Si llegamos aquí, la conexión SSH fue exitosa
                # Ahora manejamos la contraseña sudo
                sudo_attempts = 0
                while sudo_attempts < max_attempts:
                    sudo_password = getpass.getpass(f"Contraseña sudo (intento {sudo_attempts + 1}/{max_attempts}): ")
                    
                    # Verificar la contraseña sudo
                    try:
                        channel = ssh.get_transport().open_session()
                        channel.get_pty()
                        channel.exec_command(f"echo '{sudo_password}' | sudo -S echo 'sudo test'")
                        
                        # Esperar la respuesta
                        exit_status = channel.recv_exit_status()
                        if exit_status == 0:
                            print("Autenticación sudo verificada correctamente.")
                            channel.close()
                            return ssh, sudo_password
                        else:
                            print("Error: Contraseña sudo incorrecta.")
                            sudo_attempts += 1
                            if sudo_attempts == max_attempts:
                                print("Número máximo de intentos de sudo alcanzado.")
                                ssh.close()
                                return None, None
                    except Exception as e:
                        print(f"Error al verificar sudo: {e}")
                        ssh.close()
                        return None, None
                    
            except paramiko.SSHException as e:
                print(f"Error de conexión SSH: {e}")
                return None, None
            except Exception as e:
                print(f"Error inesperado: {e}")
                return None, None
            
            attempts += 1
        
        return None, None


    def _execute_remote(self, options: list) -> None:
        """Ejecuta el script en un sistema remoto vía SSH"""
        def remote_execution():
            ssh = None
            remote_script = "/tmp/Cat-Scale.sh"
            try:
                # Extraer opciones de SSH
                remote_host = None
                remote_user = None
                key_path = None
                use_password = False
                
                # Procesar opciones de línea de comandos
                i = 0
                while i < len(options):
                    if options[i] == "--remote":
                        remote_host = options[i + 1]
                        options.pop(i)
                        options.pop(i)
                    elif options[i] == "--user":
                        remote_user = options[i + 1]
                        options.pop(i)
                        options.pop(i)
                    elif options[i] == "--key":
                        key_path = options[i + 1]
                        options.pop(i)
                        options.pop(i)
                    elif options[i] == "--password":
                        use_password = True
                        options.pop(i)
                    else:
                        i += 1
                
                if not remote_host or not remote_user:
                    print("Error: Se requiere especificar host remoto y usuario")
                    return
                    
                # Intentar establecer la conexión SSH y obtener contraseña sudo
                ssh, sudo_password = self._try_ssh_connect(remote_host, remote_user, use_password, key_path)
                if not ssh or not sudo_password:
                    print("No se pudo establecer la conexión. Abortando.")
                    return
                
                # Transferir el script y archivos adicionales
                script_path = Path(self._get_script_path())
                repo_path = script_path.parent

                sftp = ssh.open_sftp()
                # Transferir el script principal
                sftp.put(str(script_path), remote_script)
                sftp.chmod(remote_script, 0o755)
                # Transferir archivos adicionales
                sftp.put(str(repo_path / 'patterns'), '/tmp/patterns')
                sftp.put(str(repo_path / 'Cat-Scale-logstash.conf'), '/tmp/Cat-Scale-logstash.conf')
                
                # Construir y ejecutar el comando remoto con sudo
                cmd = f"echo '{sudo_password}' | sudo -S {remote_script} {' '.join(options)}"
                print(f"\nEjecutando Cat-Scale en {remote_host}...")
                
                # Crear un canal SSH y solicitar un pseudo-terminal
                channel = ssh.get_transport().open_session()
                channel.get_pty()
                channel.exec_command(cmd)
                
                # Capturar toda la salida
                output_buffer = []
                while True:
                    if channel.recv_ready():
                        data = channel.recv(4096).decode('utf-8')
                        print(data, end='')  # Imprimir la salida en tiempo real
                        output_buffer.append(data)
                    if channel.exit_status_ready() and not channel.recv_ready():
                        break
                
                # Obtener errores si los hay
                stderr_output = ""
                while channel.recv_stderr_ready():
                    stderr_data = channel.recv_stderr(4096).decode('utf-8')
                    stderr_output += stderr_data
                
                # Obtener el nombre del archivo generado
                output_text = ''.join(output_buffer)
                # Buscar prefijo personalizado
                prefix = None
                for i in range(len(options)):
                    if options[i] == '-p' and i + 1 < len(options):
                        prefix = options[i + 1]
                        break
                
                remote_file = self._get_remote_file_path(output_text, prefix)
                
                if remote_file:
                    print("\nEl script ha generado el archivo:", remote_file)
                    default_path = os.path.join(os.getcwd(), "forensics", remote_file)
                    local_path = input(f"Ingrese la ruta donde desea guardar el archivo [{default_path}]: ").strip()
                    
                    if not local_path:
                        local_path = default_path
                    
                    if self._download_remote_file(ssh, remote_file, local_path):
                        print(f"Archivo guardado en: {local_path}")
                        
                        # Eliminar archivo generado y archivos temporales
                        print("Limpiando archivos temporales...")
                        cleanup_cmd = f"echo '{sudo_password}' | sudo -S rm -f {remote_file} {remote_script} /tmp/patterns /tmp/Cat-Scale-logstash.conf"
                        
                        # Crear un nuevo canal para la limpieza
                        cleanup_channel = ssh.get_transport().open_session()
                        cleanup_channel.get_pty()
                        cleanup_channel.exec_command(cleanup_cmd)
                        
                        # Esperar a que termine la limpieza y manejar cualquier error
                        exit_status = cleanup_channel.recv_exit_status()
                        if exit_status != 0:
                            stderr = cleanup_channel.recv_stderr(4096).decode('utf-8')
                            print(f"Advertencia: La limpieza de archivos puede no haber sido completa. Estado: {exit_status}")
                            if stderr:
                                print(f"Error durante limpieza: {stderr}")
                        
                        cleanup_channel.close()
                        self._handle_decompression_script(local_path)
                    else:
                        print("No se pudo descargar el archivo.")
                else:
                    print("No se pudo determinar el nombre del archivo generado.")
                    
                    # Limpiar solo los archivos temporales si no se generó archivo
                    cleanup_cmd = f"echo '{sudo_password}' | sudo -S rm -f {remote_script} /tmp/patterns /tmp/Cat-Scale-logstash.conf"
                    cleanup_channel = ssh.get_transport().open_session()
                    cleanup_channel.get_pty()
                    cleanup_channel.exec_command(cleanup_cmd)
                    cleanup_channel.recv_exit_status()
                    cleanup_channel.close()
                
                if stderr_output:
                    print(f"Error: {stderr_output}")
                    
            except Exception as e:
                print(f"Error en la ejecución remota: {e}")
            finally:
                if ssh:
                    try:
                        ssh.close()
                    except:
                        pass
                        
        self.execute_with_cleanup(remote_execution)

    def _get_remote_file_path(self, stdout_data: str, prefix: str = None) -> str:
        """Extrae el nombre del archivo comprimido de la salida del script
        
        Args:
            stdout_data (str): Salida del script a analizar
            prefix (str, optional): Prefijo especificado por el usuario. Si es None, 
                                se usa 'catscale_' como prefijo por defecto.
        
        Returns:
            str: Nombre del archivo encontrado o None si no se encuentra
        """
        import re
        
        # Si no se especifica prefijo, usar el valor por defecto
        if prefix is None:
            prefix = 'catscale_'
            
        # Escapar caracteres especiales en el prefijo para la expresión regular
        escaped_prefix = re.escape(prefix)
        
        # Construir el patrón con el prefijo dinámico
        pattern = f'{escaped_prefix}[a-zA-Z0-9_-]+-\\d{{8}}-\\d{{4}}\\.tar\\.gz'
        
        matches = re.findall(pattern, stdout_data)
        if matches:
            return matches[-1]  # Retornamos el último match encontrado
        return None

    def _download_remote_file(self, ssh: paramiko.SSHClient, remote_file: str, local_path: str) -> bool:
        """Descarga el archivo comprimido desde el host remoto"""
        try:
            sftp = ssh.open_sftp()
            # Asegurarse que el directorio local existe
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Obtener el tamaño del archivo remoto
            remote_stat = sftp.stat(remote_file)
            total_size = remote_stat.st_size
            
            print(f"\nDescargando archivo ({total_size/1024/1024:.2f} MB)...")
            
            # Configurar callback para mostrar progreso
            def progress_callback(transferred: int, total: int):
                percentage = (transferred / total) * 100
                print(f"Progreso: {percentage:.2f}%", end='\r')
            
            # Descargar el archivo
            sftp.get(remote_file, local_path, callback=progress_callback)
            print("\nDescarga completada con éxito!")
            return True
            
        except Exception as e:
            print(f"Error al descargar el archivo: {e}")
            return False

    def _handle_decompression_script(self, compressed_file_path: str) -> None:
        """Maneja la copia y ejecución del script de descompresión"""
        try:
            # Convertir la ruta del archivo comprimido a Path
            compressed_file = Path(compressed_file_path).resolve()  # resolve() para obtener la ruta absoluta
            target_dir = compressed_file.parent
            
            # Ruta al script de descompresión
            decompress_script = Path(self._get_script_path()).parent / "Extract-Cat-Scale.sh"
            
            if not decompress_script.exists():
                print("\nAdvertencia: No se encuentra el script de descompresión.")
                return
                    
            target_script = target_dir / "Extract-Cat-Scale.sh"
            
            print("\nSe ha detectado un script para descomprimir y organizar el archivo.")
            copy_script = input("¿Desea copiar el script de descompresión a la carpeta del archivo? (s/N): ").lower() == 's'
            
            if copy_script:
                # Copiar el script
                shutil.copy2(decompress_script, target_script)
                os.chmod(target_script, 0o755)  # Dar permisos de ejecución
                print(f"\nScript copiado a: {target_script}")
                
                # Preguntar si quiere ejecutarlo
                execute_script = input("¿Desea ejecutar el script de descompresión ahora? (s/N): ").lower() == 's'
                
                if execute_script:
                    print("\nEjecutando script de descompresión...")
                    try:
                        # Guardar el directorio actual
                        original_dir = os.getcwd()
                        
                        try:
                            # Cambiar al directorio donde está el archivo comprimido
                            os.chdir(target_dir)
                            
                            # Asegurarnos que el archivo comprimido está en el directorio actual
                            if not compressed_file.exists():
                                raise FileNotFoundError(f"No se encuentra el archivo {compressed_file.name}")
                                
                            # Ejecutar el script
                            subprocess.run([
                                "sudo",
                                str(target_script)
                            ], check=True)
                            
                            print("Descompresión completada con éxito.")
                            
                        finally:
                            # Volver al directorio original
                            os.chdir(original_dir)
                        
                        self.cleanup_tmux_session()
                        
                    except subprocess.CalledProcessError as e:
                        print(f"Error al ejecutar el script de descompresión: {e}")
                        self.cleanup_tmux_session()
                    except Exception as e:
                        print(f"Error durante la descompresión: {e}")
                        self.cleanup_tmux_session()
                else:
                    print(f"\nPuede ejecutar el script más tarde con:")
                    print(f"cd {target_dir} && sudo ./Extract-Cat-Scale.sh")
                    self.cleanup_tmux_session()
            else:
                print(f"\nScript disponible en: {decompress_script}")
                print(f"Puede copiarlo y ejecutarlo más tarde con:")
                print(f"cd /ruta/del/archivo && sudo ./Extract-Cat-Scale.sh")
                self.cleanup_tmux_session()
                    
        except Exception as e:
            print(f"\nError al manejar el script de descompresión: {e}")
            self.cleanup_tmux_session()

