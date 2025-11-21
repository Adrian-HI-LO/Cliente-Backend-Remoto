"""
Cliente de monitoreo - Agente
Script que se ejecuta en las PCs a monitorear
"""
import socketio
import logging
import sys
import base64
import os
import platform
from pathlib import Path
import threading

# Importar módulos locales
from modules.system_info import SystemInfo
from modules.remote_control import RemoteControl
from modules.file_transfer import FileTransfer
from modules.web_restrictions import WebRestrictions
from modules.network_control import NetworkControl
from client_gui import ClientGUI

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cliente SocketIO
sio = socketio.Client()

# Instancias de módulos
system_info = SystemInfo()
remote_control = RemoteControl()
file_transfer = FileTransfer()
web_restrictions = WebRestrictions()
network_control = NetworkControl()

# Configuración del cliente
CLIENT_ID = None
SERVER_URL = 'http://localhost:8080'

# GUI
gui = None


def get_client_id():
    """Generar ID único del cliente basado en información del sistema"""
    global CLIENT_ID
    if CLIENT_ID:
        return CLIENT_ID
    
    # Usar nombre del host + dirección MAC
    import uuid
    hostname = platform.node()
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                    for elements in range(0, 2*6, 8)][::-1])
    
    CLIENT_ID = f"{hostname}_{mac[-8:]}"
    return CLIENT_ID


# ============= Eventos de conexión =============

@sio.event
def connect():
    """Evento cuando se conecta al servidor"""
    logger.info(f'Conectado al servidor: {SERVER_URL}')
    
    # Notificar a la GUI
    if gui:
        gui.display_system_message("✅ Conectado al servidor")
    
    # Registrar cliente con el servidor
    import getpass
    from datetime import datetime
    
    client_id = get_client_id()
    ip_address = system_info.get_ip_address()
    
    sio.emit('register_client', {
        'name': platform.node(),  # Nombre de la PC
        'ip': ip_address,  # IP del cliente
        'os': f"{platform.system()} {platform.release()}",  # Sistema operativo
        'user': getpass.getuser(),  # Usuario actual
        'connected_at': datetime.now().isoformat()  # Timestamp
    })


@sio.event
def disconnect():
    """Evento cuando se desconecta del servidor"""
    logger.info('Desconectado del servidor')
    
    # Notificar a la GUI
    if gui:
        gui.display_system_message("❌ Desconectado del servidor")


@sio.event
def connect_error(data):
    """Evento cuando hay error de conexión"""
    logger.error(f'Error de conexión: {data}')
    
    # Notificar a la GUI
    if gui:
        gui.display_system_message(f"⚠️  Error de conexión: {data}")


# ============= Control remoto =============

@sio.on('request_screenshot')
def on_request_screenshot(data):
    """Capturar y enviar screenshot"""
    try:
        logger.info('Capturando screenshot...')
        
        quality = data.get('quality', 80)
        scale = data.get('scale', 1.0)
        
        # Capturar screenshot
        screenshot_b64 = remote_control.capture_screenshot(quality, scale)
        
        # Enviar al servidor
        sio.emit('screenshot_data', {
            'client_id': get_client_id(),
            'screenshot': screenshot_b64,
            'timestamp': system_info.get_system_stats().get('uptime')
        })
        
        logger.info('Screenshot enviado')
        
    except Exception as e:
        logger.error(f'Error capturando screenshot: {e}')
        sio.emit('screenshot_error', {
            'client_id': get_client_id(),
            'error': str(e)
        })


@sio.on('start_screen_stream')
def on_start_screen_stream(data):
    """Iniciar streaming de pantalla"""
    import threading
    import time
    
    def stream_screen():
        fps = data.get('fps', 10)
        quality = data.get('quality', 60)
        scale = data.get('scale', 0.5)
        interval = 1.0 / fps
        
        logger.info(f'Iniciando stream de pantalla - FPS: {fps}')
        
        while True:
            try:
                screenshot_b64 = remote_control.capture_screenshot(quality, scale)
                
                sio.emit('screen_frame', {
                    'client_id': get_client_id(),
                    'frame': screenshot_b64
                })
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f'Error en stream: {e}')
                break
    
    # Ejecutar en thread separado
    thread = threading.Thread(target=stream_screen, daemon=True)
    thread.start()


@sio.on('lock_keyboard')
def on_lock_keyboard(data):
    """Bloquear teclado"""
    try:
        result = remote_control.lock_keyboard()
        
        if result.get('success'):
            logger.info(f'Teclado bloqueado exitosamente - Método: {result.get("method", "default")}')
        else:
            logger.error(f'Error bloqueando teclado: {result.get("error", "Error desconocido")}')
        
        sio.emit('keyboard_locked', {
            'client_id': get_client_id(),
            'success': result.get('success', False),
            'message': result.get('message', result.get('error', '')),
            'details': result
        })
        
    except Exception as e:
        logger.error(f'Excepción bloqueando teclado: {e}')
        sio.emit('keyboard_locked', {
            'client_id': get_client_id(),
            'success': False,
            'error': str(e)
        })


@sio.on('unlock_keyboard')
def on_unlock_keyboard(data):
    """Desbloquear teclado"""
    try:
        result = remote_control.unlock_keyboard()
        
        if result.get('success'):
            logger.info(f'Teclado desbloqueado exitosamente')
        else:
            logger.error(f'Error desbloqueando teclado: {result.get("error", "Error desconocido")}')
        
        sio.emit('keyboard_unlocked', {
            'client_id': get_client_id(),
            'success': result.get('success', False),
            'message': result.get('message', result.get('error', '')),
            'details': result
        })
        
    except Exception as e:
        logger.error(f'Excepción desbloqueando teclado: {e}')
        sio.emit('keyboard_unlocked', {
            'client_id': get_client_id(),
            'success': False,
            'error': str(e)
        })


@sio.on('lock_mouse')
def on_lock_mouse(data):
    """Bloquear mouse"""
    try:
        result = remote_control.lock_mouse()
        
        if result.get('success'):
            logger.info(f'Mouse bloqueado exitosamente - Método: {result.get("method", "default")}')
        else:
            logger.error(f'Error bloqueando mouse: {result.get("error", "Error desconocido")}')
        
        sio.emit('mouse_locked', {
            'client_id': get_client_id(),
            'success': result.get('success', False),
            'message': result.get('message', result.get('error', '')),
            'details': result
        })
        
    except Exception as e:
        logger.error(f'Error bloqueando mouse: {e}')


@sio.on('unlock_mouse')
def on_unlock_mouse(data):
    """Desbloquear mouse"""
    try:
        result = remote_control.unlock_mouse()
        
        if result.get('success'):
            logger.info(f'Mouse desbloqueado exitosamente')
        else:
            logger.error(f'Error desbloqueando mouse: {result.get("error", "Error desconocido")}')
        
        sio.emit('mouse_unlocked', {
            'client_id': get_client_id(),
            'success': result.get('success', False),
            'message': result.get('message', result.get('error', '')),
            'details': result
        })
        
    except Exception as e:
        logger.error(f'Excepción desbloqueando mouse: {e}')
        sio.emit('mouse_unlocked', {
            'client_id': get_client_id(),
            'success': False,
            'error': str(e)
        })


@sio.on('get_input_status')
def on_get_input_status(data):
    """Obtener estado actual de bloqueo de entrada"""
    try:
        status = remote_control.get_input_status()
        
        sio.emit('input_status', {
            'client_id': get_client_id(),
            'status': status,
            'success': True
        })
        
        logger.info(f'Estado de entrada enviado: teclado={status["keyboard_locked"]}, mouse={status["mouse_locked"]}')
        
    except Exception as e:
        logger.error(f'Error obteniendo estado de entrada: {e}')
        sio.emit('input_status', {
            'client_id': get_client_id(),
            'success': False,
            'error': str(e)
        })


@sio.on('emergency_unlock_all')
def on_emergency_unlock_all(data):
    """Desbloqueo de emergencia de teclado y mouse"""
    try:
        results = remote_control.emergency_unlock_all()
        
        logger.warning('Desbloqueo de emergencia solicitado')
        
        sio.emit('emergency_unlock_complete', {
            'client_id': get_client_id(),
            'results': results
        })
        
    except Exception as e:
        logger.error(f'Error en desbloqueo de emergencia: {e}')
        sio.emit('emergency_unlock_complete', {
            'client_id': get_client_id(),
            'success': False,
            'error': str(e)
        })


@sio.on('diagnose_input_devices')
def on_diagnose_input_devices(data):
    """Diagnosticar dispositivos de entrada"""
    try:
        diagnosis = remote_control.diagnose_input_devices()
        
        sio.emit('input_devices_diagnosis', {
            'client_id': get_client_id(),
            'diagnosis': diagnosis,
            'success': True
        })
        
        logger.info(f'Diagnóstico enviado: {len(diagnosis.get("devices", {}).get("keyboards", []))} teclados, {len(diagnosis.get("devices", {}).get("mice", []))} dispositivos pointer')
        
    except Exception as e:
        logger.error(f'Error en diagnóstico: {e}')
        sio.emit('input_devices_diagnosis', {
            'client_id': get_client_id(),
            'success': False,
            'error': str(e)
        })


@sio.on('shutdown_pc')
def on_shutdown_pc(data):
    """Apagar PC"""
    try:
        force = data.get('force', False)
        logger.warning(f'Apagando PC (force={force})...')
        
        sio.emit('pc_shutting_down', {
            'client_id': get_client_id()
        })
        
        # Ejecutar shutdown
        remote_control.shutdown_system(force)
        
    except Exception as e:
        logger.error(f'Error apagando PC: {e}')


@sio.on('restart_pc')
def on_restart_pc(data):
    """Reiniciar PC"""
    try:
        force = data.get('force', False)
        logger.warning(f'Reiniciando PC (force={force})...')
        
        sio.emit('pc_restarting', {
            'client_id': get_client_id()
        })
        
        # Ejecutar restart
        remote_control.restart_system(force)
        
    except Exception as e:
        logger.error(f'Error reiniciando PC: {e}')


# ============= Información del sistema =============

@sio.on('request_system_info')
def on_request_system_info(data):
    """Enviar información del sistema"""
    try:
        stats = system_info.get_system_stats()
        
        sio.emit('system_info_response', {
            'client_id': get_client_id(),
            'stats': stats
        })
        
        logger.info('Información del sistema enviada')
        
    except Exception as e:
        logger.error(f'Error obteniendo info del sistema: {e}')


# ============= Transferencia de archivos =============

@sio.on('request_file_transfer')
def on_request_file_transfer(data):
    """Manejar transferencia de archivo"""
    try:
        direction = data.get('direction')  # 'upload' o 'download'
        filename = data.get('filename')
        
        if direction == 'download':
            # Servidor quiere descargar archivo de este cliente
            file_data = file_transfer.read_file(filename, get_client_id())
            
            if file_data:
                # Enviar en chunks
                chunks = file_transfer.split_file_chunks(file_data)
                total_chunks = len(chunks)
                
                for i, chunk in enumerate(chunks):
                    sio.emit('file_chunk', {
                        'client_id': get_client_id(),
                        'filename': filename,
                        'chunk_index': i,
                        'total_chunks': total_chunks,
                        'data': chunk
                    })
                
                logger.info(f'Archivo enviado: {filename} ({total_chunks} chunks)')
        
    except Exception as e:
        logger.error(f'Error en transferencia de archivo: {e}')


@sio.on('file_chunk')
def on_file_chunk(data):
    """Recibir chunk de archivo del servidor"""
    try:
        filename = data.get('filename')
        chunk_index = data.get('chunk_index')
        total_chunks = data.get('total_chunks')
        chunk_data = data.get('data')
        
        # Guardar chunk (acumular en memoria o disco temporal)
        # Implementar lógica de ensamblaje de chunks
        
        if chunk_index == total_chunks - 1:
            # Último chunk - guardar archivo completo
            logger.info(f'Archivo recibido: {filename}')
            
            sio.emit('file_transfer_complete', {
                'client_id': get_client_id(),
                'filename': filename
            })
        
    except Exception as e:
        logger.error(f'Error recibiendo chunk: {e}')


# ============= Chat =============

@sio.on('chat_message')
def on_chat_message(data):
    """Recibir mensaje de chat del servidor"""
    try:
        message = data.get('message')
        from_user = data.get('from', 'Server')
        timestamp = data.get('timestamp', '')
        
        logger.info(f'Mensaje de {from_user}: {message}')
        
        # Notificar a la GUI
        if gui:
            # Parsear timestamp si es ISO format
            if timestamp:
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime("%H:%M:%S")
                except:
                    pass
            gui.display_message(from_user, message, timestamp, is_client=False)
        
        # Enviar confirmación de lectura
        sio.emit('message_read', {
            'client_id': get_client_id(),
            'message_id': data.get('message_id')
        })
    except Exception as e:
        logger.error(f'Error recibiendo mensaje: {e}')

def send_message_to_server(message):
    """Enviar mensaje al servidor"""
    try:
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        
        sio.emit('client_message', {
            'message': message,
            'timestamp': timestamp,
            'client_id': get_client_id()
        })
        
        logger.info(f'Mensaje enviado al servidor: {message}')
        return True
    except Exception as e:
        logger.error(f'Error enviando mensaje: {e}')
        return False
        
    except Exception as e:
        logger.error(f'Error procesando mensaje: {e}')


@sio.on('request_chat_response')
def on_request_chat_response(data):
    """Servidor solicita respuesta al mensaje"""
    # Aquí se podría implementar auto-respuesta o
    # interfaz para que el usuario responda
    pass


# ============= Restricciones web =============

@sio.on('block_website')
def on_block_website(data):
    """Bloquear sitio web"""
    try:
        url = data.get('url')
        result = web_restrictions.block_website(url)
        
        sio.emit('website_blocked', {
            'client_id': get_client_id(),
            'url': url,
            'success': result.get('success'),
            'message': result.get('message', result.get('error'))
        })
        
        logger.info(f'Sitio bloqueado: {url}')
        
    except Exception as e:
        logger.error(f'Error bloqueando sitio: {e}')


@sio.on('unblock_website')
def on_unblock_website(data):
    """Desbloquear sitio web"""
    try:
        url = data.get('url')
        result = web_restrictions.unblock_website(url)
        
        sio.emit('website_unblocked', {
            'client_id': get_client_id(),
            'url': url,
            'success': result.get('success'),
            'message': result.get('message', result.get('error'))
        })
        
        logger.info(f'Sitio desbloqueado: {url}')
        
    except Exception as e:
        logger.error(f'Error desbloqueando sitio: {e}')


# ============= Control de red =============

@sio.on('set_ping_status')
def on_set_ping_status(data):
    """Habilitar/deshabilitar ping"""
    try:
        enabled = data.get('enabled')
        
        if enabled:
            result = network_control.enable_ping()
        else:
            result = network_control.disable_ping()
        
        sio.emit('ping_status_changed', {
            'client_id': get_client_id(),
            'enabled': enabled,
            'success': result.get('success')
        })
        
        logger.info(f'Ping {"habilitado" if enabled else "deshabilitado"}')
        
    except Exception as e:
        logger.error(f'Error cambiando estado de ping: {e}')


@sio.on('ping_test')
def on_ping_test(data):
    """Realizar test de ping"""
    try:
        host = data.get('host')
        result = network_control.test_ping(host)
        
        sio.emit('ping_test_result', {
            'client_id': get_client_id(),
            'result': result
        })
        
        logger.info(f'Ping test a {host} completado')
        
    except Exception as e:
        logger.error(f'Error en ping test: {e}')


# ============= Función principal =============

def main():
    """Iniciar cliente con GUI"""
    global gui
    
    try:
        # Obtener URL del servidor de argumentos o variable de entorno
        server_url = os.getenv('MONITOR_SERVER_URL', SERVER_URL)
        
        if len(sys.argv) > 1:
            server_url = sys.argv[1]
        
        logger.info(f'Iniciando cliente de monitoreo...')
        logger.info(f'ID del cliente: {get_client_id()}')
        logger.info(f'Conectando a servidor: {server_url}')
        
        # Crear GUI
        gui = ClientGUI(send_message_to_server)
        gui.setup_gui()
        
        # Conectar al servidor en un thread separado
        def connect_to_server():
            try:
                sio.connect(server_url)
                sio.wait()
            except Exception as e:
                logger.error(f'Error en conexión SocketIO: {e}')
                if gui and gui.root:
                    gui.display_system_message(f"❌ Error de conexión: {e}")
        
        # Iniciar conexión en thread
        socket_thread = threading.Thread(target=connect_to_server, daemon=True)
        socket_thread.start()
        
        # Iniciar GUI (bloquea hasta que se cierre)
        gui.run()
        
        # Al cerrar la GUI, desconectar socket
        logger.info('GUI cerrada, desconectando...')
        sio.disconnect()
        
    except KeyboardInterrupt:
        logger.info('Cliente detenido por el usuario')
        if sio.connected:
            sio.disconnect()
    except Exception as e:
        logger.error(f'Error en cliente: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
