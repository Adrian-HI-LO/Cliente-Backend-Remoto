#!/usr/bin/env python3
"""
Sistema de control remoto - Versión AGRESIVA para Wayland
Usa interceptores de eventos que consumen datos directamente
"""
import os
import sys
import logging
import subprocess
import time
import glob
import signal
import threading

logger = logging.getLogger(__name__)

class RemoteControl:
    def __init__(self):
        self.system = 'Linux'
        self.keyboard_locked = False
        self.mouse_locked = False
        
        # Procesos interceptores
        self.keyboard_blocker_process = None
        self.mouse_blocker_process = None
        
        # Variables para Wayland
        self.wayland_session = self._detect_wayland()
        
        logger.info(f'RemoteControl inicializado para {self.system}')
        if self.wayland_session:
            logger.warning('Detectado entorno Wayland - usando métodos AGRESIVOS')

    def _detect_wayland(self):
        """Detectar si estamos en una sesión Wayland"""
        return (os.environ.get('XDG_SESSION_TYPE') == 'wayland' or 
                os.environ.get('WAYLAND_DISPLAY') is not None)

    def lock_keyboard(self):
        """Bloquear teclado usando método agresivo"""
        try:
            if self.keyboard_locked:
                return {'success': True, 'message': 'Teclado ya estaba bloqueado'}
            
            if self.wayland_session:
                return self._lock_keyboard_aggressive_wayland()
            else:
                return self._lock_keyboard_xinput()
                
        except Exception as e:
            logger.error(f'Error bloqueando teclado: {e}')
            return {'success': False, 'error': str(e)}

    def _lock_keyboard_aggressive_wayland(self):
        """Método agresivo para bloquear teclado en Wayland"""
        try:
            # Método 1: Proceso interceptor que consume eventos
            keyboard_devices = self._find_keyboard_devices()
            if not keyboard_devices:
                return {'success': False, 'error': 'No se encontraron dispositivos de teclado'}
            
            # Crear script interceptor
            interceptor_script = f'''#!/bin/bash
            
# Limpiar archivos previos
rm -f /tmp/keyboard_interceptor_pids

# Encontrar y abrir dispositivos de teclado
for device in {' '.join(keyboard_devices)}; do
    if [ -r "$device" ]; then
        echo "Interceptando $device"
        # Abrir y leer continuamente para consumir eventos
        evtest --grab "$device" > /dev/null 2>&1 &
        echo $! >> /tmp/keyboard_interceptor_pids
    fi
done

# Mantener vivo el interceptor
while true; do
    sleep 1
done
'''
            
            # Escribir script temporal
            script_path = '/tmp/keyboard_interceptor.sh'
            with open(script_path, 'w') as f:
                f.write(interceptor_script)
            
            os.chmod(script_path, 0o755)
            
            # Ejecutar interceptor
            self.keyboard_blocker_process = subprocess.Popen(
                ['sudo', 'bash', script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
            
            # Esperar un momento para que se establezca
            time.sleep(0.5)
            
            # Verificar que está corriendo
            if self.keyboard_blocker_process.poll() is None:
                self.keyboard_locked = True
                logger.info('Interceptor de teclado activado')
                return {
                    'success': True,
                    'method': 'wayland_aggressive_interceptor',
                    'blocked_devices': keyboard_devices,
                    'pid': self.keyboard_blocker_process.pid
                }
            else:
                return {'success': False, 'error': 'No se pudo iniciar interceptor'}
                
        except Exception as e:
            self._cleanup_keyboard_blocker()
            return {'success': False, 'error': f'Error interceptor: {e}'}

    def _lock_keyboard_xinput(self):
        """Bloquear teclado usando xinput en X11"""
        try:
            result = subprocess.run(['xinput', 'list'], capture_output=True, text=True)
            if result.returncode != 0:
                return {'success': False, 'error': 'xinput no disponible'}
            
            # Buscar dispositivos de teclado
            lines = result.stdout.split('\n')
            keyboard_ids = []
            
            for line in lines:
                if 'keyboard' in line.lower() and 'id=' in line:
                    try:
                        device_id = line.split('id=')[1].split()[0]
                        keyboard_ids.append(device_id)
                    except:
                        continue
            
            if not keyboard_ids:
                return {'success': False, 'error': 'No se encontraron teclados xinput'}
            
            # Deshabilitar dispositivos
            disabled = []
            for device_id in keyboard_ids:
                try:
                    subprocess.run(['xinput', 'disable', device_id], check=True)
                    disabled.append(device_id)
                    logger.info(f'Teclado xinput {device_id} deshabilitado')
                except:
                    continue
            
            if disabled:
                self.disabled_keyboards = disabled
                self.keyboard_locked = True
                return {'success': True, 'method': 'xinput', 'disabled_devices': disabled}
            else:
                return {'success': False, 'error': 'No se pudo deshabilitar ningún teclado'}
                
        except Exception as e:
            return {'success': False, 'error': f'Error xinput: {e}'}

    def unlock_keyboard(self):
        """Desbloquear teclado"""
        try:
            if not self.keyboard_locked:
                return {'success': True, 'message': 'Teclado ya estaba desbloqueado'}
            
            if self.wayland_session:
                self._cleanup_keyboard_blocker()
            else:
                # Restaurar dispositivos xinput
                if hasattr(self, 'disabled_keyboards'):
                    for device_id in self.disabled_keyboards:
                        try:
                            subprocess.run(['xinput', 'enable', device_id], check=True)
                            logger.info(f'Teclado xinput {device_id} habilitado')
                        except:
                            pass
                    self.disabled_keyboards = []
            
            self.keyboard_locked = False
            return {'success': True, 'message': 'Teclado desbloqueado'}
            
        except Exception as e:
            logger.error(f'Error desbloqueando teclado: {e}')
            return {'success': False, 'error': str(e)}

    def lock_mouse(self):
        """Bloquear mouse usando método agresivo"""
        try:
            if self.mouse_locked:
                return {'success': True, 'message': 'Mouse ya estaba bloqueado'}
            
            if self.wayland_session:
                return self._lock_mouse_aggressive_wayland()
            else:
                return self._lock_mouse_xinput()
                
        except Exception as e:
            logger.error(f'Error bloqueando mouse: {e}')
            return {'success': False, 'error': str(e)}

    def _lock_mouse_aggressive_wayland(self):
        """Método agresivo para bloquear mouse en Wayland"""
        try:
            # Encontrar dispositivos de mouse
            mouse_devices = self._find_mouse_devices()
            if not mouse_devices:
                return {'success': False, 'error': 'No se encontraron dispositivos de mouse'}
            
            # Crear script interceptor para mouse
            interceptor_script = f'''#!/bin/bash
            
# Limpiar archivos previos
rm -f /tmp/mouse_interceptor_pids

# Encontrar y abrir dispositivos de mouse
for device in {' '.join(mouse_devices)}; do
    if [ -r "$device" ]; then
        echo "Interceptando mouse $device"
        # Abrir y leer continuamente para consumir eventos
        evtest --grab "$device" > /dev/null 2>&1 &
        echo $! >> /tmp/mouse_interceptor_pids
    fi
done

# Mantener vivo el interceptor
while true; do
    sleep 1
done
'''
            
            # Escribir script temporal
            script_path = '/tmp/mouse_interceptor.sh'
            with open(script_path, 'w') as f:
                f.write(interceptor_script)
            
            os.chmod(script_path, 0o755)
            
            # Ejecutar interceptor
            self.mouse_blocker_process = subprocess.Popen(
                ['sudo', 'bash', script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
            
            # Esperar un momento
            time.sleep(0.5)
            
            # Verificar que está corriendo
            if self.mouse_blocker_process.poll() is None:
                self.mouse_locked = True
                logger.info('Interceptor de mouse activado')
                return {
                    'success': True,
                    'method': 'wayland_aggressive_mouse_interceptor',
                    'blocked_devices': mouse_devices,
                    'pid': self.mouse_blocker_process.pid
                }
            else:
                return {'success': False, 'error': 'No se pudo iniciar interceptor de mouse'}
                
        except Exception as e:
            self._cleanup_mouse_blocker()
            return {'success': False, 'error': f'Error interceptor mouse: {e}'}

    def _lock_mouse_xinput(self):
        """Bloquear mouse usando xinput"""
        try:
            result = subprocess.run(['xinput', 'list'], capture_output=True, text=True)
            if result.returncode != 0:
                return {'success': False, 'error': 'xinput no disponible'}
            
            # Buscar dispositivos de mouse
            lines = result.stdout.split('\n')
            mouse_ids = []
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ['mouse', 'pointer', 'touchpad']) and 'id=' in line:
                    try:
                        device_id = line.split('id=')[1].split()[0]
                        mouse_ids.append(device_id)
                    except:
                        continue
            
            if not mouse_ids:
                return {'success': False, 'error': 'No se encontraron dispositivos de mouse xinput'}
            
            # Deshabilitar dispositivos
            disabled = []
            for device_id in mouse_ids:
                try:
                    subprocess.run(['xinput', 'disable', device_id], check=True)
                    disabled.append(device_id)
                    logger.info(f'Mouse xinput {device_id} deshabilitado')
                except:
                    continue
            
            if disabled:
                self.disabled_mice = disabled
                self.mouse_locked = True
                return {'success': True, 'method': 'xinput_mouse', 'disabled_devices': disabled}
            else:
                return {'success': False, 'error': 'No se pudo deshabilitar ningún mouse'}
                
        except Exception as e:
            return {'success': False, 'error': f'Error xinput mouse: {e}'}

    def unlock_mouse(self):
        """Desbloquear mouse"""
        try:
            if not self.mouse_locked:
                return {'success': True, 'message': 'Mouse ya estaba desbloqueado'}
            
            if self.wayland_session:
                self._cleanup_mouse_blocker()
            else:
                # Restaurar dispositivos xinput
                if hasattr(self, 'disabled_mice'):
                    for device_id in self.disabled_mice:
                        try:
                            subprocess.run(['xinput', 'enable', device_id], check=True)
                            logger.info(f'Mouse xinput {device_id} habilitado')
                        except:
                            pass
                    self.disabled_mice = []
            
            self.mouse_locked = False
            return {'success': True, 'message': 'Mouse desbloqueado'}
            
        except Exception as e:
            logger.error(f'Error desbloqueando mouse: {e}')
            return {'success': False, 'error': str(e)}

    def _find_keyboard_devices(self):
        """Encontrar dispositivos de teclado"""
        event_devices = glob.glob('/dev/input/event*')
        keyboard_devices = []
        
        for device_path in event_devices:
            try:
                device_name_path = f'/sys/class/input/{os.path.basename(device_path)}/device/name'
                if os.path.exists(device_name_path):
                    with open(device_name_path, 'r') as f:
                        device_name = f.read().strip().lower()
                        
                    if any(keyword in device_name for keyword in ['keyboard', 'kbd', 'translated set']):
                        keyboard_devices.append(device_path)
                        logger.info(f'Dispositivo teclado encontrado: {device_path} ({device_name})')
                        
            except (FileNotFoundError, PermissionError, OSError):
                continue
        
        return keyboard_devices

    def _find_mouse_devices(self):
        """Encontrar dispositivos de mouse"""
        event_devices = glob.glob('/dev/input/event*')
        mouse_devices = []
        
        for device_path in event_devices:
            try:
                device_name_path = f'/sys/class/input/{os.path.basename(device_path)}/device/name'
                if os.path.exists(device_name_path):
                    with open(device_name_path, 'r') as f:
                        device_name = f.read().strip().lower()
                        
                    if any(keyword in device_name for keyword in ['mouse', 'optical', 'touchpad', 'pointer']):
                        mouse_devices.append(device_path)
                        logger.info(f'Dispositivo mouse encontrado: {device_path} ({device_name})')
                        
            except (FileNotFoundError, PermissionError, OSError):
                continue
        
        return mouse_devices

    def _cleanup_keyboard_blocker(self):
        """Limpiar procesos interceptores de teclado"""
        try:
            if self.keyboard_blocker_process:
                # Matar el proceso principal
                os.killpg(os.getpgid(self.keyboard_blocker_process.pid), signal.SIGTERM)
                self.keyboard_blocker_process = None
                logger.info('Proceso interceptor de teclado terminado')
            
            # Limpiar procesos cat que leen los dispositivos
            if os.path.exists('/tmp/keyboard_interceptor_pids'):
                with open('/tmp/keyboard_interceptor_pids', 'r') as f:
                    pids = f.read().strip().split('\n')
                
                for pid in pids:
                    if pid.strip():
                        try:
                            subprocess.run(['sudo', 'kill', '-9', pid.strip()], 
                                         check=False, capture_output=True)
                        except:
                            pass
                
                os.remove('/tmp/keyboard_interceptor_pids')
            
            # Limpiar script temporal
            if os.path.exists('/tmp/keyboard_interceptor.sh'):
                os.remove('/tmp/keyboard_interceptor.sh')
                
        except Exception as e:
            logger.error(f'Error limpiando interceptor de teclado: {e}')

    def _cleanup_mouse_blocker(self):
        """Limpiar procesos interceptores de mouse"""
        try:
            if self.mouse_blocker_process:
                # Matar el proceso principal
                os.killpg(os.getpgid(self.mouse_blocker_process.pid), signal.SIGTERM)
                self.mouse_blocker_process = None
                logger.info('Proceso interceptor de mouse terminado')
            
            # Limpiar procesos cat que leen los dispositivos
            if os.path.exists('/tmp/mouse_interceptor_pids'):
                with open('/tmp/mouse_interceptor_pids', 'r') as f:
                    pids = f.read().strip().split('\n')
                
                for pid in pids:
                    if pid.strip():
                        try:
                            subprocess.run(['sudo', 'kill', '-9', pid.strip()], 
                                         check=False, capture_output=True)
                        except:
                            pass
                
                os.remove('/tmp/mouse_interceptor_pids')
            
            # Limpiar script temporal
            if os.path.exists('/tmp/mouse_interceptor.sh'):
                os.remove('/tmp/mouse_interceptor.sh')
                
        except Exception as e:
            logger.error(f'Error limpiando interceptor de mouse: {e}')

    def shutdown_system(self, force=False):
        """Apagar el sistema"""
        try:
            subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
            return {'success': True, 'message': 'Sistema apagándose...'}
        except Exception as e:
            return {'success': False, 'error': str(e)}