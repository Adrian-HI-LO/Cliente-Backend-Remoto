"""
GUI para el cliente de monitoreo
Interfaz gráfica con Tkinter para mostrar mensajes y enviar mensajes al servidor
"""
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk
from datetime import datetime
import threading
import os


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
        self.file_transfer_callback = None
        self.request_file_callback = None
        
    def setup_gui(self):
        """Configurar la interfaz gráfica"""
        self.root = tk.Tk()
        self.root.title("Cliente de Monitoreo")
        self.root.geometry("700x600")
        self.root.configure(bg="#2c3e50")
        
        # Crear Notebook (pestañas)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña de Chat
        chat_frame = tk.Frame(notebook, bg="#2c3e50")
        notebook.add(chat_frame, text="💬 Chat")
        self._setup_chat_tab(chat_frame)
        
        # Pestaña de Transferencia de Archivos
        file_frame = tk.Frame(notebook, bg="#2c3e50")
        notebook.add(file_frame, text="📁 Archivos")
        self._setup_file_transfer_tab(file_frame)
        
        # Configurar cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _setup_chat_tab(self, parent_frame):
        """Configurar la pestaña de chat"""
        # Título
        title_label = tk.Label(
            parent_frame,
            text="💬 Chat con Servidor",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        title_label.pack(pady=(10, 10))
        
        # Área de mensajes
        chat_area = tk.Frame(parent_frame, bg="#34495e", relief=tk.SUNKEN, bd=2)
        chat_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=10)
        
        # ScrolledText para mostrar mensajes
        self.chat_display = scrolledtext.ScrolledText(
            chat_area,
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
        input_frame = tk.Frame(parent_frame, bg="#2c3e50")
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
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
    
    def _setup_file_transfer_tab(self, parent_frame):
        """Configurar la pestaña de transferencia de archivos"""
        # Título
        title_label = tk.Label(
            parent_frame,
            text="📁 Transferencia de Archivos",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        title_label.pack(pady=(10, 10))
        
        # Frame principal
        main_content = tk.Frame(parent_frame, bg="#2c3e50")
        main_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Sección: Enviar archivo al servidor
        send_frame = tk.LabelFrame(
            main_content,
            text="⬆️  Enviar archivo al servidor",
            font=("Arial", 12, "bold"),
            bg="#34495e",
            fg="#ecf0f1",
            relief=tk.RAISED,
            bd=2
        )
        send_frame.pack(fill=tk.X, pady=(0, 10))
        
        send_content = tk.Frame(send_frame, bg="#34495e")
        send_content.pack(fill=tk.X, padx=10, pady=10)
        
        self.selected_file_label = tk.Label(
            send_content,
            text="No hay archivo seleccionado",
            font=("Arial", 10),
            bg="#34495e",
            fg="#bdc3c7",
            anchor="w"
        )
        self.selected_file_label.pack(fill=tk.X, pady=(0, 5))
        
        btn_frame1 = tk.Frame(send_content, bg="#34495e")
        btn_frame1.pack(fill=tk.X)
        
        select_file_btn = tk.Button(
            btn_frame1,
            text="📎 Seleccionar Archivo",
            command=self.select_file_to_send,
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        select_file_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        send_file_btn = tk.Button(
            btn_frame1,
            text="⬆️ Enviar al Servidor",
            command=self.send_file_to_server,
            font=("Arial", 10, "bold"),
            bg="#27ae60",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        send_file_btn.pack(side=tk.LEFT)
        
        # Sección: Recibir archivo del servidor
        receive_frame = tk.LabelFrame(
            main_content,
            text="⬇️  Recibir archivo del servidor",
            font=("Arial", 12, "bold"),
            bg="#34495e",
            fg="#ecf0f1",
            relief=tk.RAISED,
            bd=2
        )
        receive_frame.pack(fill=tk.X, pady=(0, 10))
        
        receive_content = tk.Frame(receive_frame, bg="#34495e")
        receive_content.pack(fill=tk.X, padx=10, pady=10)
        
        info_label = tk.Label(
            receive_content,
            text="Cuando el servidor envíe un archivo, se te preguntará dónde guardarlo",
            font=("Arial", 9),
            bg="#34495e",
            fg="#bdc3c7",
            wraplength=550,
            justify="left"
        )
        info_label.pack(fill=tk.X, pady=(0, 5))
        
        # Log de transferencias
        log_frame = tk.LabelFrame(
            main_content,
            text="📋 Registro de Transferencias",
            font=("Arial", 12, "bold"),
            bg="#34495e",
            fg="#ecf0f1",
            relief=tk.RAISED,
            bd=2
        )
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.transfer_log = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=60,
            height=10,
            font=("Courier", 9),
            bg="#ecf0f1",
            fg="#2c3e50",
            state=tk.DISABLED,
            relief=tk.FLAT
        )
        self.transfer_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.transfer_log.tag_config("success", foreground="#27ae60", font=("Courier", 9, "bold"))
        self.transfer_log.tag_config("error", foreground="#e74c3c", font=("Courier", 9, "bold"))
        self.transfer_log.tag_config("info", foreground="#3498db", font=("Courier", 9, "bold"))
        
        self.log_transfer("Sistema de transferencia de archivos iniciado", "info")
        
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
    
    def select_file_to_send(self):
        """Seleccionar archivo para enviar al servidor"""
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo para enviar",
            filetypes=[
                ("Todos los archivos", "*.*"),
                ("Documentos", "*.pdf *.doc *.docx *.txt"),
                ("Imágenes", "*.png *.jpg *.jpeg *.gif"),
                ("Archivos comprimidos", "*.zip *.rar *.7z")
            ]
        )
        
        if filename:
            self.selected_file_path = filename
            basename = os.path.basename(filename)
            size = os.path.getsize(filename)
            size_str = self._format_file_size(size)
            self.selected_file_label.config(
                text=f"✓ {basename} ({size_str})",
                fg="#27ae60"
            )
            self.log_transfer(f"Archivo seleccionado: {basename}", "info")
        else:
            self.selected_file_path = None
            self.selected_file_label.config(
                text="No hay archivo seleccionado",
                fg="#bdc3c7"
            )
    
    def send_file_to_server(self):
        """Enviar archivo seleccionado al servidor"""
        if not hasattr(self, 'selected_file_path') or not self.selected_file_path:
            messagebox.showwarning("Advertencia", "Selecciona un archivo primero")
            return
        
        if not self.file_transfer_callback:
            messagebox.showerror("Error", "Sistema de transferencia no disponible")
            return
        
        basename = os.path.basename(self.selected_file_path)
        self.log_transfer(f"Enviando: {basename}...", "info")
        
        # Llamar callback para enviar archivo
        success = self.file_transfer_callback(self.selected_file_path)
        
        if success:
            self.log_transfer(f"✓ Archivo enviado: {basename}", "success")
            self.selected_file_path = None
            self.selected_file_label.config(
                text="No hay archivo seleccionado",
                fg="#bdc3c7"
            )
        else:
            self.log_transfer(f"✗ Error enviando: {basename}", "error")
    
    def ask_save_location(self, filename, file_data):
        """Preguntar dónde guardar el archivo recibido"""
        save_path = filedialog.asksaveasfilename(
            title="Guardar archivo recibido",
            initialfile=filename,
            defaultextension="",
            filetypes=[("Todos los archivos", "*.*")]
        )
        
        if save_path:
            try:
                import base64
                file_bytes = base64.b64decode(file_data)
                with open(save_path, 'wb') as f:
                    f.write(file_bytes)
                
                size = os.path.getsize(save_path)
                size_str = self._format_file_size(size)
                self.log_transfer(f"✓ Archivo guardado: {filename} ({size_str})", "success")
                messagebox.showinfo("Éxito", f"Archivo guardado en:\n{save_path}")
                return True
            except Exception as e:
                self.log_transfer(f"✗ Error guardando: {str(e)}", "error")
                messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{str(e)}")
                return False
        else:
            self.log_transfer(f"Recepción cancelada: {filename}", "info")
            return False
    
    def log_transfer(self, message, msg_type="info"):
        """Agregar mensaje al log de transferencias"""
        if not hasattr(self, 'transfer_log') or not self.transfer_log:
            return
        
        def _log():
            self.transfer_log.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.transfer_log.insert(tk.END, f"[{timestamp}] ", "info")
            self.transfer_log.insert(tk.END, f"{message}\n", msg_type)
            self.transfer_log.see(tk.END)
            self.transfer_log.config(state=tk.DISABLED)
        
        if threading.current_thread() == threading.main_thread():
            _log()
        else:
            self.root.after(0, _log)
    
    def _format_file_size(self, size_bytes):
        """Formatear tamaño de archivo"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def set_file_transfer_callback(self, callback):
        """Establecer callback para transferencia de archivos"""
        self.file_transfer_callback = callback
    
    def on_closing(self):
        """Manejar cierre de ventana"""
        if messagebox.askokcancel("Salir", "¿Deseas cerrar el cliente de monitoreo?"):
            self.root.quit()
            self.root.destroy()
    
    def run(self):
        """Iniciar el loop de la GUI"""
        if self.root:
            self.root.mainloop()