# client.py
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import messagebox
from tkinter import ttk # Импортируем ttk для вкладок

HOST = '192.168.9.215'
PORT = 12345

class ChatClient:
    def __init__(self, master):
        self.master = master
        master.title("Общий Чат")
        master.geometry("700x600") # Начальный размер окна
        master.resizable(True, True) # Разрешим изменение размера окна

        self.client_socket = None
        self.connected = False
        self.username = ""
        self.current_private_chat_partner = None

        self.private_chat_widgets = {} # Словарь для хранения {partner_username: {'text_widget': ScrolledText, 'entry_widget': Entry}}

        self.create_widgets()
        self.show_auth_interface()

    def create_widgets(self):
        # --- Фрейм для регистрации/входа (без изменений) ---
        self.auth_frame = tk.Frame(self.master)

        tk.Label(self.auth_frame, text="Имя пользователя:", font=("Arial", 12)).pack(pady=(10, 5))
        self.auth_username_entry = tk.Entry(self.auth_frame, font=("Arial", 12))
        self.auth_username_entry.pack(fill=tk.X, padx=20)

        tk.Label(self.auth_frame, text="Пароль:", font=("Arial", 12)).pack(pady=(10, 5))
        self.auth_password_entry = tk.Entry(self.auth_frame, show="*", font=("Arial", 12))
        self.auth_password_entry.pack(fill=tk.X, padx=20)

        self.login_button = tk.Button(self.auth_frame, text="Войти", command=self.send_login_request, font=("Arial", 12))
        self.login_button.pack(pady=10)

        self.register_button = tk.Button(self.auth_frame, text="Зарегистрироваться", command=self.send_register_request, font=("Arial", 12))
        self.register_button.pack(pady=5)

        # --- Основной фрейм чата с вкладками ---
        self.chat_main_frame = tk.Frame(self.master)
        self.chat_main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10) # Будет паковаться после входа

        self.notebook = ttk.Notebook(self.chat_main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # --- Вкладка "Общий Чат" ---
        self.public_chat_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.public_chat_tab, text="Общий Чат")
        self.public_chat_tab.grid_rowconfigure(0, weight=1)
        self.public_chat_tab.grid_columnconfigure(0, weight=1)

        self.messages_text = scrolledtext.ScrolledText(self.public_chat_tab, wrap=tk.WORD, state='disabled', font=("Arial", 10))
        self.messages_text.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        self.input_frame_public = tk.Frame(self.public_chat_tab)
        self.input_frame_public.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))

        self.message_entry_public = tk.Entry(self.input_frame_public, font=("Arial", 12))
        self.message_entry_public.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry_public.bind("<Return>", self.send_public_message_event)

        self.send_button_public = tk.Button(self.input_frame_public, text="Отправить", command=self.send_public_message, font=("Arial", 10))
        self.send_button_public.pack(side=tk.RIGHT)

        # --- Вкладка "Личные Сообщения" ---
        self.private_chat_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.private_chat_tab, text="Личные Сообщения")
        self.private_chat_tab.grid_rowconfigure(2, weight=1) # Для фрейма с текущим чатом
        self.private_chat_tab.grid_columnconfigure(0, weight=1)

        tk.Label(self.private_chat_tab, text="Пользователи:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.search_entry = tk.Entry(self.private_chat_tab, font=("Arial", 10))
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.search_entry.bind("<KeyRelease>", self.filter_users)

        # Фрейм для списка пользователей и кнопки обновления
        self.users_list_frame = tk.Frame(self.private_chat_tab)
        self.users_list_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.users_list_frame.grid_columnconfigure(0, weight=1)

        self.users_listbox = tk.Listbox(self.users_list_frame, font=("Arial", 10), height=8)
        self.users_listbox.grid(row=0, column=0, sticky="nsew")
        self.users_listbox.bind("<<ListboxSelect>>", self.open_private_chat)

        self.users_list_scrollbar = tk.Scrollbar(self.users_list_frame, orient="vertical", command=self.users_listbox.yview)
        self.users_list_scrollbar.grid(row=0, column=1, sticky="ns")
        self.users_listbox.config(yscrollcommand=self.users_list_scrollbar.set)

        self.refresh_users_button = tk.Button(self.users_list_frame, text="Обновить список", command=self.request_user_list, font=("Arial", 8))
        self.refresh_users_button.grid(row=1, column=0, columnspan=2, pady=2)


        # Фрейм для отображения текущего личного чата
        self.current_private_chat_frame = tk.Frame(self.private_chat_tab, bd=1, relief=tk.SUNKEN)
        self.current_private_chat_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.current_private_chat_frame.grid_rowconfigure(1, weight=1)
        self.current_private_chat_frame.grid_columnconfigure(0, weight=1)

        self.private_chat_partner_label = tk.Label(self.current_private_chat_frame, text="Личный чат с: Нет", font=("Arial", 10, "bold"))
        self.private_chat_partner_label.grid(row=0, column=0, columnspan=2, pady=(5, 0), sticky="ew")

        # Виджет ScrolledText для личного чата, будет изменяться
        self.private_messages_text = scrolledtext.ScrolledText(self.current_private_chat_frame, wrap=tk.WORD, state='disabled', font=("Arial", 9))
        self.private_messages_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        self.input_frame_private = tk.Frame(self.current_private_chat_frame)
        self.input_frame_private.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))

        self.message_entry_private = tk.Entry(self.input_frame_private, font=("Arial", 10))
        self.message_entry_private.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry_private.bind("<Return>", self.send_private_message_event)

        self.send_button_private = tk.Button(self.input_frame_private, text="Отпр.", command=self.send_private_message, font=("Arial", 8))
        self.send_button_private.pack(side=tk.RIGHT)

        # Кнопка отключения (будет внизу основного окна, не в вкладке)
        self.disconnect_button = tk.Button(self.master, text="Отключиться", command=self.disconnect_from_server, font=("Arial", 10))
        # self.disconnect_button.pack(side=tk.BOTTOM, pady=10) # Закомментируем, чтобы показать/скрыть при переключении интерфейсов

    def show_auth_interface(self):
        """Показывает интерфейс для регистрации/входа."""
        self.chat_main_frame.pack_forget() # Скрываем основной чат
        self.disconnect_button.pack_forget() # Скрываем кнопку Отключиться
        self.auth_frame.pack(padx=10, pady=10, fill=tk.X)
        self.master.geometry("500x300")
        self.master.resizable(False, False) # Запрещаем изменение размера на экране входа
        self.auth_username_entry.focus_set()
        self.auth_password_entry.delete(0, tk.END)

    def show_chat_interface(self):
        """Показывает интерфейс чата с вкладками."""
        self.auth_frame.pack_forget() # Скрываем аутентификацию
        self.chat_main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10) # Показываем основной чат
        self.disconnect_button.pack(side=tk.BOTTOM, pady=10) # Показываем кнопку Отключиться
        self.master.geometry("700x600")
        self.master.resizable(True, True) # Разрешаем изменение размера
        self.message_entry_public.focus_set()
        self.request_user_list()

    def display_public_message(self, message):
        """Отображает сообщение в текстовом поле общего чата."""
        self.messages_text.config(state='normal')
        self.messages_text.insert(tk.END, message + "\n")
        self.messages_text.yview(tk.END)
        self.messages_text.config(state='disabled')

    def display_private_message(self, partner_username, message):
        """Отображает сообщение в текстовом поле личного чата."""
        if partner_username == self.current_private_chat_partner:
            self.private_messages_text.config(state='normal')
            self.private_messages_text.insert(tk.END, message + "\n")
            self.private_messages_text.yview(tk.END)
            self.private_messages_text.config(state='disabled')
        else:
            # Если сообщение от другого пользователя, который не является текущим,
            # можно сделать небольшое уведомление, например, в общем чате или мигать вкладкой.
            self.display_public_message(f"[ЛС от {partner_username}]: {message}")


    def connect_to_server_once(self):
        """Устанавливает соединение с сервером, если его нет."""
        if not self.client_socket or not self.connected:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((HOST, PORT))
                self.connected = True
                receive_thread = threading.Thread(target=self.receive_messages)
                receive_thread.daemon = True
                receive_thread.start()
                return True
            except ConnectionRefusedError:
                messagebox.showerror("Ошибка подключения", "Сервер не запущен или недоступен.", parent=self.master)
                return False
            except Exception as e:
                messagebox.showerror("Ошибка подключения", f"Произошла ошибка при подключении: {e}", parent=self.master)
                return False
        return True

    def receive_messages(self):
        """Поток для получения сообщений от сервера."""
        while self.connected:
            try:
                raw_data = self.client_socket.recv(4096)
                if not raw_data:
                    self.disconnect_from_server("Сервер отключился.")
                    break
                message = raw_data.decode('utf-8')

                if message.startswith("REGISTER_SUCCESS"):
                    messagebox.showinfo("Регистрация", "Регистрация прошла успешно! Теперь вы можете войти.", parent=self.master)
                    self.auth_username_entry.delete(0, tk.END)
                    self.auth_password_entry.delete(0, tk.END)
                    self.auth_username_entry.focus_set()
                elif message.startswith("REGISTER_FAIL:"):
                    error_msg = message.split(':', 1)[1]
                    messagebox.showerror("Ошибка регистрации", error_msg, parent=self.master)
                elif message.startswith("LOGIN_SUCCESS:"):
                    self.username = message.split(':', 1)[1]
                    messagebox.showinfo("Вход", f"Добро пожаловать, {self.username}!", parent=self.master)
                    self.display_public_message("--- Подключено к чату. ---")
                    self.show_chat_interface()
                elif message.startswith("LOGIN_FAIL:"):
                    error_msg = message.split(':', 1)[1]
                    messagebox.showerror("Ошибка входа", error_msg, parent=self.master)
                elif message.startswith("ERROR:"):
                    error_msg = message.split(':', 1)[1]
                    self.display_public_message(f"[ОШИБКА] {error_msg}")
                    messagebox.showerror("Ошибка", error_msg, parent=self.master)
                elif message.startswith("PRIVATE_FROM:"):
                    parts = message.split(':', 2)
                    if len(parts) >= 3:
                        sender = parts[1]
                        private_msg = parts[2]
                        # Отображаем сообщение в текущем окне ЛС, если оно совпадает, иначе уведомляем в общем чате
                        self.display_private_message(sender, f"{sender}: {private_msg}")
                elif message.startswith("HISTORY_RESPONSE:"):
                    parts = message.split(':', 2)
                    if len(parts) >= 3:
                        partner_user = parts[1]
                        history_content = parts[2]
                        if partner_user == self.current_private_chat_partner:
                            self.private_messages_text.config(state='normal')
                            self.private_messages_text.delete(1.0, tk.END)
                            self.private_messages_text.insert(tk.END, history_content + "\n")
                            self.private_messages_text.yview(tk.END)
                            self.private_messages_text.config(state='disabled')
                        else:
                            print(f"История для {partner_user} пришла, но чат с ним не открыт.")
                elif message.startswith("USER_LIST:"):
                    user_string = message.split(':', 1)[1]
                    self.all_registered_users = user_string.split(',') if user_string else []
                    self.filter_users()
                else:
                    self.display_public_message(message)

            except ConnectionResetError:
                self.disconnect_from_server("Соединение с сервером потеряно.")
                break
            except OSError:
                break
            except Exception as e:
                print(f"Ошибка при получении сообщения: {e}")
                self.disconnect_from_server(f"Ошибка: {e}")
                break

    def send_register_request(self):
        username = self.auth_username_entry.get().strip()
        password = self.auth_password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Предупреждение", "Пожалуйста, введите имя пользователя и пароль для регистрации.", parent=self.master)
            return

        if self.connect_to_server_once():
            try:
                self.client_socket.send(f"REGISTER:{username}:{password}".encode('utf-8'))
            except Exception as e:
                messagebox.showerror("Ошибка регистрации", f"Не удалось отправить запрос на регистрацию: {e}", parent=self.master)
                self.disconnect_from_server()

    def send_login_request(self):
        username = self.auth_username_entry.get().strip()
        password = self.auth_password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Предупреждение", "Пожалуйста, введите имя пользователя и пароль для входа.", parent=self.master)
            return

        if self.connect_to_server_once():
            try:
                self.client_socket.send(f"LOGIN:{username}:{password}".encode('utf-8'))
            except Exception as e:
                messagebox.showerror("Ошибка входа", f"Не удалось отправить запрос на вход: {e}", parent=self.master)
                self.disconnect_from_server()

    def send_public_message(self):
        """Отправляет сообщение общего чата на сервер."""
        if not self.connected or not self.username:
            messagebox.showerror("Ошибка", "Вы не подключены или не вошли в систему.", parent=self.master)
            return

        message = self.message_entry_public.get()
        if message:
            try:
                self.client_socket.send(f"CHAT:{message}".encode('utf-8'))
                self.display_public_message(f"Вы: {message}")
                self.message_entry_public.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Ошибка отправки", f"Не удалось отправить сообщение: {e}", parent=self.master)
                self.disconnect_from_server()

    def send_public_message_event(self, event):
        self.send_public_message()

    def request_user_list(self):
        """Запрашивает список всех зарегистрированных пользователей у сервера."""
        if self.connected and self.username:
            try:
                self.client_socket.send("GET_USERS".encode('utf-8'))
            except Exception as e:
                print(f"Ошибка при запросе списка пользователей: {e}")

    def filter_users(self, event=None):
        """Фильтрует список пользователей в Listbox по введенному тексту."""
        search_query = self.search_entry.get().lower()
        self.users_listbox.delete(0, tk.END)
        for user in self.all_registered_users:
            if search_query in user.lower() and user != self.username: # Не показывать себя
                self.users_listbox.insert(tk.END, user)

    def open_private_chat(self, event):
        """Открывает или переключает на личный чат с выбранным пользователем."""
        selected_indices = self.users_listbox.curselection()
        if not selected_indices:
            return

        index = selected_indices[0]
        partner_username = self.users_listbox.get(index)

        if partner_username == self.username: # Эта проверка теперь дублируется в filter_users, но можно оставить
            messagebox.showwarning("Ошибка", "Вы не можете начать личный чат с самим собой.", parent=self.master)
            return

        # Переключаем на вкладку личных сообщений, если пользователь не там
        self.notebook.select(self.private_chat_tab)

        if partner_username != self.current_private_chat_partner:
            self.current_private_chat_partner = partner_username
            self.private_chat_partner_label.config(text=f"Личный чат с: {partner_username}")
            
            # Загружаем историю для нового партнера
            self.request_private_chat_history(partner_username)
        
        self.message_entry_private.focus_set()

    def request_private_chat_history(self, partner_username):
        """Запрашивает историю личного чата у сервера."""
        if self.connected and self.username:
            try:
                self.client_socket.send(f"HISTORY_REQUEST:{partner_username}".encode('utf-8'))
            except Exception as e:
                print(f"Ошибка при запросе истории чата с {partner_username}: {e}")

    def send_private_message(self):
        """Отправляет личное сообщение выбранному пользователю."""
        if not self.connected or not self.username:
            messagebox.showerror("Ошибка", "Вы не подключены или не вошли в систему.", parent=self.master)
            return
        if not self.current_private_chat_partner:
            messagebox.showwarning("Ошибка", "Выберите пользователя для личного чата.", parent=self.master)
            return

        message = self.message_entry_private.get()
        if message:
            try:
                self.client_socket.send(f"PRIVATE_MSG:{self.current_private_chat_partner}:{message}".encode('utf-8'))
                self.display_private_message(self.current_private_chat_partner, f"Вы: {message}")
                self.message_entry_private.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Ошибка отправки ЛС", f"Не удалось отправить личное сообщение: {e}", parent=self.master)
                self.disconnect_from_server()

    def send_private_message_event(self, event):
        self.send_private_message()

    def disconnect_from_server(self, reason="Вы были отключены."):
        """Отключается от сервера."""
        if not self.connected:
            return

        try:
            self.connected = False
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
            self.display_public_message(f"--- Отключено от сервера: {reason} ---")
            self.show_auth_interface()
            self.username = ""
            self.current_private_chat_partner = None

            # Очищаем все чат-поля
            self.messages_text.config(state='normal')
            self.messages_text.delete(1.0, tk.END)
            self.messages_text.config(state='disabled')

            self.private_messages_text.config(state='normal')
            self.private_messages_text.delete(1.0, tk.END)
            self.private_messages_text.config(state='disabled')
            self.private_chat_partner_label.config(text="Личный чат с: Нет")
            self.users_listbox.delete(0, tk.END)
            self.search_entry.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Ошибка отключения", f"Ошибка при отключении: {e}", parent=self.master)

    def on_closing(self):
        """Вызывается при закрытии окна."""
        if self.connected:
            self.disconnect_from_server("Закрытие приложения.")
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()