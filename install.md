Te preparo un README.md mejorado que incluya la instalación global del framework:

```markdown
# HackConsole Framework

Un framework modular para gestión y ejecución de herramientas de seguridad en sistemas Linux.

## Características

- Gestión modular de herramientas
- Instalación y actualización automática de dependencias
- Modos guiado y directo para cada herramienta
- Interfaz de línea de comandos mejorada
- Soporte para múltiples distribuciones Linux

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu_usuario/hackconsole.git
cd hackconsole
```

### 2. Método de instalación recomendado (Entorno Virtual)

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar el entorno virtual
source venv/bin/activate  # En Linux/Mac
# o
.\venv\Scripts\activate  # En Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Instalación de dependencias del sistema

Según tu distribución Linux:

#### Debian/Ubuntu
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv
```

#### Fedora
```bash
sudo dnf update
sudo dnf install -y python3-pip python3-venv
```

#### Arch Linux
```bash
sudo pacman -Syu
sudo pacman -S python-pip python-virtualenv
```

### 4. Instalación global

Hay dos métodos para instalar HackConsole globalmente:

#### Método 1: Instalación en /opt (Recomendado)
```bash
# Crear directorio para la aplicación
sudo mkdir -p /opt/hackconsole

# Copiar el framework
sudo cp -r . /opt/hackconsole/

# Crear enlace simbólico
sudo ln -s /opt/hackconsole/main.py /usr/local/bin/hackconsole

# Configurar permisos
sudo chmod +x /usr/local/bin/hackconsole
sudo chmod -R 755 /opt/hackconsole
```
Para ejecutar hackconsole tendrás que hacerlo como sudo
```bash
sudo hackconsole
```

# Añadir alias al archivo de configuración de tu shell
echo "alias hackconsole='python3 $(pwd)/main.py'" >> ~/.bashrc
# O si usas zsh
echo "alias hackconsole='python3 $(pwd)/main.py'" >> ~/.zshrc

# Recargar la configuración
source ~/.bashrc  # O source ~/.zshrc

## Dependencias Python

Las siguientes dependencias se instalarán automáticamente con el requirements.txt:

- **psutil>=5.9.0**: Monitoreo del sistema
- **cmd2>=2.4.0**: Mejoras para la línea de comandos
- **colorama>=0.4.6**: Soporte de colores en la terminal
- **prompt_toolkit>=3.0.0**: Mejora del manejo de entrada

## Uso

Puedes iniciar el framework de dos maneras:

```bash
# Si instalaste globalmente
hackconsole

# O desde el directorio del proyecto
python3 main.py
```

## Estructura del proyecto

```
hackconsole/
├── core/           # Núcleo del framework
├── modules/        # Módulos de herramientas
├── scripts/        # Scripts de las herramientas
├── venv/          # Entorno virtual (si se usa)
├── main.py        # Punto de entrada
├── requirements.txt
└── README.md
```

## Añadir nuevas herramientas

1. Crear un nuevo módulo en la carpeta `modules/`
2. Implementar la clase del módulo heredando de `ToolModule`
3. Configurar los métodos requeridos
4. El framework detectará automáticamente el nuevo módulo

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia XYZ - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Tu Nombre - [@tu_twitter](https://twitter.com/tu_usuario)

Link del proyecto: [https://github.com/tu_usuario/hackconsole](https://github.com/tu_usuario/hackconsole)
```

