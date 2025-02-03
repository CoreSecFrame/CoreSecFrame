const { createApp } = Vue;

// Terminal Manager para manejar múltiples instancias de xterm.js
class TerminalManager {
    constructor(socket) {
        this.terminals = new Map();
        this.socket = socket;
    }

    async createTerminal(sessionId, containerId, options = {}) {
        // Crear terminal xterm.js
        const terminal = new Terminal({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: 'Menlo, Monaco, "Courier New", monospace',
            theme: {
                background: '#1e1e1e',
                foreground: '#ffffff'
            },
            ...options
        });

        // Añadir addons
        const fitAddon = new FitAddon.FitAddon();
        const webLinksAddon = new WebLinksAddon.WebLinksAddon();
        terminal.loadAddon(fitAddon);
        terminal.loadAddon(webLinksAddon);

        // Montar el terminal en el contenedor
        const container = document.getElementById(containerId);
        if (!container) {
            throw new Error(`Container ${containerId} not found`);
        }
        terminal.open(container);
        fitAddon.fit();

        // Configurar event listeners
        terminal.onData(data => {
            this.socket.emit('terminal_input', {
                session_id: sessionId,
                input: data
            });
        });

        // Manejar resize
        const resizeObserver = new ResizeObserver(() => {
            fitAddon.fit();
            this.socket.emit('terminal_resize', {
                session_id: sessionId,
                rows: terminal.rows,
                cols: terminal.cols
            });
        });
        resizeObserver.observe(container);

        // Guardar referencia del terminal
        this.terminals.set(sessionId, {
            terminal,
            fitAddon,
            resizeObserver
        });

        // Solicitar creación de terminal en el servidor
        this.socket.emit('terminal_create', { session_id: sessionId });

        return terminal;
    }

    closeTerminal(sessionId) {
        const terminalData = this.terminals.get(sessionId);
        if (terminalData) {
            const { terminal, resizeObserver } = terminalData;
            terminal.dispose();
            resizeObserver.disconnect();
            this.terminals.delete(sessionId);
            this.socket.emit('terminal_close', { session_id: sessionId });
        }
    }

    write(sessionId, data) {
        const terminalData = this.terminals.get(sessionId);
        if (terminalData) {
            terminalData.terminal.write(data);
        }
    }
}

// Vue Application
const app = createApp({
    data() {
        return {
            activeView: 'dashboard',
            loading: true,
            tools: [],
            sessions: [],
            categories: [],
            showToolModal: false,
            showSessionModal: false,
            selectedTool: null,
            selectedSession: null,
            executionMode: 'guided',
            activeTerminals: [],
            notifications: [],
            notificationId: 0,
            socket: null,
            terminalManager: null
        }
    },
    computed: {
        installedToolsCount() {
            return this.tools.filter(t => t.installed).length;
        },
        activeSessionsCount() {
            return this.sessions.filter(s => s.active).length;
        },
        totalTasks() {
            return this.sessions.reduce((acc, s) => acc + (s.history?.length || 0), 0);
        },
        sortedTools() {
            return [...this.tools].sort((a, b) => a.name.localeCompare(b.name));
        },
        sortedSessions() {
            return [...this.sessions].sort((a, b) => b.id - a.id);
        }
    },
    methods: {
        async initializeSocket() {
            this.socket = io();
            this.terminalManager = new TerminalManager(this.socket);

            // Socket.IO event handlers
            this.socket.on('connect', () => {
                console.log('Connected to server');
            });

            this.socket.on('terminal_output', (data) => {
                this.terminalManager.write(data.session_id, data.output);
            });

            this.socket.on('terminal_created', (data) => {
                console.log(`Terminal created: ${data.session_id}`);
            });

            this.socket.on('terminal_closed', (data) => {
                this.closeTerminal(data.session_id);
            });

            this.socket.on('terminal_error', (data) => {
                this.showNotification(data.error, 'error');
            });
        },

        async fetchData() {
            try {
                // Manejar cada petición individualmente
                try {
                    const toolsResponse = await fetch('/api/tools');
                    if (toolsResponse.ok) {
                        this.tools = await toolsResponse.json();
                    } else {
                        console.error('Error fetching tools:', toolsResponse.status);
                        this.tools = [];
                    }
                } catch (e) {
                    console.error('Error fetching tools:', e);
                    this.tools = [];
                }

                try {
                    const categoriesResponse = await fetch('/api/categories');
                    if (categoriesResponse.ok) {
                        this.categories = await categoriesResponse.json();
                    } else {
                        console.error('Error fetching categories:', categoriesResponse.status);
                        this.categories = [];
                    }
                } catch (e) {
                    console.error('Error fetching categories:', e);
                    this.categories = [];
                }

                try {
                    const sessionsResponse = await fetch('/api/sessions');
                    if (sessionsResponse.ok) {
                        this.sessions = await sessionsResponse.json();
                    } else {
                        console.error('Error fetching sessions:', sessionsResponse.status);
                        this.sessions = [];
                    }
                } catch (e) {
                    console.error('Error fetching sessions:', e);
                    this.sessions = [];
                }

                this.loading = false;
            } catch (error) {
                console.error('General error in fetchData:', error);
                this.showNotification('Some data could not be loaded', 'warning');
                this.loading = false;
            }
        },

        toggleView(view) {
            this.activeView = view;
        },

        getStatusClass(status) {
            return status ? 'text-green-600' : 'text-red-600';
        },

        async executeTool(toolName) {
            try {
                // Crear un nuevo terminal para la herramienta
                const sessionId = `tool_${toolName}_${Date.now()}`;
                const terminalId = `terminal-${sessionId}`;

                // Añadir terminal a la lista de activos
                this.activeTerminals.push({
                    sessionId,
                    title: `${toolName} - ${this.executionMode} mode`,
                    minimized: false
                });

                // Cerrar modal
                this.showToolModal = false;

                // En el próximo tick, cuando el DOM esté actualizado
                this.$nextTick(async () => {
                    // Crear terminal
                    await this.terminalManager.createTerminal(sessionId, terminalId);

                    // Ejecutar herramienta
                    this.socket.emit('execute_tool', {
                        tool: toolName,
                        mode: this.executionMode
                    });
                });
            } catch (error) {
                this.showNotification(`Error executing tool: ${error}`, 'error');
            }
        },

        async installTool(toolName) {
            try {
                // Crear terminal para la instalación
                const sessionId = `install_${toolName}_${Date.now()}`;
                const terminalId = `terminal-${sessionId}`;

                this.activeTerminals.push({
                    sessionId,
                    title: `Installing ${toolName}`,
                    minimized: false
                });

                this.$nextTick(async () => {
                    await this.terminalManager.createTerminal(sessionId, terminalId);
                    
                    const response = await fetch(`/api/tool/${toolName}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'install' })
                    });

                    if (!response.ok) {
                        throw new Error('Installation failed');
                    }

                    await this.fetchData();
                });
            } catch (error) {
                this.showNotification(`Error installing tool: ${error}`, 'error');
            }
        },

        async removeTool(toolName) {
            try {
                const sessionId = `remove_${toolName}_${Date.now()}`;
                const terminalId = `terminal-${sessionId}`;

                this.activeTerminals.push({
                    sessionId,
                    title: `Removing ${toolName}`,
                    minimized: false
                });

                this.$nextTick(async () => {
                    await this.terminalManager.createTerminal(sessionId, terminalId);
                    
                    const response = await fetch(`/api/tool/${toolName}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'remove' })
                    });

                    if (!response.ok) {
                        throw new Error('Removal failed');
                    }

                    await this.fetchData();
                });
            } catch (error) {
                this.showNotification(`Error removing tool: ${error}`, 'error');
            }
        },

        minimizeTerminal(sessionId) {
            const terminal = this.activeTerminals.find(t => t.sessionId === sessionId);
            if (terminal) {
                terminal.minimized = !terminal.minimized;
            }
        },

        closeTerminal(sessionId) {
            this.terminalManager.closeTerminal(sessionId);
            const index = this.activeTerminals.findIndex(t => t.sessionId === sessionId);
            if (index !== -1) {
                this.activeTerminals.splice(index, 1);
            }
        },

        showNotification(message, type = 'success') {
            const id = this.notificationId++;
            this.notifications.push({ id, message, type });
            setTimeout(() => {
                this.notifications = this.notifications.filter(n => n.id !== id);
            }, 3000);
        },

        closeModals() {
            this.showToolModal = false;
            this.showSessionModal = false;
        },

        async getToolDetails(toolName) {
            const tool = this.tools.find(t => t.name === toolName);
            if (tool) {
                this.selectedTool = tool;
                this.showToolModal = true;
            }
        },

        async getSessionDetails(sessionId) {
            const session = this.sessions.find(s => s.id === sessionId);
            if (session) {
                this.selectedSession = session;
                this.showSessionModal = true;
            }
        },

        toggleExecutionMode() {
            this.executionMode = this.executionMode === 'direct' ? 'guided' : 'direct';
        }
    },
    async created() {
        await this.initializeSocket();
        await this.fetchData();
        setInterval(this.fetchData, 5000);
    }
});

app.mount('#app');