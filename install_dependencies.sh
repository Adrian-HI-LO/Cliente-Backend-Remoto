#!/bin/bash

# Script de instalación de dependencias del backend
# Sistema de Monitoreo Remoto

echo "======================================"
echo "Instalación de Backend - Sistema de Monitoreo"
echo "======================================"
echo ""

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    echo "Por favor instala Python 3.8 o superior"
    exit 1
fi

echo "✓ Python encontrado: $(python3 --version)"
echo ""

# Verificar si estamos en un entorno virtual
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✓ Entorno virtual activo: $VIRTUAL_ENV"
else
    echo "⚠️  Advertencia: No se detectó entorno virtual activo"
    echo "Se recomienda usar un entorno virtual (venv)"
    echo ""
    read -p "¿Continuar de todas formas? (s/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "Instalación cancelada"
        exit 1
    fi
fi

echo ""
echo "======================================"
echo "Instalando dependencias..."
echo "======================================"
echo ""

# Actualizar pip
echo "→ Actualizando pip..."
python3 -m pip install --upgrade pip

# Instalar dependencias
echo ""
echo "→ Instalando Flask y extensiones..."
pip install flask==3.0.0
pip install flask-socketio==5.3.5
pip install flask-cors==4.0.0

echo ""
echo "→ Instalando SocketIO..."
pip install python-socketio==5.10.0
pip install setuptools
pip install eventlet==0.35.2

echo ""
echo "→ Instalando bibliotecas de control..."
pip install pyautogui==0.9.54
pip install Pillow==10.1.0
pip install mss==9.0.1

echo ""
echo "→ Instalando bibliotecas de sistema..."
pip install psutil==5.9.6
pip install netifaces==0.11.0
pip install ping3==4.0.4

echo ""
echo "→ Instalando utilidades..."
pip install python-dotenv==1.0.0
pip install werkzeug==3.0.1
pip install cryptography==41.0.7

echo ""
echo "======================================"
echo "Verificando instalación..."
echo "======================================"
echo ""

# Verificar cada paquete
packages=(
    "flask"
    "flask_socketio"
    "flask_cors"
    "socketio"
    "eventlet"
    "pyautogui"
    "PIL"
    "mss"
    "psutil"
    "netifaces"
    "ping3"
    "dotenv"
    "werkzeug"
    "cryptography"
)

all_installed=true

for package in "${packages[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        echo "✓ $package instalado correctamente"
    else
        echo "❌ Error: $package NO se instaló correctamente"
        all_installed=false
    fi
done

echo ""
echo "======================================"

if [ "$all_installed" = true ]; then
    echo "✅ Instalación completada exitosamente!"
    echo ""
    echo "Siguiente paso:"
    echo "  python app.py"
    echo ""
    echo "Para instalar el cliente en otra PC:"
    echo "  python client.py"
else
    echo "⚠️  Instalación completada con errores"
    echo "Revisa los mensajes de error arriba"
fi

echo "======================================"
