#!/bin/bash

# Script para ejecutar el cliente con permisos X11 adecuados
echo "Configurando permisos X11..."
export DISPLAY=:0
xhost +local: > /dev/null 2>&1

# Activar entorno virtual
echo "Activando entorno virtual..."
source Caja/bin/activate

# Verificar que se proporcionó la URL del servidor
if [ $# -eq 0 ]; then
    echo "Uso: $0 http://192.168.1.80:8000"
    echo "Ejemplo: $0 http://192.168.1.80:8000"
    exit 1
fi

# Ejecutar cliente
echo "Iniciando cliente de monitoreo..."
echo "Conectando a: $1"
python client.py "$1"
