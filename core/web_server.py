# IMPORTANTE: El monkey patching debe ser lo primero
import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import os
import pty
import select
import subprocess
import termios
import struct
import fcntl
from threading import Thread, Lock
from pathlib import Path

class PtyManager:
    """Gestor de terminales PTY virtuales"""
    def __init__(self):
        self.terminals = {}
        self.lock = Lock()

    def create_terminal(self, session_id):
        """Crea un nuevo terminal PTY"""
        try:
            # Crear el PTY
            master_fd, slave_fd = pty.openpty()
            
            # Configurar el terminal
            term_settings = termios.tcgetattr(slave_fd)
            term_settings[3] = term_settings[3] & ~termios.ECHO  # Deshabilitar eco
            termios.tcsetattr(slave_fd, termios.TCSADRAIN, term_settings)
            
            # Configurar entorno
            env = os.environ.copy()
            env["TERM"] = "xterm-256color"
            
            # Crear proceso bash sin preexec_fn para evitar el error
            process = subprocess.Popen(
                ['bash'],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                env=env,
                universal_newlines=True,
                shell=False
            )
            
            with self.lock:
                self.terminals[session_id] = {
                    'master_fd': master_fd,
                    'slave_fd': slave_fd,
                    'process': process,
                    'thread': None,
                    'active': True
                }
            
            # Inicializar el terminal
            self.write_to_terminal(session_id, "export TERM=xterm-256color\nclear\n")
            
            return master_fd
            
        except Exception as e:
            print(f"Error creating terminal: {str(e)}")
            # Limpiar recursos en caso de error
            try:
                os.close(master_fd)
                os.close(slave_fd)
            except:
                pass
            raise

    def write_to_terminal(self, session_id, data):
        """Escribe datos al terminal"""
        with self.lock:
            if session_id in self.terminals and self.terminals[session_id]['active']:
                try:
                    master_fd = self.terminals[session_id]['master_fd']
                    if isinstance(data, str):
                        data = data.encode()
                    os.write(master_fd, data)
                except Exception as e:
                    print(f"Error writing to terminal {session_id}: {e}")
                    self.terminals[session_id]['active'] = False

    def read_from_terminal(self, session_id):
        """Lee datos del terminal"""
        with self.lock:
            if session_id in self.terminals and self.terminals[session_id]['active']:
                try:
                    master_fd = self.terminals[session_id]['master_fd']
                    ready, _, _ = select.select([master_fd], [], [], 0.1)
                    if ready:
                        data = os.read(master_fd, 1024)
                        return data.decode('utf-8', 'replace')
                except (OSError, IOError) as e:
                    if e.errno == 5:  # Input/output error (terminal cerrado)
                        self.terminals[session_id]['active'] = False
                    else:
                        print(f"Error reading from terminal {session_id}: {e}")
                except Exception as e:
                    print(f"Unexpected error reading from terminal {session_id}: {e}")
                    self.terminals[session_id]['active'] = False
        return None

    def resize_terminal(self, session_id, rows, cols):
        """Cambia el tamaño del terminal"""
        with self.lock:
            if session_id in self.terminals and self.terminals[session_id]['active']:
                try:
                    master_fd = self.terminals[session_id]['master_fd']
                    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, 
                              struct.pack('HHHH', rows, cols, 0, 0))
                except Exception as e:
                    print(f"Error resizing terminal {session_id}: {e}")
                    self.terminals[session_id]['active'] = False

    def close_terminal(self, session_id):
        """Cierra un terminal"""
        with self.lock:
            if session_id in self.terminals:
                terminal = self.terminals[session_id]
                try:
                    # Intentar terminar el proceso de manera limpia primero
                    if terminal['process'].poll() is None:
                        terminal['process'].terminate()
                        terminal['process'].wait(timeout=1)
                except:
                    # Si falla la terminación limpia, forzar
                    try:
                        terminal['process'].kill()
                    except:
                        pass
                
                # Cerrar descriptores de archivo
                try:
                    os.close(terminal['master_fd'])
                except:
                    pass
                try:
                    os.close(terminal['slave_fd'])
                except:
                    pass
                
                # Marcar como inactivo y eliminar
                terminal['active'] = False
                del self.terminals[session_id]

    def cleanup(self):
        """Limpia todos los terminales al cerrar"""
        for session_id in list(self.terminals.keys()):
            self.close_terminal(session_id)

class WebServer:
    """Servidor web para la interfaz gráfica"""
    def __init__(self, framework_interface):
        # Configurar directorios
        root_dir = Path(__file__).parent.parent
        static_folder = root_dir / 'static'
        
        # Inicializar Flask con configuración
        self.app = Flask(__name__, 
                        static_folder=str(static_folder),
                        static_url_path='/static')

        # Configuración adicional para Flask
        self.app.config['SECRET_KEY'] = 'secret!'  # Necesario para Flask-SocketIO
        self.app.config['DEBUG'] = True
        self.app.config['PROPAGATE_EXCEPTIONS'] = True
                        
        # Configurar Socket.IO
        self.socketio = SocketIO(
            self.app, 
            cors_allowed_origins="*",
            async_mode='eventlet',
            logger=True,
            engineio_logger=True
        )
                               
        self.framework = framework_interface
        self.pty_manager = PtyManager()
        
        # Configurar el contexto de la aplicación
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        self.setup_routes()
        self.setup_socketio_handlers()

    def setup_routes(self):
        """Configura las rutas de la API REST"""
        @self.app.route('/')
        def index():
            root_dir = Path(__file__).parent.parent
            return send_from_directory(str(root_dir), 'index.html')

        @self.app.route('/api/tools', methods=['GET'])
        def get_tools():
            try:
                tools = []
                for name, tool in self.framework.modules.items():
                    tools.append({
                        'name': tool.name,
                        'command': tool.command,
                        'description': tool.description,
                        'installed': tool.installed,
                        'dependencies': tool.dependencies,
                        'category': tool._get_category()
                    })
                return jsonify(tools)
            except Exception as e:
                print(f"Error in get_tools: {e}")
                return jsonify([])

        @self.app.route('/api/categories', methods=['GET'])
        def get_categories():
            try:
                categories = list(set(tool._get_category() for tool in self.framework.modules.values()))
                return jsonify(categories)
            except Exception as e:
                print(f"Error in get_categories: {e}")
                return jsonify([])

        @self.app.route('/api/sessions', methods=['GET'])
        def get_sessions():
            try:
                sessions = []
                if hasattr(self.framework, 'session_manager') and self.framework.session_manager:
                    for session_id, session in self.framework.session_manager.sessions.items():
                        sessions.append({
                            'id': session_id,
                            'name': session.name,
                            'active': session.active,
                            'history': session.command_history if hasattr(session, 'command_history') else [],
                            'tool': session.tool.name if session.tool else None
                        })
                return jsonify(sessions)
            except Exception as e:
                print(f"Error in get_sessions: {e}")
                return jsonify([])

        @self.app.route('/api/tool/<name>', methods=['POST'])
        def manage_tool(name):
            action = request.json.get('action')
            try:
                if action == 'install':
                    command = f"apt-get install -y {name}"
                elif action == 'remove':
                    command = f"apt-get remove -y {name}"
                elif action == 'update':
                    command = f"apt-get update && apt-get upgrade -y {name}"
                else:
                    return jsonify({'status': 'error', 'message': 'Invalid action'}), 400

                # Crear un nuevo terminal para la operación
                session_id = f"tool_{name}_{action}"
                master_fd = self.pty_manager.create_terminal(session_id)
                
                # Ejecutar el comando
                self.pty_manager.write_to_terminal(session_id, f"sudo {command}\n")
                
                return jsonify({
                    'status': 'success',
                    'session_id': session_id
                })
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

    def setup_socketio_handlers(self):
        """Configura los manejadores de Socket.IO"""
        @self.socketio.on('connect')
        def handle_connect():
            print('[*] Client connected to Socket.IO')

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('[*] Client disconnected from Socket.IO')

        @self.socketio.on('terminal_create')
        def handle_terminal_create(data):
            try:
                session_id = data.get('session_id', f"term_{len(self.pty_manager.terminals)}")
                master_fd = self.pty_manager.create_terminal(session_id)
                emit('terminal_created', {'session_id': session_id})
                
                # Iniciar thread para leer output
                def read_output():
                    while True:
                        output = self.pty_manager.read_from_terminal(session_id)
                        if output:
                            emit('terminal_output', {
                                'session_id': session_id,
                                'output': output
                            })
                
                thread = Thread(target=read_output)
                thread.daemon = True
                thread.start()
                
                self.pty_manager.terminals[session_id]['thread'] = thread
                
            except Exception as e:
                emit('terminal_error', {'error': str(e)})

        @self.socketio.on('terminal_input')
        def handle_terminal_input(data):
            try:
                session_id = data['session_id']
                input_data = data['input']
                self.pty_manager.write_to_terminal(session_id, input_data)
            except Exception as e:
                emit('terminal_error', {'error': str(e)})

        @self.socketio.on('terminal_resize')
        def handle_terminal_resize(data):
            try:
                session_id = data['session_id']
                rows = data['rows']
                cols = data['cols']
                self.pty_manager.resize_terminal(session_id, rows, cols)
            except Exception as e:
                emit('terminal_error', {'error': str(e)})

        @self.socketio.on('terminal_close')
        def handle_terminal_close(data):
            try:
                session_id = data['session_id']
                self.pty_manager.close_terminal(session_id)
                emit('terminal_closed', {'session_id': session_id})
            except Exception as e:
                emit('terminal_error', {'error': str(e)})

        @self.socketio.on('execute_tool')
        def handle_execute_tool(data):
            try:
                tool_name = data['tool']
                mode = data.get('mode', 'guided')
                
                # Crear un nuevo terminal para la herramienta
                session_id = f"tool_{tool_name}_{len(self.pty_manager.terminals)}"
                master_fd = self.pty_manager.create_terminal(session_id)
                
                # Preparar el comando de la herramienta
                tool = self.framework.modules.get(tool_name.lower())
                if tool:
                    try:
                        # Cambiar al directorio del framework
                        root_dir = Path(__file__).parent.parent
                        cmd = f"cd {root_dir} && "
                        
                        if mode == 'guided':
                            cmd += f"python3 -c 'import sys; sys.path.append(\"{root_dir}\"); "
                            cmd += f"from modules.{tool.__class__.__module__.split('.')[-1]} import {tool.__class__.__name__}; "
                            cmd += f"tool = {tool.__class__.__name__}(); tool.run_guided()'"
                        else:
                            cmd += f"python3 -c 'import sys; sys.path.append(\"{root_dir}\"); "
                            cmd += f"from modules.{tool.__class__.__module__.split('.')[-1]} import {tool.__class__.__name__}; "
                            cmd += f"tool = {tool.__class__.__name__}(); tool.run_direct()'"
                        
                        self.pty_manager.write_to_terminal(session_id, f"{cmd}\n")
                        emit('terminal_created', {'session_id': session_id})
                    except Exception as e:
                        print(f"Error executing tool: {e}")
                        emit('terminal_error', {'error': f'Error executing tool: {str(e)}'})
                else:
                    emit('terminal_error', {'error': f'Tool {tool_name} not found'})
                    
            except Exception as e:
                print(f"Error in handle_execute_tool: {e}")
                emit('terminal_error', {'error': str(e)})

    def start(self):
        """Inicia el servidor web"""
        try:
            print(f"\n[*] Starting web server...")
            print(f"[*] Static folder: {self.app.static_folder}")
            print(f"[*] Root directory: {Path(__file__).parent.parent}")
            
            # Verificar archivos necesarios
            root_dir = Path(__file__).parent.parent
            index_path = root_dir / 'index.html'
            if index_path.exists():
                print(f"[*] Found index.html")
            else:
                print(f"[!] Warning: index.html not found!")
                
            # Iniciar servidor
            self.socketio.run(
                self.app,
                host='0.0.0.0',
                port=5000,
                debug=True,
                use_reloader=False
            )
                            
        except Exception as e:
            print(f"[!] Error starting web server: {str(e)}")
            raise
            
    def __del__(self):
        """Limpieza al destruir el objeto"""
        # Limpiar el contexto de la aplicación
        try:
            self.app_context.pop()
        except Exception:
            pass
            
        # Cerrar todos los terminales
        for session_id in list(self.pty_manager.terminals.keys()):
            try:
                self.pty_manager.close_terminal(session_id)
            except Exception:
                pass