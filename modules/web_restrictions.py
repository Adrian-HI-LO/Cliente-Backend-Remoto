"""
Módulo de restricciones web
"""
import logging
import os
import platform
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class WebRestrictions:
    """Gestión de restricciones de acceso web"""
    
    def __init__(self):
        """Inicializar gestor de restricciones"""
        self.system = platform.system()
        self.hosts_file = self._get_hosts_file_path()
        self.blocked_sites = set()
        self._load_blocked_sites()
    
    def _get_hosts_file_path(self):
        """Obtener ruta del archivo hosts según el sistema operativo"""
        if self.system == 'Windows':
            return Path('C:/Windows/System32/drivers/etc/hosts')
        else:  # Linux y macOS
            return Path('/etc/hosts')
    
    def _load_blocked_sites(self):
        """Cargar sitios bloqueados desde el archivo hosts"""
        try:
            if not self.hosts_file.exists():
                logger.warning(f'Archivo hosts no encontrado: {self.hosts_file}')
                return
            
            with open(self.hosts_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Buscar líneas que redirijan a 127.0.0.1
                    if line.startswith('127.0.0.1') and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 2:
                            site = parts[1]
                            # Excluir localhost
                            if site != 'localhost':
                                self.blocked_sites.add(site)
            
            logger.info(f'Sitios bloqueados cargados: {len(self.blocked_sites)}')
            
        except PermissionError:
            logger.error('Permisos insuficientes para leer archivo hosts')
        except Exception as e:
            logger.error(f'Error cargando sitios bloqueados: {e}')
    
    def block_website(self, url):
        """
        Bloquear acceso a un sitio web
        
        Args:
            url: URL del sitio a bloquear (ej: 'facebook.com')
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Limpiar URL
            url = url.replace('http://', '').replace('https://', '')
            url = url.replace('www.', '').split('/')[0].strip()
            
            if not url:
                return {'success': False, 'error': 'URL inválida'}
            
            # Verificar si ya está bloqueado
            if url in self.blocked_sites:
                return {'success': True, 'message': 'Sitio ya bloqueado'}
            
            # Agregar entrada al archivo hosts
            redirect_line = f'127.0.0.1    {url}\n'
            www_redirect_line = f'127.0.0.1    www.{url}\n'
            
            with open(self.hosts_file, 'a') as f:
                f.write(redirect_line)
                f.write(www_redirect_line)
            
            self.blocked_sites.add(url)
            self.blocked_sites.add(f'www.{url}')
            
            # Limpiar caché DNS
            self._flush_dns_cache()
            
            logger.info(f'Sitio bloqueado: {url}')
            
            return {
                'success': True,
                'message': f'Sitio {url} bloqueado exitosamente',
                'url': url
            }
            
        except PermissionError:
            error_msg = 'Permisos insuficientes. Ejecutar como administrador/root'
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            logger.error(f'Error bloqueando sitio {url}: {e}')
            return {'success': False, 'error': str(e)}
    
    def unblock_website(self, url):
        """
        Desbloquear acceso a un sitio web
        
        Args:
            url: URL del sitio a desbloquear
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Limpiar URL
            url = url.replace('http://', '').replace('https://', '')
            url = url.replace('www.', '').split('/')[0].strip()
            
            if not url:
                return {'success': False, 'error': 'URL inválida'}
            
            # Verificar si está bloqueado
            if url not in self.blocked_sites and f'www.{url}' not in self.blocked_sites:
                return {'success': True, 'message': 'Sitio no estaba bloqueado'}
            
            # Leer archivo hosts
            with open(self.hosts_file, 'r') as f:
                lines = f.readlines()
            
            # Filtrar líneas que no contengan el sitio a desbloquear
            new_lines = []
            for line in lines:
                if url not in line and f'www.{url}' not in line:
                    new_lines.append(line)
                # Si la línea contiene el sitio pero está comentada, mantenerla
                elif line.strip().startswith('#'):
                    new_lines.append(line)
            
            # Escribir archivo sin las entradas del sitio
            with open(self.hosts_file, 'w') as f:
                f.writelines(new_lines)
            
            # Remover de lista de bloqueados
            self.blocked_sites.discard(url)
            self.blocked_sites.discard(f'www.{url}')
            
            # Limpiar caché DNS
            self._flush_dns_cache()
            
            logger.info(f'Sitio desbloqueado: {url}')
            
            return {
                'success': True,
                'message': f'Sitio {url} desbloqueado exitosamente',
                'url': url
            }
            
        except PermissionError:
            error_msg = 'Permisos insuficientes. Ejecutar como administrador/root'
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            logger.error(f'Error desbloqueando sitio {url}: {e}')
            return {'success': False, 'error': str(e)}
    
    def get_blocked_sites(self):
        """
        Obtener lista de sitios bloqueados
        
        Returns:
            Lista de sitios bloqueados
        """
        return list(self.blocked_sites)
    
    def block_multiple_sites(self, urls):
        """
        Bloquear múltiples sitios a la vez
        
        Args:
            urls: Lista de URLs a bloquear
            
        Returns:
            Dict con resultados por sitio
        """
        results = {
            'successful': [],
            'failed': [],
            'already_blocked': []
        }
        
        for url in urls:
            result = self.block_website(url)
            if result['success']:
                if 'ya bloqueado' in result.get('message', '').lower():
                    results['already_blocked'].append(url)
                else:
                    results['successful'].append(url)
            else:
                results['failed'].append({'url': url, 'error': result.get('error')})
        
        return results
    
    def unblock_all(self):
        """
        Desbloquear todos los sitios
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Obtener copia de sitios bloqueados
            sites_to_unblock = list(self.blocked_sites)
            
            unblocked_count = 0
            for site in sites_to_unblock:
                if not site.startswith('www.'):
                    result = self.unblock_website(site)
                    if result['success']:
                        unblocked_count += 1
            
            logger.info(f'Todos los sitios desbloqueados: {unblocked_count}')
            
            return {
                'success': True,
                'message': f'{unblocked_count} sitios desbloqueados',
                'count': unblocked_count
            }
            
        except Exception as e:
            logger.error(f'Error desbloqueando todos los sitios: {e}')
            return {'success': False, 'error': str(e)}
    
    def _flush_dns_cache(self):
        """Limpiar caché DNS según el sistema operativo"""
        try:
            if self.system == 'Windows':
                subprocess.run(['ipconfig', '/flushdns'], 
                              capture_output=True, check=True)
            elif self.system == 'Darwin':  # macOS
                subprocess.run(['dscacheutil', '-flushcache'],
                              capture_output=True, check=True)
                subprocess.run(['killall', '-HUP', 'mDNSResponder'],
                              capture_output=True, check=True)
            elif self.system == 'Linux':
                # Intentar diferentes métodos según el servicio DNS
                try:
                    subprocess.run(['systemctl', 'restart', 'systemd-resolved'],
                                  capture_output=True, check=True)
                except:
                    try:
                        subprocess.run(['systemctl', 'restart', 'nscd'],
                                      capture_output=True, check=True)
                    except:
                        pass
            
            logger.info('Caché DNS limpiado')
            
        except Exception as e:
            logger.warning(f'Error limpiando caché DNS: {e}')
