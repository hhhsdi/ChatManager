# client.py
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import messagebox
from tkinter import ttk

HOST = '192.168.9.215'
PORT = 12345

# --- Обновленные Настройки Стилей и Цветов ---
COLOR_BG_MAIN = "#282C34"
COLOR_BG_CARD = "#3A3F47"
COLOR_TEXT_PRIMARY = "#ABB2BF"
COLOR_TEXT_ACCENT = "#61AFEF"
COLOR_PRIMARY_BUTTON = "#61AFEF"
COLOR_SECONDARY_BUTTON = "#C678DD"
COLOR_HOVER = "#56B6C2"
COLOR_ERROR = "#E06C75"

FONT_FAMILY_TITLE = "Helvetica Neue"
FONT_FAMILY_TEXT = "Arial"

FONT_TITLE = (FONT_FAMILY_TITLE, 24, "bold")
FONT_HEADING = (FONT_FAMILY_TEXT, 14, "bold")
FONT_SUBHEADING = (FONT_FAMILY_TEXT, 12, "bold")
FONT_NORMAL = (FONT_FAMILY_TEXT, 11)
FONT_SMALL = (FONT_FAMILY_TEXT, 9)
FONT_CHAT = ("Consolas", 10)

class ChatClient:
    def __init__(self, master):
        self.master = master
        master.title("Мессенджер")
        master.geometry("800x700")
        master.minsize(650, 550)
        master.configure(bg=COLOR_BG_MAIN)

        self.client_socket = None
        self.connected = False
        self.username = ""
        self.current_private_chat_partner = None # Текущий активный личный чат (пользователь)

        # Словарь для хранения информации о динамически созданных вкладках личных чатов
        # Ключ: имя пользователя, Значение: {'tab_id': <id вкладки>, 'text_widget': <ScrolledText>}
        self.private_chat_tabs = {}

        self.all_registered_users = [] # Список всех пользователей для поиска

        self.setup_styles()
        self.create_widgets()
        self.show_auth_interface()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.',
                        background=COLOR_BG_MAIN,
                        foreground=COLOR_TEXT_PRIMARY,
                        font=FONT_NORMAL)

        style.configure('Card.TFrame',
                        background=COLOR_BG_CARD,
                        relief="flat",
                        borderwidth=0)

        style.configure('TButton',
                        background=COLOR_PRIMARY_BUTTON,
                        foreground="#FFFFFF",
                        font=FONT_NORMAL,
                        padding=[15, 8],
                        relief="flat",
                        focuscolor=COLOR_PRIMARY_BUTTON)
        style.map('TButton',
                  background=[('active', COLOR_HOVER), ('pressed', COLOR_SECONDARY_BUTTON)],
                  foreground=[('active', "#FFFFFF"), ('pressed', "#FFFFFF")])

        style.configure('Secondary.TButton',
                        background=COLOR_SECONDARY_BUTTON,
                        foreground="#FFFFFF",
                        font=FONT_NORMAL,
                        padding=[15, 8],
                        relief="flat",
                        focuscolor=COLOR_SECONDARY_BUTTON)
        style.map('Secondary.TButton',
                  background=[('active', COLOR_HOVER), ('pressed', COLOR_PRIMARY_BUTTON)],
                  foreground=[('active', "#FFFFFF"), ('pressed', "#FFFFFF")])

        style.configure('TEntry',
                        fieldbackground=COLOR_BG_CARD,
                        foreground=COLOR_TEXT_PRIMARY,
                        insertbackground=COLOR_TEXT_ACCENT,
                        borderwidth=1,
                        relief="solid",
                        highlightbackground=COLOR_BG_CARD,
                        highlightcolor=COLOR_PRIMARY_BUTTON,
                        highlightthickness=1,
                        padding=[5, 5])

        style.configure('TLabel',
                        background=COLOR_BG_MAIN,
                        foreground=COLOR_TEXT_PRIMARY)
        style.configure('Heading.TLabel',
                        font=FONT_HEADING,
                        background=COLOR_BG_MAIN,
                        foreground=COLOR_TEXT_ACCENT)
        style.configure('Subheading.TLabel',
                        font=FONT_SUBHEADING,
                        background=COLOR_BG_CARD,
                        foreground=COLOR_TEXT_PRIMARY)

        # Notebook (вкладки)
        style.configure('TNotebook',
                        background=COLOR_BG_MAIN,
                        borderwidth=0,
                        tabposition='wn', # Вкладки слева
                        padding=0)

        style.configure('TNotebook.Tab',
                        background=COLOR_BG_CARD,
                        foreground=COLOR_TEXT_PRIMARY,
                        font=FONT_SUBHEADING,
                        padding=[15, 10], # Увеличиваем отступы вкладок
                        borderwidth=0,
                        relief="flat",
                        focuscolor="") # Убираем пунктирную рамку фокуса для вкладки

        style.map('TNotebook.Tab',
                  background=[('selected', COLOR_PRIMARY_BUTTON), ('active', COLOR_HOVER)],
                  foreground=[('selected', "#FFFFFF"), ('active', "#FFFFFF")],
                  expand=[('selected', [0,0,0,0])])

        style.layout("TNotebook.Tab", [
            ("TNotebook.tab", {
                "sticky": "nswe",
                "children": [
                    ("TNotebook.padding", {
                        "sticky": "nswe",
                        "children": [
                            ("TNotebook.focus", {
                                "sticky": "nswe",
                                "children": [
                                    ("TNotebook.label", {"sticky": "nswe"}) # Метка растягивается
                                ]
                            })
                        ]
                    })
                ]
            })
        ])
        style.configure('TNotebook.Tab', width=18) # Фиксированная ширина в символах

        # Скроллбары
        style.configure("Vertical.TScrollbar",
                        background=COLOR_BG_MAIN,
                        troughcolor=COLOR_BG_CARD,
                        bordercolor=COLOR_BG_MAIN,
                        arrowcolor=COLOR_TEXT_PRIMARY,
                        relief="flat")
        style.map("Vertical.TScrollbar",
                  background=[('active', COLOR_HOVER)])

    def create_widgets(self):
        # --- Фрейм для регистрации/входа ---
        self.auth_frame = ttk.Frame(self.master, style='Card.TFrame', padding=30)
        
        ttk.Label(self.auth_frame, text="Добро пожаловать в Мессенджер", font=FONT_TITLE,
                  background=COLOR_BG_CARD, foreground=COLOR_TEXT_ACCENT).pack(pady=(0, 25))
        
        ttk.Label(self.auth_frame, text="Имя пользователя:", font=FONT_NORMAL,
                  background=COLOR_BG_CARD, foreground=COLOR_TEXT_PRIMARY).pack(pady=(5, 0), anchor="w")
        self.auth_username_entry = ttk.Entry(self.auth_frame, font=FONT_NORMAL)
        self.auth_username_entry.pack(fill=tk.X, padx=0, pady=5)

        ttk.Label(self.auth_frame, text="Пароль:", font=FONT_NORMAL,
                  background=COLOR_BG_CARD, foreground=COLOR_TEXT_PRIMARY).pack(pady=(15, 0), anchor="w")
        self.auth_password_entry = ttk.Entry(self.auth_frame, show="*", font=FONT_NORMAL)
        self.auth_password_entry.pack(fill=tk.X, padx=0, pady=5)

        self.login_button = ttk.Button(self.auth_frame, text="Войти", command=self.send_login_request, style='TButton')
        self.login_button.pack(fill=tk.X, pady=(25, 10))

        self.register_button = ttk.Button(self.auth_frame, text="Зарегистрироваться", command=self.send_register_request, style='Secondary.TButton')
        self.register_button.pack(fill=tk.X, pady=(10, 0))

        # --- Основной фрейм чата с вкладками ---
        self.chat_main_frame = ttk.Frame(self.master, style='TFrame')

        self.notebook = ttk.Notebook(self.chat_main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True) 

        # --- Вкладка "Общий Чат" ---
        self.public_chat_tab = ttk.Frame(self.notebook, style='Card.TFrame', padding=10)
        self.notebook.add(self.public_chat_tab, text="Общий Чат", sticky="nsew") # sticky для растягивания содержимого вкладки
        self.public_chat_tab.grid_rowconfigure(0, weight=1)
        self.public_chat_tab.grid_columnconfigure(0, weight=1)

        ttk.Label(self.public_chat_tab, text="Общий Чат", font=FONT_HEADING,
                  background=COLOR_BG_CARD, foreground=COLOR_TEXT_ACCENT).grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.messages_text = scrolledtext.ScrolledText(
            self.public_chat_tab,
            wrap=tk.WORD,
            state='disabled',
            font=FONT_CHAT,
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_PRIMARY,
            insertbackground=COLOR_TEXT_PRIMARY,
            borderwidth=0,
            relief="flat",
            highlightbackground=COLOR_BG_MAIN,
            highlightthickness=0
        )
        self.messages_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        self.input_frame_public = ttk.Frame(self.public_chat_tab, style='Card.TFrame')
        self.input_frame_public.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(5, 0))

        self.message_entry_public = ttk.Entry(self.input_frame_public, font=FONT_NORMAL)
        self.message_entry_public.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry_public.bind("<Return>", self.send_public_message_event)

        self.send_button_public = ttk.Button(self.input_frame_public, text="Отправить", command=self.send_public_message)
        self.send_button_public.pack(side=tk.RIGHT)

        # --- Вкладка "Начать новый чат" (раньше была "Личные сообщения") ---
        # Эта вкладка будет использоваться только для поиска пользователей и создания НОВЫХ чатов.
        # Сами чаты будут отдельными вкладками.
        self.new_private_chat_tab = ttk.Frame(self.notebook, style='Card.TFrame', padding=10)
        self.notebook.add(self.new_private_chat_tab, text="Новый Чат / Поиск")
        
        self.new_private_chat_tab.grid_columnconfigure(0, weight=1)
        self.new_private_chat_tab.grid_rowconfigure(2, weight=1) # Listbox растягивается

        ttk.Label(self.new_private_chat_tab, text="Найти пользователя для чата:", font=FONT_HEADING,
                  background=COLOR_BG_CARD, foreground=COLOR_TEXT_ACCENT).grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.search_entry = ttk.Entry(self.new_private_chat_tab, font=FONT_NORMAL)
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.search_entry.bind("<KeyRelease>", self.filter_users)

        self.search_results_listbox = tk.Listbox(
            self.new_private_chat_tab,
            font=FONT_NORMAL,
            height=10,
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_PRIMARY,
            selectbackground=COLOR_PRIMARY_BUTTON,
            selectforeground="#FFFFFF",
            borderwidth=0,
            relief="flat",
            highlightbackground=COLOR_BG_MAIN,
            highlightthickness=0
        )
        self.search_results_listbox.grid(row=2, column=0, sticky="nswe", padx=5, pady=5)
        self.search_results_listbox.bind("<<ListboxSelect>>", self.create_or_switch_private_chat_tab)
        
        self.refresh_users_button = ttk.Button(self.new_private_chat_tab, text="Обновить список пользователей", command=self.request_user_list, style='Secondary.TButton')
        self.refresh_users_button.grid(row=3, column=0, sticky="ew", padx=5, pady=(5,0))

        # Кнопка отключения (внизу основного окна)
        self.disconnect_button = ttk.Button(self.master, text="Отключиться", command=self.disconnect_from_server, style='Secondary.TButton')
        
        # Разделитель между вкладками и кнопкой отключения
        self.separator = ttk.Separator(self.master, orient='horizontal')

    def show_auth_interface(self):
        self.chat_main_frame.pack_forget()
        self.disconnect_button.pack_forget()
        self.separator.pack_forget()

        self.auth_frame.pack(expand=True, fill=tk.BOTH, padx=70, pady=70)
        self.master.geometry("450x550")
        self.master.resizable(False, False)
        self.auth_username_entry.focus_set()
        self.auth_password_entry.delete(0, tk.END)

    def show_chat_interface(self):
        self.auth_frame.pack_forget()
        self.chat_main_frame.pack(fill=tk.BOTH, expand=True)
        self.separator.pack(fill=tk.X, padx=10, pady=(0,5))
        self.disconnect_button.pack(side=tk.BOTTOM, pady=(0, 10))
        
        self.master.geometry("800x700")
        self.master.resizable(True, True)
        self.message_entry_public.focus_set()
        self.request_user_list()

    def display_public_message(self, message):
        self.messages_text.config(state='normal')
        self.messages_text.insert(tk.END, message + "\n")
        self.messages_text.yview(tk.END)
        self.messages_text.config(state='disabled')

    def display_private_message(self, partner_username, message):
        """Отображает сообщение в текстовом поле личного чата.
           Создает вкладку чата, если ее нет, и добавляет сообщение."""
        self.master.after(0, lambda: self._handle_incoming_private_message_thread_safe(partner_username, message))

    def _handle_incoming_private_message_thread_safe(self, partner_username, message):
        if partner_username not in self.private_chat_tabs:
            self.create_or_switch_private_chat_tab(partner_username=partner_username)

        # Добавляем сообщение в соответствующий текстовый виджет
        text_widget = self.private_chat_tabs[partner_username]['text_widget']
        text_widget.config(state='normal')
        text_widget.insert(tk.END, message + "\n")
        text_widget.yview(tk.END)
        text_widget.config(state='disabled')

        # Если это новый чат или сообщение пришло от неактивного чата, можно подсветить вкладку
        if self.notebook.tab(self.notebook.select(), "text") != partner_username:
            # В ttk.Notebook нет прямого метода для "подсветки" вкладки
            # Можно изменить текст вкладки (добавить *) или цвет (если это возможно через стили)
            pass # Пока не реализуем индикатор непрочитанных сообщений, т.к. это усложнит стили

    def connect_to_server_once(self):
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
        while self.connected:
            try:
                raw_data = self.client_socket.recv(4096)
                if not raw_data:
                    self.disconnect_from_server("Сервер отключился.")
                    break
                message = raw_data.decode('utf-8')

                if message.startswith("REGISTER_SUCCESS"):
                    self.master.after(0, lambda: self.display_public_message("--- Регистрация прошла успешно! Теперь вы можете войти. ---"))
                    self.master.after(0, lambda: self.auth_username_entry.delete(0, tk.END))
                    self.master.after(0, lambda: self.auth_password_entry.delete(0, tk.END))
                    self.master.after(0, lambda: self.auth_username_entry.focus_set())
                elif message.startswith("REGISTER_FAIL:"):
                    error_msg = message.split(':', 1)[1]
                    messagebox.showerror("Ошибка регистрации", error_msg, parent=self.master)
                elif message.startswith("LOGIN_SUCCESS:"):
                    self.username = message.split(':', 1)[1]
                    self.master.after(0, self.show_chat_interface)
                    self.master.after(0, lambda: self.display_public_message(f"--- Добро пожаловать в чат, {self.username}! ---"))
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
                        # Убедимся, что создание виджета и отображение сообщения происходит в главном потоке Tkinter
                        self.master.after(0, self.display_private_message, sender, f"{sender}: {private_msg}")
                elif message.startswith("HISTORY_RESPONSE:"):
                    parts = message.split(':', 2)
                    if len(parts) >= 3:
                        partner_user = parts[1]
                        history_content = parts[2]
                        if partner_user in self.private_chat_tabs:
                            text_widget = self.private_chat_tabs[partner_user]['text_widget']
                            self.master.after(0, lambda: self.load_private_chat_history_to_widget(text_widget, history_content))
                elif message.startswith("USER_LIST:"):
                    user_string = message.split(':', 1)[1]
                    self.all_registered_users = sorted([u for u in user_string.split(',') if u and u != self.username])
                    self.master.after(0, self.filter_users)
                else:
                    self.master.after(0, self.display_public_message, message)

            except ConnectionResetError:
                self.disconnect_from_server("Соединение с сервером потеряно.")
                break
            except OSError:
                break
            except Exception as e:
                print(f"Ошибка при получении сообщения: {e}")
                self.disconnect_from_server(f"Ошибка: {e}")
                break

    def load_private_chat_history_to_widget(self, text_widget, history_content):
        text_widget.config(state='normal')
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, history_content + "\n")
        text_widget.yview(tk.END)
        text_widget.config(state='disabled')

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
        if self.connected and self.username:
            try:
                self.client_socket.send("GET_USERS".encode('utf-8'))
            except Exception as e:
                print(f"Ошибка при запросе списка пользователей: {e}")

    def filter_users(self, event=None):
        search_query = self.search_entry.get().strip().lower()
        self.search_results_listbox.delete(0, tk.END)
        for user in sorted(self.all_registered_users):
            # Показываем только тех, с кем еще нет открытой вкладки
            if search_query in user.lower() and user not in self.private_chat_tabs:
                self.search_results_listbox.insert(tk.END, user)

    def create_or_switch_private_chat_tab(self, event=None, partner_username=None):
        """Создает новую вкладку для личного чата или переключается на существующую."""
        if partner_username is None: # Если вызов идет от Listbox (клик пользователя)
            selected_indices = self.search_results_listbox.curselection()
            if not selected_indices:
                return
            index = selected_indices[0]
            partner_username = self.search_results_listbox.get(index)

            # Очищаем поле поиска и список результатов после выбора
            self.search_entry.delete(0, tk.END)
            self.filter_users() # Обновим список, чтобы убрать выбранного пользователя

        if partner_username == self.username:
            messagebox.showwarning("Ошибка", "Вы не можете начать чат с самим собой.", parent=self.master)
            return

        if partner_username in self.private_chat_tabs:
            # Если вкладка уже существует, просто переключаемся на нее
            self.notebook.select(self.private_chat_tabs[partner_username]['tab_id'])
            self.current_private_chat_partner = partner_username
            self.message_entry_private.focus_set()
            return

        # --- Создаем новую вкладку для личного чата ---
        chat_tab_frame = ttk.Frame(self.notebook, style='Card.TFrame', padding=10)
        
        # Заголовок чата (можно сделать динамическим, включающим статус)
        chat_header_label = ttk.Label(chat_tab_frame, text=f"Личный чат с: {partner_username}", font=FONT_HEADING,
                                      background=COLOR_BG_CARD, foreground=COLOR_TEXT_ACCENT)
        chat_header_label.pack(side=tk.TOP, fill=tk.X, pady=5)

        # Кнопка закрытия вкладки (находится рядом с заголовком)
        # Это не стандартная функциональность ttk.Notebook, но можно реализовать
        # через создание фрейма заголовка или добавлением кнопки внутри вкладки.
        # Для простоты, пока сделаем кнопку закрытия внутри самой вкладки вверху.
        close_button = ttk.Button(chat_tab_frame, text="X", width=3, style='Secondary.TButton',
                                  command=lambda p=partner_username: self.close_private_chat_tab(p))
        close_button.place(relx=1.0, rely=0, anchor="ne", x=-5, y=5) # Размещаем в правом верхнем углу

        # Текстовое поле для сообщений чата
        messages_text_widget = scrolledtext.ScrolledText(
            chat_tab_frame,
            wrap=tk.WORD,
            state='disabled',
            font=FONT_CHAT,
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_PRIMARY,
            insertbackground=COLOR_TEXT_PRIMARY,
            borderwidth=0,
            relief="flat",
            highlightbackground=COLOR_BG_MAIN,
            highlightthickness=0
        )
        messages_text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Поле ввода сообщения и кнопка отправки
        input_frame = ttk.Frame(chat_tab_frame, style='Card.TFrame')
        input_frame.pack(fill=tk.X, pady=(5, 0), padx=5)

        message_entry = ttk.Entry(input_frame, font=FONT_NORMAL)
        message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        message_entry.bind("<Return>", lambda event: self.send_private_message(partner_username, message_entry))

        send_button = ttk.Button(input_frame, text="Отправить", command=lambda: self.send_private_message(partner_username, message_entry))
        send_button.pack(side=tk.RIGHT)

        # Добавляем новую вкладку в Notebook
        tab_id = self.notebook.add(chat_tab_frame, text=partner_username, sticky="nsew") # Имя пользователя как заголовок вкладки
        self.notebook.select(tab_id) # Сразу переключаемся на новую вкладку
        self.current_private_chat_partner = partner_username
        
        # Сохраняем ссылки на виджеты для этого чата
        self.private_chat_tabs[partner_username] = {
            'tab_id': tab_id,
            'text_widget': messages_text_widget,
            'entry_widget': message_entry,
            'frame': chat_tab_frame # Также сохраним ссылку на фрейм вкладки
        }

        # Запрашиваем историю для новой вкладки
        self.request_private_chat_history(partner_username)
        message_entry.focus_set()


    def close_private_chat_tab(self, partner_username):
        """Закрывает вкладку личного чата."""
        if partner_username in self.private_chat_tabs:
            tab_info = self.private_chat_tabs[partner_username]
            self.notebook.forget(tab_info['tab_id']) # Удаляем вкладку из Notebook
            del self.private_chat_tabs[partner_username] # Удаляем из словаря

            # Если закрыли текущую активную вкладку, сбрасываем current_private_chat_partner
            if self.current_private_chat_partner == partner_username:
                self.current_private_chat_partner = None
                # Переключаемся на вкладку "Общий Чат" или "Новый Чат"
                self.notebook.select(self.public_chat_tab)
            
            self.filter_users() # Обновим список пользователей для поиска, если пользователь стал доступен снова

    def request_private_chat_history(self, partner_username):
        if self.connected and self.username:
            try:
                self.client_socket.send(f"HISTORY_REQUEST:{partner_username}".encode('utf-8'))
            except Exception as e:
                print(f"Ошибка при запросе истории чата с {partner_username}: {e}")

    def send_private_message(self, partner_username, entry_widget):
        """Отправляет личное сообщение выбранному пользователю."""
        if not self.connected or not self.username:
            messagebox.showerror("Ошибка", "Вы не подключены или не вошли в систему.", parent=self.master)
            return
        if not partner_username: # Убедимся, что выбран партнер
            messagebox.showwarning("Ошибка", "Выберите пользователя для личного чата.", parent=self.master)
            return

        message = entry_widget.get()
        if message:
            try:
                self.client_socket.send(f"PRIVATE_MSG:{partner_username}:{message}".encode('utf-8'))
                # Отображаем сообщение в активном чате
                self.display_private_message(partner_username, f"Вы: {message}")
                entry_widget.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Ошибка отправки ЛС", f"Не удалось отправить личное сообщение: {e}", parent=self.master)
                self.disconnect_from_server()

    # В этой версии, send_private_message_event больше не нужен напрямую, 
    # так как привязка к <Return> теперь передает partner_username и entry_widget
    # def send_private_message_event(self, event):
    #    self.send_private_message(self.current_private_chat_partner, self.message_entry_private)


    def disconnect_from_server(self, reason="Вы были отключены."):
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

            self.messages_text.config(state='normal')
            self.messages_text.delete(1.0, tk.END)
            self.messages_text.config(state='disabled')

            # Закрываем все динамически созданные вкладки чатов
            for partner in list(self.private_chat_tabs.keys()):
                self.notebook.forget(self.private_chat_tabs[partner]['tab_id'])
                del self.private_chat_tabs[partner]
            
            self.search_entry.delete(0, tk.END)
            self.search_results_listbox.delete(0, tk.END)
            self.filter_users() # Обновим список доступных пользователей

        except Exception as e:
            messagebox.showerror("Ошибка отключения", f"Ошибка при отключении: {e}", parent=self.master)

    def on_closing(self):
        if self.connected:
            self.disconnect_from_server("Закрытие приложения.")
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()