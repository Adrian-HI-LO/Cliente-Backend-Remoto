"""
GUI para el cliente de monitoreo
Interfaz gráfica con Tkinter para mostrar mensajes y enviar mensajes al servidor
"""
import tkinter as tk
from tkinter import scrolledtext, messagebox
from datetime import datetime
import threading


class ClientGUI:
    """Interfaz gráfica para el cliente"""
    
    def __init__(self, send_message_callback):
        """
        Inicializar GUI
        
        Args:
            send_message_callback: Función para enviar mensajes al servidor
        """
        self.send_message_callback = send_message_callback
        self.root = None
        self.chat_display = None
        self.message_entry = None
        
    def setup_gui(self):
        """Configurar la interfaz gráfica"""
        self.root = tk.Tk()
        self.root.title("Cliente de Monitoreo - Chat")
        self.root.geometry("600x500")
        self.root.configure(bg="#2c3e50")
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_label = tk.Label(
            main_frame,
            text="💬 Chat con Servidor",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        title_label.pack(pady=(0, 10))
        
        # Área de mensajes
        chat_frame = tk.Frame(main_frame, bg="#34495e", relief=tk.SUNKEN, bd=2)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # ScrolledText para mostrar mensajes
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            width=70,
            height=20,
            font=("Courier", 10),
            bg="#ecf0f1",
            fg="#2c3e50",
            state=tk.DISABLED,
            relief=tk.FLAT
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configurar tags para colores
        self.chat_display.tag_config("server", foreground="#2980b9", font=("Courier", 10, "bold"))
        self.chat_display.tag_config("client", foreground="#27ae60", font=("Courier", 10, "bold"))
        self.chat_display.tag_config("timestamp", foreground="#7f8c8d", font=("Courier", 8))
        self.chat_display.tag_config("system", foreground="#e74c3c", font=("Courier", 10, "italic"))
        
        # Frame para enviar mensajes
        input_frame = tk.Frame(main_frame, bg="#2c3e50")
        input_frame.pack(fill=tk.X)
        
        # Campo de entrada
        self.message_entry = tk.Entry(
            input_frame,
            font=("Arial", 11),
            bg="#ecf0f1",
            fg="#2c3e50",
            relief=tk.FLAT,
            bd=5
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        # Botón de enviar
        send_button = tk.Button(
            input_frame,
            text="📤 Enviar",
            command=self.send_message,
            font=("Arial", 11, "bold"),
            bg="#3498db",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor="hand2"
        )
        send_button.pack(side=tk.RIGHT)
        
        # Mensaje de bienvenida
        self.display_system_message("Cliente de monitoreo iniciado")
        self.display_system_message("Conectando al servidor...")
        
        # Configurar cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def send_message(self):
        """Enviar mensaje al servidor"""
        message = self.message_entry.get().strip()
        
        if not message:
            return
        
        # Enviar mensaje mediante callback
        if self.send_message_callback:
            success = self.send_message_callback(message)
            
            if success:
                # Mostrar mensaje propio en la GUI
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.display_message("Tú", message, timestamp, is_client=True)
                
                # Limpiar campo de entrada
                self.message_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", "No se pudo enviar el mensaje")
    
    def display_message(self, sender, message, timestamp, is_client=False):
        """
        Mostrar mensaje en el chat
        
        Args:
            sender: Nombre del remitente
            message: Contenido del mensaje
            timestamp: Marca de tiempo
            is_client: True si el mensaje es del cliente actual
        """
        if not self.root:
            return
        
        def _display():
            self.chat_display.config(state=tk.NORMAL)
            
            # Timestamp
            time_str = timestamp if timestamp else datetime.now().strftime("%H:%M:%S")
            self.chat_display.insert(tk.END, f"[{time_str}] ", "timestamp")
            
            # Remitente
            tag = "client" if is_client else "server"
            self.chat_display.insert(tk.END, f"{sender}: ", tag)
            
            # Mensaje
            self.chat_display.insert(tk.END, f"{message}\n")
            
            # Auto-scroll al final
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
        
        # Ejecutar en el thread de la GUI
        if threading.current_thread() == threading.main_thread():
            _display()
        else:
            self.root.after(0, _display)
    
    def display_system_message(self, message):
        """Mostrar mensaje del sistema"""
        if not self.root:
            return
        
        def _display():
            self.chat_display.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.chat_display.insert(tk.END, f"⚙️  {message}\n", "system")
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
        
        if threading.current_thread() == threading.main_thread():
            _display()
        else:
            self.root.after(0, _display)
    
    def on_closing(self):
        """Manejar cierre de ventana"""
        if messagebox.askokcancel("Salir", "¿Deseas cerrar el cliente de monitoreo?"):
            self.root.quit()
            self.root.destroy()
    
    def run(self):
        """Iniciar el loop de la GUI"""
        if self.root:
            self.root.mainloop()
