import paramiko
import getpass
from pathlib import Path
import os
from typing import Optional, Tuple, Callable
from dataclasses import dataclass

@dataclass
class SSHCredentials:
    """Data class to store SSH connection credentials"""
    host: str
    user: str
    password: Optional[str] = None
    key_path: Optional[str] = None
    use_password: bool = False

class SSHManager:
    """Manages SSH connections and file operations for remote hosts"""
    
    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts
        self._ssh: Optional[paramiko.SSHClient] = None
        self._sudo_password: Optional[str] = None

    @property 
    def is_connected(self) -> bool:
        """Check if there's an active SSH connection"""
        return self._ssh is not None and self._ssh.get_transport() is not None

    def connect(self, credentials: SSHCredentials) -> Tuple[bool, Optional[str]]:
        """
        Establishes SSH connection and verifies sudo access
        
        Args:
            credentials: SSHCredentials object containing connection details
            
        Returns:
            Tuple[bool, Optional[str]]: (Success status, Error message if any)
        """
        attempts = 0
        while attempts < self.max_attempts:
            try:
                self._ssh = paramiko.SSHClient()
                self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if credentials.use_password:
                    password = getpass.getpass(f"SSH Password (attempt {attempts + 1}/{self.max_attempts}): ")
                    try:
                        self._ssh.connect(credentials.host, username=credentials.user, password=password)
                        print("SSH connection established successfully.")
                    except paramiko.AuthenticationException:
                        print("Error: Invalid SSH password.")
                        attempts += 1
                        if attempts == self.max_attempts:
                            return False, "Maximum SSH authentication attempts reached"
                        continue
                elif credentials.key_path:
                    try:
                        key = paramiko.RSAKey.from_private_key_file(credentials.key_path)
                        self._ssh.connect(credentials.host, username=credentials.user, pkey=key)
                        print("SSH connection established successfully using private key.")
                    except (paramiko.SSHException, IOError) as e:
                        return False, f"Private key error: {str(e)}"
                else:
                    self._ssh.connect(credentials.host, username=credentials.user)
                    print("SSH connection established successfully.")
                
                # Verify sudo access
                if not self._verify_sudo_access():
                    return False, "Failed to verify sudo access"
                    
                return True, None
                
            except paramiko.SSHException as e:
                return False, f"SSH connection error: {str(e)}"
            except Exception as e:
                return False, f"Unexpected error: {str(e)}"
            
            attempts += 1
            
        return False, "Maximum connection attempts reached"

    def _verify_sudo_access(self) -> bool:
        """
        Verifies sudo access by requesting and testing sudo password
        
        Returns:
            bool: True if sudo access is verified, False otherwise
        """
        sudo_attempts = 0
        while sudo_attempts < self.max_attempts:
            try:
                self._sudo_password = getpass.getpass(
                    f"Sudo password (attempt {sudo_attempts + 1}/{self.max_attempts}): "
                )
                
                channel = self._ssh.get_transport().open_session()
                channel.get_pty()
                channel.exec_command(f"echo '{self._sudo_password}' | sudo -S echo 'sudo test'")
                
                exit_status = channel.recv_exit_status()
                if exit_status == 0:
                    print("Sudo access verified successfully.")
                    channel.close()
                    return True
                else:
                    print("Error: Invalid sudo password.")
                    sudo_attempts += 1
                    if sudo_attempts == self.max_attempts:
                        print("Maximum sudo authentication attempts reached.")
                        return False
            except Exception as e:
                print(f"Error verifying sudo access: {e}")
                return False
        
        return False

    def execute_command(self, command: str, use_sudo: bool = False) -> Tuple[int, str, str]:
        """
        Executes a command on the remote host
        
        Args:
            command: Command to execute
            use_sudo: Whether to execute command with sudo
            
        Returns:
            Tuple[int, str, str]: (Exit status, stdout, stderr)
        """
        if not self.is_connected:
            raise RuntimeError("No active SSH connection")
            
        try:
            channel = self._ssh.get_transport().open_session()
            channel.get_pty()
            
            if use_sudo:
                if not self._sudo_password:
                    raise RuntimeError("Sudo password not available")
                command = f"echo '{self._sudo_password}' | sudo -S {command}"
                
            channel.exec_command(command)
            
            # Capture output
            stdout = ""
            stderr = ""
            while True:
                if channel.recv_ready():
                    stdout += channel.recv(4096).decode('utf-8')
                if channel.recv_stderr_ready():
                    stderr += channel.recv_stderr(4096).decode('utf-8')
                if channel.exit_status_ready() and not (channel.recv_ready() or channel.recv_stderr_ready()):
                    break
                    
            exit_status = channel.recv_exit_status()
            channel.close()
            
            return exit_status, stdout, stderr
            
        except Exception as e:
            return -1, "", str(e)

    def upload_file(self, local_path: str, remote_path: str, callback: Optional[Callable] = None) -> bool:
        """
        Uploads a file to the remote host
        
        Args:
            local_path: Path to local file
            remote_path: Path where to store file on remote host
            callback: Optional callback function for progress updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected:
            raise RuntimeError("No active SSH connection")
            
        try:
            sftp = self._ssh.open_sftp()
            sftp.put(local_path, remote_path, callback=callback)
            return True
        except Exception as e:
            print(f"Error uploading file: {e}")
            return False

    def download_file(self, remote_path: str, local_path: str, callback: Optional[Callable] = None) -> bool:
        """
        Downloads a file from the remote host
        
        Args:
            remote_path: Path to remote file
            local_path: Path where to store file locally
            callback: Optional callback function for progress updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected:
            raise RuntimeError("No active SSH connection")
            
        try:
            # Ensure local directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            sftp = self._ssh.open_sftp()
            
            # Get remote file size for progress tracking
            remote_stat = sftp.stat(remote_path)
            total_size = remote_stat.st_size
            
            print(f"\nDownloading file ({total_size/1024/1024:.2f} MB)...")
            
            # Use provided callback or default progress callback
            if not callback:
                def default_callback(transferred: int, total: int):
                    percentage = (transferred / total) * 100
                    print(f"Progress: {percentage:.2f}%", end='\r')
                callback = default_callback
            
            sftp.get(remote_path, local_path, callback=callback)
            print("\nDownload completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            return False

    def close(self):
        """Closes the SSH connection"""
        if self._ssh:
            try:
                self._ssh.close()
                self._ssh = None
                self._sudo_password = None
            except:
                pass