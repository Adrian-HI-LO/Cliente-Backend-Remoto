"""
Módulo de información del sistema
"""
import psutil
import platform
import socket
from datetime import datetime


class SystemInfo:
    """Obtener información del sistema"""
    
    @staticmethod
    def get_system_stats():
        """Obtener estadísticas del sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memoria
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_total = memory.total / (1024 ** 3)  # GB
            memory_used = memory.used / (1024 ** 3)    # GB
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_total = disk.total / (1024 ** 3)  # GB
            disk_used = disk.used / (1024 ** 3)    # GB
            
            # Red
            net_io = psutil.net_io_counters()
            
            # Sistema
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = str(datetime.now() - boot_time).split('.')[0]
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'percent': memory_percent,
                    'total_gb': round(memory_total, 2),
                    'used_gb': round(memory_used, 2)
                },
                'disk': {
                    'percent': disk_percent,
                    'total_gb': round(disk_total, 2),
                    'used_gb': round(disk_used, 2)
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv
                },
                'system': {
                    'platform': platform.system(),
                    'release': platform.release(),
                    'version': platform.version(),
                    'machine': platform.machine(),
                    'processor': platform.processor(),
                    'hostname': socket.gethostname(),
                    'uptime': uptime
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_ip_address():
        """Obtener dirección IP del servidor"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    @staticmethod
    def get_network_interfaces():
        """Obtener interfaces de red"""
        try:
            import netifaces
            interfaces = []
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        interfaces.append({
                            'interface': interface,
                            'ip': addr['addr'],
                            'netmask': addr.get('netmask', '')
                        })
            return interfaces
        except ImportError:
            return []
        except Exception as e:
            return {'error': str(e)}
