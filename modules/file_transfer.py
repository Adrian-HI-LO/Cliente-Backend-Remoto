"""
Módulo de transferencia de archivos
"""
import os
import base64
import logging
from pathlib import Path
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


class FileTransfer:
    """Gestión de transferencia de archivos"""
    
    def __init__(self, upload_folder='uploads'):
        """
        Inicializar módulo de transferencia
        
        Args:
            upload_folder: Carpeta donde guardar archivos subidos
        """
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
        
        # Extensiones permitidas
        self.allowed_extensions = {
            'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 
            'zip', 'rar', '7z', 'tar', 'gz',
            'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
            'mp4', 'avi', 'mkv', 'mp3', 'wav',
            'exe', 'msi', 'apk'
        }
    
    def is_allowed_file(self, filename):
        """
        Verificar si el archivo está permitido
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Boolean
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def save_file(self, filename, file_data, client_id):
        """
        Guardar archivo recibido
        
        Args:
            filename: Nombre del archivo
            file_data: Datos del archivo en base64
            client_id: ID del cliente que envía
            
        Returns:
            Dict con resultado
        """
        try:
            # Asegurar nombre de archivo
            safe_filename = secure_filename(filename)
            
            # Crear carpeta del cliente si no existe
            client_folder = os.path.join(self.upload_folder, client_id)
            os.makedirs(client_folder, exist_ok=True)
            
            # Ruta completa
            file_path = os.path.join(client_folder, safe_filename)
            
            # Decodificar y guardar
            file_bytes = base64.b64decode(file_data)
            
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            file_size = os.path.getsize(file_path)
            
            logger.info(f'Archivo guardado: {safe_filename} ({file_size} bytes) de {client_id}')
            
            return {
                'success': True,
                'filename': safe_filename,
                'path': file_path,
                'size': file_size
            }
        
        except Exception as e:
            logger.error(f'Error guardando archivo: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def read_file(self, filename, client_id=None):
        """
        Leer archivo para enviar
        
        Args:
            filename: Nombre del archivo
            client_id: ID del cliente (opcional, para archivos en carpeta de cliente)
            
        Returns:
            Dict con datos del archivo
        """
        try:
            # Determinar ruta
            if client_id:
                file_path = os.path.join(self.upload_folder, client_id, filename)
            else:
                file_path = os.path.join(self.upload_folder, filename)
            
            # Verificar que existe
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': 'Archivo no encontrado'
                }
            
            # Leer y encodear
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            file_base64 = base64.b64encode(file_data).decode('utf-8')
            file_size = os.path.getsize(file_path)
            
            logger.info(f'Archivo leído: {filename} ({file_size} bytes)')
            
            return {
                'success': True,
                'filename': filename,
                'data': file_base64,
                'size': file_size
            }
        
        except Exception as e:
            logger.error(f'Error leyendo archivo: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_files(self, client_id=None):
        """
        Listar archivos disponibles
        
        Args:
            client_id: ID del cliente (opcional)
            
        Returns:
            Lista de archivos
        """
        try:
            if client_id:
                folder_path = os.path.join(self.upload_folder, client_id)
            else:
                folder_path = self.upload_folder
            
            if not os.path.exists(folder_path):
                return []
            
            files = []
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    files.append({
                        'name': filename,
                        'size': os.path.getsize(file_path),
                        'modified': os.path.getmtime(file_path)
                    })
            
            return files
        
        except Exception as e:
            logger.error(f'Error listando archivos: {e}')
            return []
    
    def delete_file(self, filename, client_id=None):
        """
        Eliminar archivo
        
        Args:
            filename: Nombre del archivo
            client_id: ID del cliente (opcional)
            
        Returns:
            Dict con resultado
        """
        try:
            if client_id:
                file_path = os.path.join(self.upload_folder, client_id, filename)
            else:
                file_path = os.path.join(self.upload_folder, filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f'Archivo eliminado: {filename}')
                return {'success': True}
            else:
                return {'success': False, 'error': 'Archivo no encontrado'}
        
        except Exception as e:
            logger.error(f'Error eliminando archivo: {e}')
            return {'success': False, 'error': str(e)}
    
    def split_file_chunks(self, file_data, chunk_size=64 * 1024):
        """
        Dividir archivo en chunks para transmisión
        
        Args:
            file_data: Datos del archivo en bytes
            chunk_size: Tamaño de cada chunk (default 64KB)
            
        Returns:
            Lista de chunks
        """
        chunks = []
        for i in range(0, len(file_data), chunk_size):
            chunk = file_data[i:i + chunk_size]
            chunks.append(base64.b64encode(chunk).decode('utf-8'))
        return chunks
