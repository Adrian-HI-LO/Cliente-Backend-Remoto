"""
Módulo de control de red
"""
import logging
import platform
import subprocess
import socket
from ping3 import ping
import psutil

logger = logging.getLogger(__name__)


class NetworkControl:
    """Gestión de control de red y ping"""
    
    def __init__(self):
        """Inicializar controlador de red"""
        self.system = platform.system()
        self.ping_enabled = True
        self.firewall_rules = {}
    
    def test_ping(self, host, timeout=4, count=4):
        """
        Probar conectividad ping a un host
        
        Args:
            host: Host o IP a testear
            timeout: Tiempo de espera en segundos
            count: Cantidad de pings a enviar
            
        Returns:
            Dict con resultados del ping
        """
        try:
            results = []
            successful_pings = 0
            total_time = 0
            
            for i in range(count):
                try:
                    # Realizar ping
                    response_time = ping(host, timeout=timeout, unit='ms')
                    
                    if response_time is not None:
                        results.append({
                            'sequence': i + 1,
                            'time': round(response_time, 2),
                            'success': True
                        })
                        successful_pings += 1
                        total_time += response_time
                    else:
                        results.append({
                            'sequence': i + 1,
                            'time': None,
                            'success': False,
                            'error': 'Timeout'
                        })
                        
                except Exception as e:
                    results.append({
                        'sequence': i + 1,
                        'time': None,
                        'success': False,
                        'error': str(e)
                    })
            
            # Calcular estadísticas
            packet_loss = ((count - successful_pings) / count) * 100
            avg_time = total_time / successful_pings if successful_pings > 0 else 0
            
            return {
                'success': True,
                'host': host,
                'results': results,
                'statistics': {
                    'packets_sent': count,
                    'packets_received': successful_pings,
                    'packet_loss': round(packet_loss, 2),
                    'avg_time': round(avg_time, 2)
                }
            }
            
        except Exception as e:
            logger.error(f'Error en test de ping: {e}')
            return {
                'success': False,
                'host': host,
                'error': str(e)
            }
    
    def enable_ping(self):
        """
        Habilitar respuesta a ping (ICMP) - bidireccional
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            if self.system == 'Windows':
                # Habilitar regla de firewall para ICMP
                commands = [
                    # Eliminar reglas de bloqueo si existen
                    ['netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                     'name="ICMP Block incoming V4 echo request"'],
                    ['netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                     'name="ICMP Block outgoing V4 echo request"'],
                    # Agregar reglas de permitir
                    ['netsh', 'advfirewall', 'firewall', 'add', 'rule',
                     'name="ICMP Allow incoming V4 echo request"',
                     'protocol=icmpv4:8,any', 'dir=in', 'action=allow'],
                    ['netsh', 'advfirewall', 'firewall', 'add', 'rule',
                     'name="ICMP Allow outgoing V4 echo request"',
                     'protocol=icmpv4:8,any', 'dir=out', 'action=allow']
                ]
                
                for cmd in commands:
                    try:
                        subprocess.run(cmd, capture_output=True, check=False)
                    except:
                        pass
                    
            elif self.system == 'Linux':
                # Verificar si iptables está disponible
                try:
                    subprocess.run(['which', 'iptables'], capture_output=True, check=True)
                except subprocess.CalledProcessError:
                    return {'success': False, 'error': 'iptables no está disponible'}
                
                # Remover reglas de bloqueo (si existen) y permitir ICMP
                commands = [
                    # Remover reglas de bloqueo previas
                    ['sudo', 'iptables', '-D', 'INPUT', '-p', 'icmp', '--icmp-type',
                     'echo-request', '-j', 'DROP'],
                    ['sudo', 'iptables', '-D', 'OUTPUT', '-p', 'icmp', '--icmp-type',
                     'echo-request', '-j', 'DROP'],
                    # Agregar reglas de aceptación (si no existen)
                    ['sudo', 'iptables', '-I', 'INPUT', '1', '-p', 'icmp', '--icmp-type',
                     'echo-request', '-j', 'ACCEPT'],
                    ['sudo', 'iptables', '-I', 'OUTPUT', '1', '-p', 'icmp', '--icmp-type',
                     'echo-request', '-j', 'ACCEPT']
                ]
                
                for cmd in commands:
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        # No fallar si la regla no existe al eliminar
                        if result.returncode != 0 and '-D' not in cmd:
                            logger.warning(f'Comando falló: {" ".join(cmd)}, error: {result.stderr}')
                    except Exception as e:
                        logger.warning(f'Error ejecutando comando {cmd}: {e}')
                        
            elif self.system == 'Darwin':  # macOS
                # En macOS, usar pfctl
                try:
                    subprocess.run(['sudo', 'pfctl', '-d'], capture_output=True)
                except:
                    pass
            
            self.ping_enabled = True
            logger.info('Ping habilitado exitosamente (bidireccional)')
            
            return {
                'success': True,
                'message': 'Ping habilitado (entrada y salida)',
                'enabled': True
            }
            
        except subprocess.CalledProcessError as e:
            error_msg = f'Error ejecutando comando: {e}'
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except PermissionError:
            error_msg = 'Permisos insuficientes. Ejecutar como administrador/root'
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            logger.error(f'Error habilitando ping: {e}')
            return {'success': False, 'error': str(e)}
    
    def disable_ping(self):
        """
        Deshabilitar ping (ICMP) - bidireccional
        Bloquea tanto pings entrantes como salientes
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            if self.system == 'Windows':
                # Deshabilitar regla de firewall para ICMP bidireccional
                commands = [
                    # Eliminar reglas de permitir
                    ['netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                     'name="ICMP Allow incoming V4 echo request"'],
                    ['netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                     'name="ICMP Allow outgoing V4 echo request"'],
                    # Agregar reglas de bloqueo
                    ['netsh', 'advfirewall', 'firewall', 'add', 'rule',
                     'name="ICMP Block incoming V4 echo request"',
                     'protocol=icmpv4:8,any', 'dir=in', 'action=block'],
                    ['netsh', 'advfirewall', 'firewall', 'add', 'rule',
                     'name="ICMP Block outgoing V4 echo request"',
                     'protocol=icmpv4:8,any', 'dir=out', 'action=block']
                ]
                
                for cmd in commands:
                    try:
                        subprocess.run(cmd, capture_output=True, check=False)
                    except:
                        pass
                        
            elif self.system == 'Linux':
                # Verificar si iptables está disponible
                try:
                    subprocess.run(['which', 'iptables'], capture_output=True, check=True)
                except subprocess.CalledProcessError:
                    return {'success': False, 'error': 'iptables no está disponible'}
                
                # Bloquear ICMP bidireccional en iptables
                commands = [
                    # Remover reglas de aceptación previas
                    ['sudo', 'iptables', '-D', 'INPUT', '-p', 'icmp', '--icmp-type',
                     'echo-request', '-j', 'ACCEPT'],
                    ['sudo', 'iptables', '-D', 'OUTPUT', '-p', 'icmp', '--icmp-type',
                     'echo-request', '-j', 'ACCEPT'],
                    # Agregar reglas de bloqueo al inicio de las cadenas
                    ['sudo', 'iptables', '-I', 'INPUT', '1', '-p', 'icmp', '--icmp-type',
                     'echo-request', '-j', 'DROP'],
                    ['sudo', 'iptables', '-I', 'OUTPUT', '1', '-p', 'icmp', '--icmp-type',
                     'echo-request', '-j', 'DROP']
                ]
                
                for cmd in commands:
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        # No fallar si la regla no existe al eliminar
                        if result.returncode != 0 and '-D' not in cmd:
                            logger.warning(f'Comando falló: {" ".join(cmd)}, error: {result.stderr}')
                    except Exception as e:
                        logger.warning(f'Error ejecutando comando {cmd}: {e}')
                        
            elif self.system == 'Darwin':  # macOS
                # En macOS, configurar pfctl para bloquear ICMP
                try:
                    subprocess.run(['sudo', 'pfctl', '-e'], capture_output=True)
                except:
                    pass
            
            self.ping_enabled = False
            logger.info('Ping deshabilitado exitosamente (bidireccional)')
            
            return {
                'success': True,
                'message': 'Ping deshabilitado (entrada y salida)',
                'enabled': False
            }
            
        except subprocess.CalledProcessError as e:
            error_msg = f'Error ejecutando comando: {e}'
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except PermissionError:
            error_msg = 'Permisos insuficientes. Ejecutar como administrador/root'
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            logger.error(f'Error deshabilitando ping: {e}')
            return {'success': False, 'error': str(e)}
    
    def get_ping_status(self):
        """
        Obtener estado actual del ping verificando las reglas del firewall
        
        Returns:
            Dict con estado del ping
        """
        try:
            actual_status = self._check_actual_ping_status()
            return {
                'enabled': actual_status,
                'system': self.system,
                'internal_state': self.ping_enabled
            }
        except Exception as e:
            logger.error(f'Error verificando estado de ping: {e}')
            return {
                'enabled': self.ping_enabled,
                'system': self.system,
                'error': str(e)
            }
    
    def _check_actual_ping_status(self):
        """
        Verificar el estado real del ping consultando las reglas del firewall
        
        Returns:
            bool: True si ping está habilitado, False si está bloqueado
        """
        try:
            if self.system == 'Linux':
                # Verificar reglas de iptables
                result = subprocess.run(['sudo', 'iptables', '-L', '-n'], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    output = result.stdout
                    # Buscar reglas de DROP para ICMP
                    if 'DROP       icmp' in output and 'echo-request' in output:
                        return False
                    return True
                    
            elif self.system == 'Windows':
                # Verificar reglas de Windows Firewall
                result = subprocess.run(['netsh', 'advfirewall', 'firewall', 'show', 'rule',
                                       'name="ICMP Block incoming V4 echo request"'],
                                      capture_output=True, text=True)
                
                if result.returncode == 0 and 'Ok.' not in result.stdout:
                    return False
                return True
                
            # Para otros sistemas o si falla la verificación, usar estado interno
            return self.ping_enabled
            
        except Exception as e:
            logger.warning(f'No se pudo verificar estado real de ping: {e}')
            return self.ping_enabled
    
    def reset_ping_rules(self):
        """
        Limpiar todas las reglas de ping y restaurar estado por defecto
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            if self.system == 'Linux':
                # Remover todas las reglas relacionadas con ICMP
                commands = [
                    ['sudo', 'iptables', '-D', 'INPUT', '-p', 'icmp', '--icmp-type',
                     'echo-request', '-j', 'DROP'],
                    ['sudo', 'iptables', '-D', 'OUTPUT', '-p', 'icmp', '--icmp-type',
                     'echo-request', '-j', 'DROP'],
                    ['sudo', 'iptables', '-D', 'INPUT', '-p', 'icmp', '--icmp-type',
                     'echo-request', '-j', 'ACCEPT'],
                    ['sudo', 'iptables', '-D', 'OUTPUT', '-p', 'icmp', '--icmp-type',
                     'echo-request', '-j', 'ACCEPT']
                ]
                
                for cmd in commands:
                    try:
                        subprocess.run(cmd, capture_output=True)
                    except:
                        pass
                        
            elif self.system == 'Windows':
                # Remover todas las reglas de ICMP
                commands = [
                    ['netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                     'name="ICMP Allow incoming V4 echo request"'],
                    ['netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                     'name="ICMP Allow outgoing V4 echo request"'],
                    ['netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                     'name="ICMP Block incoming V4 echo request"'],
                    ['netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                     'name="ICMP Block outgoing V4 echo request"']
                ]
                
                for cmd in commands:
                    try:
                        subprocess.run(cmd, capture_output=True)
                    except:
                        pass
            
            # Restaurar estado por defecto (habilitado)
            self.ping_enabled = True
            logger.info('Reglas de ping reseteadas al estado por defecto')
            
            return {
                'success': True,
                'message': 'Reglas de ping reseteadas',
                'enabled': True
            }
            
        except Exception as e:
            logger.error(f'Error reseteando reglas de ping: {e}')
            return {'success': False, 'error': str(e)}
    
    def get_network_interfaces(self):
        """
        Obtener información de interfaces de red
        
        Returns:
            Lista con información de cada interfaz
        """
        try:
            interfaces = []
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()
            
            for interface_name, interface_addrs in addrs.items():
                interface_info = {
                    'name': interface_name,
                    'addresses': [],
                    'is_up': False,
                    'speed': 0
                }
                
                # Obtener direcciones
                for addr in interface_addrs:
                    if addr.family == socket.AF_INET:  # IPv4
                        interface_info['addresses'].append({
                            'type': 'IPv4',
                            'address': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast
                        })
                    elif addr.family == socket.AF_INET6:  # IPv6
                        interface_info['addresses'].append({
                            'type': 'IPv6',
                            'address': addr.address,
                            'netmask': addr.netmask
                        })
                
                # Obtener estadísticas
                if interface_name in stats:
                    stat = stats[interface_name]
                    interface_info['is_up'] = stat.isup
                    interface_info['speed'] = stat.speed
                
                interfaces.append(interface_info)
            
            return {
                'success': True,
                'interfaces': interfaces
            }
            
        except Exception as e:
            logger.error(f'Error obteniendo interfaces de red: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_network_stats(self):
        """
        Obtener estadísticas de tráfico de red
        
        Returns:
            Dict con estadísticas de red
        """
        try:
            io_counters = psutil.net_io_counters()
            
            return {
                'success': True,
                'stats': {
                    'bytes_sent': io_counters.bytes_sent,
                    'bytes_recv': io_counters.bytes_recv,
                    'packets_sent': io_counters.packets_sent,
                    'packets_recv': io_counters.packets_recv,
                    'errin': io_counters.errin,
                    'errout': io_counters.errout,
                    'dropin': io_counters.dropin,
                    'dropout': io_counters.dropout
                }
            }
            
        except Exception as e:
            logger.error(f'Error obteniendo estadísticas de red: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def resolve_hostname(self, hostname):
        """
        Resolver nombre de host a dirección IP
        
        Args:
            hostname: Nombre del host a resolver
            
        Returns:
            Dict con resultado
        """
        try:
            ip_address = socket.gethostbyname(hostname)
            
            return {
                'success': True,
                'hostname': hostname,
                'ip': ip_address
            }
            
        except socket.gaierror as e:
            return {
                'success': False,
                'hostname': hostname,
                'error': f'No se pudo resolver: {e}'
            }
        except Exception as e:
            return {
                'success': False,
                'hostname': hostname,
                'error': str(e)
            }