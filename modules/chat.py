"""
Módulo de chat
"""
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class ChatManager:
    """Gestión de mensajes de chat"""
    
    def __init__(self, history_limit=100):
        """
        Inicializar gestor de chat
        
        Args:
            history_limit: Límite de mensajes en historial por conversación
        """
        self.history_limit = history_limit
        # Historial de mensajes: {(client1_id, client2_id): [mensajes]}
        self.chat_history = defaultdict(list)
        # Usuarios conectados
        self.online_users = set()
    
    def add_user(self, user_id):
        """Agregar usuario en línea"""
        self.online_users.add(user_id)
        logger.info(f'Usuario agregado al chat: {user_id}')
    
    def remove_user(self, user_id):
        """Remover usuario en línea"""
        if user_id in self.online_users:
            self.online_users.remove(user_id)
            logger.info(f'Usuario removido del chat: {user_id}')
    
    def is_user_online(self, user_id):
        """Verificar si usuario está en línea"""
        return user_id in self.online_users
    
    def get_conversation_key(self, user1_id, user2_id):
        """
        Obtener clave de conversación (siempre en el mismo orden)
        
        Args:
            user1_id: ID del primer usuario
            user2_id: ID del segundo usuario
            
        Returns:
            Tupla ordenada de IDs
        """
        return tuple(sorted([user1_id, user2_id]))
    
    def save_message(self, from_id, to_id, message, message_type='text'):
        """
        Guardar mensaje en el historial
        
        Args:
            from_id: ID del remitente
            to_id: ID del destinatario
            message: Contenido del mensaje
            message_type: Tipo de mensaje ('text', 'file', 'system')
            
        Returns:
            Dict con el mensaje guardado
        """
        conversation_key = self.get_conversation_key(from_id, to_id)
        
        msg_data = {
            'id': f"{from_id}_{to_id}_{datetime.now().timestamp()}",
            'from': from_id,
            'to': to_id,
            'message': message,
            'type': message_type,
            'timestamp': datetime.now().isoformat(),
            'read': False
        }
        
        # Agregar al historial
        self.chat_history[conversation_key].append(msg_data)
        
        # Limitar historial
        if len(self.chat_history[conversation_key]) > self.history_limit:
            self.chat_history[conversation_key] = \
                self.chat_history[conversation_key][-self.history_limit:]
        
        logger.info(f'Mensaje guardado: {from_id} -> {to_id}')
        
        return msg_data
    
    def get_conversation_history(self, user1_id, user2_id, limit=50):
        """
        Obtener historial de conversación
        
        Args:
            user1_id: ID del primer usuario
            user2_id: ID del segundo usuario
            limit: Cantidad máxima de mensajes a retornar
            
        Returns:
            Lista de mensajes
        """
        conversation_key = self.get_conversation_key(user1_id, user2_id)
        messages = self.chat_history.get(conversation_key, [])
        
        # Retornar los últimos 'limit' mensajes
        return messages[-limit:] if len(messages) > limit else messages
    
    def mark_as_read(self, user1_id, user2_id, message_id=None):
        """
        Marcar mensaje(s) como leído(s)
        
        Args:
            user1_id: ID del primer usuario
            user2_id: ID del segundo usuario
            message_id: ID específico del mensaje (opcional, None = todos)
        """
        conversation_key = self.get_conversation_key(user1_id, user2_id)
        
        if message_id:
            # Marcar mensaje específico
            for msg in self.chat_history[conversation_key]:
                if msg['id'] == message_id:
                    msg['read'] = True
                    break
        else:
            # Marcar todos como leídos
            for msg in self.chat_history[conversation_key]:
                msg['read'] = True
    
    def get_unread_count(self, user_id):
        """
        Obtener cantidad de mensajes no leídos para un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con contadores por conversación
        """
        unread = {}
        
        for conversation_key, messages in self.chat_history.items():
            if user_id in conversation_key:
                count = sum(1 for msg in messages 
                           if msg['to'] == user_id and not msg['read'])
                if count > 0:
                    other_user = [u for u in conversation_key if u != user_id][0]
                    unread[other_user] = count
        
        return unread
    
    def get_active_conversations(self, user_id):
        """
        Obtener conversaciones activas de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de conversaciones con último mensaje
        """
        conversations = []
        
        for conversation_key, messages in self.chat_history.items():
            if user_id in conversation_key and messages:
                other_user = [u for u in conversation_key if u != user_id][0]
                last_message = messages[-1]
                unread_count = sum(1 for msg in messages 
                                  if msg['to'] == user_id and not msg['read'])
                
                conversations.append({
                    'user_id': other_user,
                    'last_message': last_message,
                    'unread_count': unread_count,
                    'online': self.is_user_online(other_user)
                })
        
        # Ordenar por timestamp del último mensaje
        conversations.sort(
            key=lambda x: x['last_message']['timestamp'], 
            reverse=True
        )
        
        return conversations
    
    def delete_conversation(self, user1_id, user2_id):
        """
        Eliminar conversación completa
        
        Args:
            user1_id: ID del primer usuario
            user2_id: ID del segundo usuario
            
        Returns:
            Boolean indicando éxito
        """
        conversation_key = self.get_conversation_key(user1_id, user2_id)
        
        if conversation_key in self.chat_history:
            del self.chat_history[conversation_key]
            logger.info(f'Conversación eliminada: {conversation_key}')
            return True
        
        return False
    
    def broadcast_message(self, from_id, message):
        """
        Enviar mensaje a todos los usuarios conectados
        
        Args:
            from_id: ID del remitente
            message: Contenido del mensaje
            
        Returns:
            Lista de IDs de usuarios que recibieron el mensaje
        """
        recipients = []
        
        for user_id in self.online_users:
            if user_id != from_id:
                self.save_message(from_id, user_id, message, 'broadcast')
                recipients.append(user_id)
        
        logger.info(f'Mensaje broadcast enviado a {len(recipients)} usuarios')
        
        return recipients
