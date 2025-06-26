# client.py
import socket # Импортируем модуль socket для работы с сетевыми соединениями.
import threading # Импортируем модуль threading для создания и управления потоками.
import tkinter as tk # Импортируем библиотеку Tkinter для создания графического интерфейса пользователя.
from tkinter import scrolledtext # Импортируем ScrolledText из Tkinter для текстового поля с прокруткой.
from tkinter import messagebox # Импортируем messagebox из Tkinter для вывода всплывающих сообщений.
from tkinter import ttk # Импортируем ttk (Themed Tkinter) для современных виджетов Tkinter.

HOST = '192.168.9.215' # Определяем IP-адрес хоста сервера, к которому будет подключаться клиент.
PORT = 12345 # Определяем порт, используемый для соединения с сервером.

# --- Обновленные Настройки Стилей и Цветов ---
COLOR_BG_MAIN = "#282C34" # Основной цвет фона приложения (темно-серый).
COLOR_BG_CARD = "#3A3F47" # Цвет фона для "карточек" или секций (чуть светлее основного серого).
COLOR_TEXT_PRIMARY = "#ABB2BF" # Основной цвет текста (светло-серый).
COLOR_TEXT_ACCENT = "#61AFEF" # Акцентный цвет текста, часто используется для заголовков (голубой).
COLOR_PRIMARY_BUTTON = "#61AFEF" # Основной цвет кнопок (голубой).
COLOR_SECONDARY_BUTTON = "#C678DD" # Вторичный цвет кнопок (фиолетовый).
COLOR_HOVER = "#56B6C2" # Цвет при наведении курсора на интерактивные элементы (бирюзовый).
COLOR_ERROR = "#E06C75" # Цвет для сообщений об ошибках (красный).

FONT_FAMILY_TITLE = "Helvetica Neue" # Семейство шрифтов для заголовков.
FONT_FAMILY_TEXT = "Arial" # Семейство шрифтов для основного текста.

FONT_TITLE = (FONT_FAMILY_TITLE, 24, "bold") # Стиль шрифта для главного заголовка.
FONT_HEADING = (FONT_FAMILY_TEXT, 14, "bold") # Стиль шрифта для подзаголовков.
FONT_SUBHEADING = (FONT_FAMILY_TEXT, 12, "bold") # Стиль шрифта для дополнительных подзаголовков.
FONT_NORMAL = (FONT_FAMILY_TEXT, 11) # Стиль шрифта для обычного текста.
FONT_SMALL = (FONT_FAMILY_TEXT, 9) # Стиль шрифта для мелкого текста.
FONT_CHAT = ("Consolas", 10) # Стиль шрифта для области чата (моноширинный).

class ChatClient: # Объявление класса ChatClient, который инкапсулирует логику клиентского приложения.
    def __init__(self, master): # Конструктор класса, принимает главный виджет Tkinter (master).
        self.master = master # Сохраняем ссылку на главный виджет.
        master.title("Мессенджер") # Устанавливаем заголовок окна приложения.
        master.geometry("800x700") # Устанавливаем начальный размер окна.
        master.minsize(650, 550) # Устанавливаем минимальный размер окна.
        master.configure(bg=COLOR_BG_MAIN) # Устанавливаем основной цвет фона окна.

        self.client_socket = None # Инициализируем сокет клиента как None (пока не подключен).
        self.connected = False # Флаг состояния подключения к серверу.
        self.username = "" # Имя пользователя текущего клиента.
        self.current_private_chat_partner = None # Хранит имя пользователя, с которым активен личный чат.

        # Словарь для хранения информации о динамически созданных вкладках личных чатов
        # Ключ: имя пользователя, Значение: {'tab_id': <id вкладки>, 'text_widget': <ScrolledText>}
        self.private_chat_tabs = {} # Словарь для отслеживания открытых личных чатов (вкладок).

        self.all_registered_users = [] # Список всех зарегистрированных пользователей для поиска.

        self.setup_styles() # Вызываем метод для настройки стилей ttk.
        self.create_widgets() # Вызываем метод для создания всех виджетов интерфейса.
        self.show_auth_interface() # Показываем интерфейс авторизации при запуске.

    def setup_styles(self): # Метод для настройки стилей виджетов ttk.
        style = ttk.Style() # Создаем объект Style.
        style.theme_use('clam') # Устанавливаем тему 'clam' для ttk.

        style.configure('.', # Конфигурируем стили по умолчанию для всех виджетов.
                        background=COLOR_BG_MAIN, # Цвет фона.
                        foreground=COLOR_TEXT_PRIMARY, # Цвет текста.
                        font=FONT_NORMAL) # Шрифт.

        style.configure('Card.TFrame', # Стиль для фреймов, имитирующих "карточки".
                        background=COLOR_BG_CARD, # Цвет фона карточки.
                        relief="flat", # Без рельефа.
                        borderwidth=0) # Без рамки.

        style.configure('TButton', # Стиль для стандартных кнопок.
                        background=COLOR_PRIMARY_BUTTON, # Цвет фона кнопки.
                        foreground="#FFFFFF", # Цвет текста кнопки (белый).
                        font=FONT_NORMAL, # Шрифт кнопки.
                        padding=[15, 8], # Внутренние отступы.
                        relief="flat", # Без рельефа.
                        focuscolor=COLOR_PRIMARY_BUTTON) # Цвет фокуса.
        style.map('TButton', # Определяем, как меняется кнопка при наведении/нажатии.
                  background=[('active', COLOR_HOVER), ('pressed', COLOR_SECONDARY_BUTTON)], # Цвет фона при активном/нажатом состоянии.
                  foreground=[('active', "#FFFFFF"), ('pressed', "#FFFFFF")]) # Цвет текста при активном/нажатом состоянии.

        style.configure('Secondary.TButton', # Стиль для вторичных кнопок.
                        background=COLOR_SECONDARY_BUTTON, # Цвет фона.
                        foreground="#FFFFFF", # Цвет текста.
                        font=FONT_NORMAL, # Шрифт.
                        padding=[15, 8], # Отступы.
                        relief="flat", # Без рельефа.
                        focuscolor=COLOR_SECONDARY_BUTTON) # Цвет фокуса.
        style.map('Secondary.TButton', # Определяем, как меняется вторичная кнопка.
                  background=[('active', COLOR_HOVER), ('pressed', COLOR_PRIMARY_BUTTON)], # Цвет фона.
                  foreground=[('active', "#FFFFFF"), ('pressed', "#FFFFFF")]) # Цвет текста.

        style.configure('TEntry', # Стиль для полей ввода текста.
                        fieldbackground=COLOR_BG_CARD, # Цвет фона поля.
                        foreground=COLOR_TEXT_PRIMARY, # Цвет текста.
                        insertbackground=COLOR_TEXT_ACCENT, # Цвет курсора.
                        borderwidth=1, # Ширина рамки.
                        relief="solid", # Тип рельефа рамки.
                        highlightbackground=COLOR_BG_CARD, # Цвет рамки без фокуса.
                        highlightcolor=COLOR_PRIMARY_BUTTON, # Цвет рамки при фокусе.
                        highlightthickness=1, # Толщина рамки.
                        padding=[5, 5]) # Отступы.

        style.configure('TLabel', # Стиль для меток текста.
                        background=COLOR_BG_MAIN, # Цвет фона.
                        foreground=COLOR_TEXT_PRIMARY) # Цвет текста.
        style.configure('Heading.TLabel', # Стиль для заголовков меток.
                        font=FONT_HEADING, # Шрифт.
                        background=COLOR_BG_MAIN, # Цвет фона.
                        foreground=COLOR_TEXT_ACCENT) # Цвет текста.
        style.configure('Subheading.TLabel', # Стиль для подзаголовков меток.
                        font=FONT_SUBHEADING, # Шрифт.
                        background=COLOR_BG_CARD, # Цвет фона.
                        foreground=COLOR_TEXT_PRIMARY) # Цвет текста.

        # Notebook (вкладки)
        style.configure('TNotebook', # Стиль для виджета Notebook (вкладки).
                        background=COLOR_BG_MAIN, # Цвет фона.
                        borderwidth=0, # Без рамки.
                        tabposition='wn', # Вкладки слева (west-north).
                        padding=0) # Без отступов.

        style.configure('TNotebook.Tab', # Стиль для отдельных вкладок Notebook.
                        background=COLOR_BG_CARD, # Цвет фона вкладки.
                        foreground=COLOR_TEXT_PRIMARY, # Цвет текста вкладки.
                        font=FONT_SUBHEADING, # Шрифт вкладки.
                        padding=[15, 10], # Увеличиваем отступы вкладок.
                        borderwidth=0, # Без рамки.
                        relief="flat", # Без рельефа.
                        focuscolor="") # Убираем пунктирную рамку фокуса для вкладки.

        style.map('TNotebook.Tab', # Определяем, как меняется вкладка при выборе/активации.
                  background=[('selected', COLOR_PRIMARY_BUTTON), ('active', COLOR_HOVER)], # Цвет фона при выбранном/активном состоянии.
                  foreground=[('selected', "#FFFFFF"), ('active', "#FFFFFF")], # Цвет текста при выбранном/активном состоянии.
                  expand=[('selected', [0,0,0,0])]) # Не расширять вкладку при выборе.

        style.layout("TNotebook.Tab", [ # Определяем компоновку вкладки.
            ("TNotebook.tab", { # Основной элемент вкладки.
                "sticky": "nswe", # Растягивается по всем сторонам.
                "children": [ # Дочерние элементы.
                    ("TNotebook.padding", { # Отступ внутри вкладки.
                        "sticky": "nswe",
                        "children": [
                            ("TNotebook.focus", { # Область фокуса.
                                "sticky": "nswe",
                                "children": [
                                    ("TNotebook.label", {"sticky": "nswe"}) # Метка вкладки растягивается.
                                ]
                            })
                        ]
                    })
                ]
            })
        ])
        style.configure('TNotebook.Tab', width=18) # Фиксированная ширина вкладок в символах.

        # Скроллбары
        style.configure("Vertical.TScrollbar", # Стиль для вертикальных скроллбаров.
                        background=COLOR_BG_MAIN, # Цвет фона скроллбара.
                        troughcolor=COLOR_BG_CARD, # Цвет "желоба" скроллбара.
                        bordercolor=COLOR_BG_MAIN, # Цвет рамки.
                        arrowcolor=COLOR_TEXT_PRIMARY, # Цвет стрелок.
                        relief="flat") # Без рельефа.
        style.map("Vertical.TScrollbar", # Определяем, как меняется скроллбар при наведении.
                  background=[('active', COLOR_HOVER)]) # Цвет фона при активном состоянии.

    def create_widgets(self): # Метод для создания всех виджетов пользовательского интерфейса.
        # --- Фрейм для регистрации/входа ---
        self.auth_frame = ttk.Frame(self.master, style='Card.TFrame', padding=30) # Создаем фрейм для авторизации.
        
        ttk.Label(self.auth_frame, text="Добро пожаловать в Мессенджер", font=FONT_TITLE, # Заголовок "Добро пожаловать".
                  background=COLOR_BG_CARD, foreground=COLOR_TEXT_ACCENT).pack(pady=(0, 25)) # Размещаем заголовок.
        
        ttk.Label(self.auth_frame, text="Имя пользователя:", font=FONT_NORMAL, # Метка "Имя пользователя".
                  background=COLOR_BG_CARD, foreground=COLOR_TEXT_PRIMARY).pack(pady=(5, 0), anchor="w") # Размещаем метку.
        self.auth_username_entry = ttk.Entry(self.auth_frame, font=FONT_NORMAL) # Поле ввода имени пользователя.
        self.auth_username_entry.pack(fill=tk.X, padx=0, pady=5) # Размещаем поле ввода.

        ttk.Label(self.auth_frame, text="Пароль:", font=FONT_NORMAL, # Метка "Пароль".
                  background=COLOR_BG_CARD, foreground=COLOR_TEXT_PRIMARY).pack(pady=(15, 0), anchor="w") # Размещаем метку.
        self.auth_password_entry = ttk.Entry(self.auth_frame, show="*", font=FONT_NORMAL) # Поле ввода пароля (скрытый ввод).
        self.auth_password_entry.pack(fill=tk.X, padx=0, pady=5) # Размещаем поле ввода.

        self.login_button = ttk.Button(self.auth_frame, text="Войти", command=self.send_login_request, style='TButton') # Кнопка "Войти".
        self.login_button.pack(fill=tk.X, pady=(25, 10)) # Размещаем кнопку.

        self.register_button = ttk.Button(self.auth_frame, text="Зарегистрироваться", command=self.send_register_request, style='Secondary.TButton') # Кнопка "Зарегистрироваться".
        self.register_button.pack(fill=tk.X, pady=(10, 0)) # Размещаем кнопку.

        # --- Основной фрейм чата с вкладками ---
        self.chat_main_frame = ttk.Frame(self.master, style='TFrame') # Создаем основной фрейм для интерфейса чата.

        self.notebook = ttk.Notebook(self.chat_main_frame) # Создаем виджет Notebook (вкладки).
        self.notebook.pack(fill=tk.BOTH, expand=True) # Размещаем Notebook, чтобы он занимал все доступное пространство.

        # --- Вкладка "Общий Чат" ---
        self.public_chat_tab = ttk.Frame(self.notebook, style='Card.TFrame', padding=10) # Создаем фрейм для вкладки общего чата.
        self.notebook.add(self.public_chat_tab, text="Общий Чат", sticky="nsew") # Добавляем фрейм как вкладку в Notebook.
        self.public_chat_tab.grid_rowconfigure(0, weight=1) # Настраиваем растягивание строк в сетке.
        self.public_chat_tab.grid_columnconfigure(0, weight=1) # Настраиваем растягивание столбцов в сетке.

        ttk.Label(self.public_chat_tab, text="Общий Чат", font=FONT_HEADING, # Заголовок вкладки "Общий Чат".
                  background=COLOR_BG_CARD, foreground=COLOR_TEXT_ACCENT).grid(row=0, column=0, sticky="ew", padx=5, pady=5) # Размещаем заголовок.

        self.messages_text = scrolledtext.ScrolledText( # Создаем текстовое поле с прокруткой для сообщений общего чата.
            self.public_chat_tab, # Родительский виджет.
            wrap=tk.WORD, # Перенос строк по словам.
            state='disabled', # Изначально текстовое поле отключено (только для чтения).
            font=FONT_CHAT, # Шрифт.
            bg=COLOR_BG_MAIN, # Цвет фона.
            fg=COLOR_TEXT_PRIMARY, # Цвет текста.
            insertbackground=COLOR_TEXT_PRIMARY, # Цвет курсора.
            borderwidth=0, # Без рамки.
            relief="flat", # Без рельефа.
            highlightbackground=COLOR_BG_MAIN, # Цвет рамки без фокуса.
            highlightthickness=0 # Толщина рамки без фокуса.
        )
        self.messages_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5) # Размещаем текстовое поле.

        self.input_frame_public = ttk.Frame(self.public_chat_tab, style='Card.TFrame') # Фрейм для поля ввода и кнопки отправки.
        self.input_frame_public.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(5, 0)) # Размещаем фрейм.

        self.message_entry_public = ttk.Entry(self.input_frame_public, font=FONT_NORMAL) # Поле ввода сообщения для общего чата.
        self.message_entry_public.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5)) # Размещаем поле ввода.
        self.message_entry_public.bind("<Return>", self.send_public_message_event) # Привязываем отправку по Enter.

        self.send_button_public = ttk.Button(self.input_frame_public, text="Отправить", command=self.send_public_message) # Кнопка "Отправить" для общего чата.
        self.send_button_public.pack(side=tk.RIGHT) # Размещаем кнопку.

        # --- Вкладка "Начать новый чат" (раньше была "Личные сообщения") ---
        # Эта вкладка будет использоваться только для поиска пользователей и создания НОВЫХ чатов.
        # Сами чаты будут отдельными вкладками.
        self.new_private_chat_tab = ttk.Frame(self.notebook, style='Card.TFrame', padding=10) # Фрейм для вкладки нового чата/поиска.
        self.notebook.add(self.new_private_chat_tab, text="Новый Чат / Поиск") # Добавляем как вкладку.
        
        self.new_private_chat_tab.grid_columnconfigure(0, weight=1) # Настраиваем растягивание столбцов.
        self.new_private_chat_tab.grid_rowconfigure(2, weight=1) # Listbox растягивается.

        ttk.Label(self.new_private_chat_tab, text="Найти пользователя для чата:", font=FONT_HEADING, # Заголовок для поиска пользователей.
                  background=COLOR_BG_CARD, foreground=COLOR_TEXT_ACCENT).grid(row=0, column=0, sticky="ew", padx=5, pady=5) # Размещаем заголовок.

        self.search_entry = ttk.Entry(self.new_private_chat_tab, font=FONT_NORMAL) # Поле ввода для поиска пользователей.
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5) # Размещаем поле ввода.
        self.search_entry.bind("<KeyRelease>", self.filter_users) # Привязываем фильтрацию по мере ввода.

        self.search_results_listbox = tk.Listbox( # Список для отображения результатов поиска пользователей.
            self.new_private_chat_tab, # Родительский виджет.
            font=FONT_NORMAL, # Шрифт.
            height=10, # Высота списка.
            bg=COLOR_BG_MAIN, # Цвет фона.
            fg=COLOR_TEXT_PRIMARY, # Цвет текста.
            selectbackground=COLOR_PRIMARY_BUTTON, # Цвет выделения.
            selectforeground="#FFFFFF", # Цвет текста при выделении.
            borderwidth=0, # Без рамки.
            relief="flat", # Без рельефа.
            highlightbackground=COLOR_BG_MAIN, # Цвет рамки без фокуса.
            highlightthickness=0 # Толщина рамки без фокуса.
        )
        self.search_results_listbox.grid(row=2, column=0, sticky="nswe", padx=5, pady=5) # Размещаем список.
        self.search_results_listbox.bind("<<ListboxSelect>>", self.create_or_switch_private_chat_tab) # Привязываем создание/переключение чата по выбору.
        
        self.refresh_users_button = ttk.Button(self.new_private_chat_tab, text="Обновить список пользователей", command=self.request_user_list, style='Secondary.TButton') # Кнопка "Обновить список пользователей".
        self.refresh_users_button.grid(row=3, column=0, sticky="ew", padx=5, pady=(5,0)) # Размещаем кнопку.

        # Кнопка отключения (внизу основного окна)
        self.disconnect_button = ttk.Button(self.master, text="Отключиться", command=self.disconnect_from_server, style='Secondary.TButton') # Кнопка "Отключиться".
        
        # Разделитель между вкладками и кнопкой отключения
        self.separator = ttk.Separator(self.master, orient='horizontal') # Создаем горизонтальный разделитель.

    def show_auth_interface(self): # Метод для отображения интерфейса авторизации.
        self.chat_main_frame.pack_forget() # Скрываем основной фрейм чата.
        self.disconnect_button.pack_forget() # Скрываем кнопку отключения.
        self.separator.pack_forget() # Скрываем разделитель.

        self.auth_frame.pack(expand=True, fill=tk.BOTH, padx=70, pady=70) # Размещаем фрейм авторизации по центру.
        self.master.geometry("450x550") # Устанавливаем размер окна для авторизации.
        self.master.resizable(False, False) # Запрещаем изменение размера окна.
        self.auth_username_entry.focus_set() # Устанавливаем фокус на поле ввода имени пользователя.
        self.auth_password_entry.delete(0, tk.END) # Очищаем поле пароля.

    def show_chat_interface(self): # Метод для отображения интерфейса чата.
        self.auth_frame.pack_forget() # Скрываем фрейм авторизации.
        self.chat_main_frame.pack(fill=tk.BOTH, expand=True) # Размещаем основной фрейм чата.
        self.separator.pack(fill=tk.X, padx=10, pady=(0,5)) # Размещаем разделитель.
        self.disconnect_button.pack(side=tk.BOTTOM, pady=(0, 10)) # Размещаем кнопку отключения.
        
        self.master.geometry("800x700") # Устанавливаем размер окна для чата.
        self.master.resizable(True, True) # Разрешаем изменение размера окна.
        self.message_entry_public.focus_set() # Устанавливаем фокус на поле ввода публичного сообщения.
        self.request_user_list() # Запрашиваем список пользователей при входе.

    def display_public_message(self, message): # Метод для отображения публичных сообщений.
        self.messages_text.config(state='normal') # Разрешаем редактирование текстового поля.
        self.messages_text.insert(tk.END, message + "\n") # Вставляем сообщение в конец.
        self.messages_text.yview(tk.END) # Прокручиваем до конца.
        self.messages_text.config(state='disabled') # Запрещаем редактирование текстового поля.

    def display_private_message(self, partner_username, message): # Метод для отображения личных сообщений.
        """Отображает сообщение в текстовом поле личного чата.
           Создает вкладку чата, если ее нет, и добавляет сообщение."""
        self.master.after(0, lambda: self._handle_incoming_private_message_thread_safe(partner_username, message)) # Выполняем в основном потоке Tkinter.

    def _handle_incoming_private_message_thread_safe(self, partner_username, message): # Вспомогательный метод для потокобезопасной обработки личных сообщений.
        if partner_username not in self.private_chat_tabs: # Если вкладки для этого пользователя нет.
            self.create_or_switch_private_chat_tab(partner_username=partner_username) # Создаем или переключаемся на вкладку.

        # Добавляем сообщение в соответствующий текстовый виджет
        text_widget = self.private_chat_tabs[partner_username]['text_widget'] # Получаем текстовый виджет для чата.
        text_widget.config(state='normal') # Разрешаем редактирование.
        text_widget.insert(tk.END, message + "\n") # Вставляем сообщение.
        text_widget.yview(tk.END) # Прокручиваем до конца.
        text_widget.config(state='disabled') # Запрещаем редактирование.

        # Если это новый чат или сообщение пришло от неактивного чата, можно подсветить вкладку
        if self.notebook.tab(self.notebook.select(), "text") != partner_username: # Если текущая вкладка не соответствует.
            # В ttk.Notebook нет прямого метода для "подсветки" вкладки
            # Можно изменить текст вкладки (добавить *) или цвет (если это возможно через стили)
            pass # Пока не реализуем индикатор непрочитанных сообщений, т.к. это усложнит стили

    def connect_to_server_once(self): # Метод для однократного подключения к серверу.
        if not self.client_socket or not self.connected: # Если сокет еще не создан или не подключен.
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Создаем TCP/IP сокет.
                self.client_socket.connect((HOST, PORT)) # Подключаемся к серверу.
                self.connected = True # Устанавливаем флаг подключения.
                receive_thread = threading.Thread(target=self.receive_messages) # Создаем новый поток для получения сообщений.
                receive_thread.daemon = True # Делаем поток демоном (завершится при завершении основного процесса).
                receive_thread.start() # Запускаем поток.
                return True # Возвращаем True, если подключение успешно.
            except ConnectionRefusedError: # Обработка ошибки, если сервер не доступен.
                messagebox.showerror("Ошибка подключения", "Сервер не запущен или недоступен.", parent=self.master) # Показываем сообщение об ошибке.
                return False # Возвращаем False.
            except Exception as e: # Обработка других возможных ошибок.
                messagebox.showerror("Ошибка подключения", f"Произошла ошибка при подключении: {e}", parent=self.master) # Показываем сообщение об ошибке.
                return False # Возвращаем False.
        return True # Возвращаем True, если уже подключены.

    def receive_messages(self): # Метод для получения сообщений от сервера в отдельном потоке.
        while self.connected: # Цикл, пока клиент подключен.
            try:
                raw_data = self.client_socket.recv(4096) # Получаем данные от сервера (до 4096 байт).
                if not raw_data: # Если данных нет, значит соединение разорвано.
                    self.disconnect_from_server("Сервер отключился.") # Отключаемся от сервера.
                    break # Выходим из цикла.
                message = raw_data.decode('utf-8') # Декодируем полученные данные в строку UTF-8.

                if message.startswith("REGISTER_SUCCESS"): # Если сообщение начинается с "REGISTER_SUCCESS".
                    self.master.after(0, lambda: self.display_public_message("--- Регистрация прошла успешно! Теперь вы можете войти. ---")) # Отображаем сообщение об успешной регистрации.
                    self.master.after(0, lambda: self.auth_username_entry.delete(0, tk.END)) # Очищаем поле имени пользователя.
                    self.master.after(0, lambda: self.auth_password_entry.delete(0, tk.END)) # Очищаем поле пароля.
                    self.master.after(0, lambda: self.auth_username_entry.focus_set()) # Устанавливаем фокус на поле имени пользователя.
                elif message.startswith("REGISTER_FAIL:"): # Если сообщение об ошибке регистрации.
                    error_msg = message.split(':', 1)[1] # Извлекаем текст ошибки.
                    messagebox.showerror("Ошибка регистрации", error_msg, parent=self.master) # Показываем сообщение об ошибке.
                elif message.startswith("LOGIN_SUCCESS:"): # Если сообщение об успешном входе.
                    self.username = message.split(':', 1)[1] # Извлекаем имя пользователя.
                    self.master.after(0, self.show_chat_interface) # Показываем интерфейс чата.
                    self.master.after(0, lambda: self.display_public_message(f"--- Добро пожаловать в чат, {self.username}! ---")) # Приветствуем пользователя.
                elif message.startswith("LOGIN_FAIL:"): # Если сообщение об ошибке входа.
                    error_msg = message.split(':', 1)[1] # Извлекаем текст ошибки.
                    messagebox.showerror("Ошибка входа", error_msg, parent=self.master) # Показываем сообщение об ошибке.
                elif message.startswith("ERROR:"): # Если общее сообщение об ошибке.
                    error_msg = message.split(':', 1)[1] # Извлекаем текст ошибки.
                    self.display_public_message(f"[ОШИБКА] {error_msg}") # Отображаем ошибку в публичном чате.
                    messagebox.showerror("Ошибка", error_msg, parent=self.master) # Показываем сообщение об ошибке.
                elif message.startswith("PRIVATE_FROM:"): # Если получено личное сообщение.
                    parts = message.split(':', 2) # Разделяем сообщение.
                    if len(parts) >= 3: # Проверяем корректность формата.
                        sender = parts[1] # Извлекаем отправителя.
                        private_msg = parts[2] # Извлекаем само сообщение.
                        # Убедимся, что создание виджета и отображение сообщения происходит в главном потоке Tkinter
                        self.master.after(0, self.display_private_message, sender, f"{sender}: {private_msg}") # Отображаем личное сообщение.
                elif message.startswith("HISTORY_RESPONSE:"): # Если получен ответ с историей чата.
                    parts = message.split(':', 2) # Разделяем сообщение.
                    if len(parts) >= 3: # Проверяем корректность формата.
                        partner_user = parts[1] # Извлекаем имя партнера по чату.
                        history_content = parts[2] # Извлекаем содержимое истории.
                        if partner_user in self.private_chat_tabs: # Если вкладка для этого партнера существует.
                            text_widget = self.private_chat_tabs[partner_user]['text_widget'] # Получаем текстовый виджет.
                            self.master.after(0, lambda: self.load_private_chat_history_to_widget(text_widget, history_content)) # Загружаем историю.
                elif message.startswith("USER_LIST:"): # Если получен список пользователей.
                    user_string = message.split(':', 1)[1] # Извлекаем строку с пользователями.
                    self.all_registered_users = sorted([u for u in user_string.split(',') if u and u != self.username]) # Парсим и сортируем список.
                    self.master.after(0, self.filter_users) # Обновляем список пользователей для поиска.
                else:
                    self.master.after(0, self.display_public_message, message) # В противном случае, отображаем как публичное сообщение.

            except ConnectionResetError: # Обработка ошибки, если соединение сброшено.
                self.disconnect_from_server("Соединение с сервером потеряно.") # Отключаемся от сервера.
                break # Выходим из цикла.
            except OSError: # Обработка ошибки ОС (например, сокет закрыт).
                break # Выходим из цикла.
            except Exception as e: # Обработка других возможных ошибок.
                print(f"Ошибка при получении сообщения: {e}") # Выводим ошибку в консоль.
                self.disconnect_from_server(f"Ошибка: {e}") # Отключаемся от сервера.
                break # Выходим из цикла.

    def load_private_chat_history_to_widget(self, text_widget, history_content): # Метод для загрузки истории в виджет чата.
        text_widget.config(state='normal') # Разрешаем редактирование.
        text_widget.delete(1.0, tk.END) # Очищаем текстовое поле.
        text_widget.insert(tk.END, history_content + "\n") # Вставляем историю.
        text_widget.yview(tk.END) # Прокручиваем до конца.
        text_widget.config(state='disabled') # Запрещаем редактирование.

    def send_register_request(self): # Метод для отправки запроса на регистрацию.
        username = self.auth_username_entry.get().strip() # Получаем имя пользователя из поля ввода.
        password = self.auth_password_entry.get().strip() # Получаем пароль из поля ввода.
        if not username or not password: # Проверяем, что поля не пустые.
            messagebox.showwarning("Предупреждение", "Пожалуйста, введите имя пользователя и пароль для регистрации.", parent=self.master) # Предупреждение.
            return # Выходим из метода.

        if self.connect_to_server_once(): # Пытаемся подключиться к серверу, если еще не подключены.
            try:
                self.client_socket.send(f"REGISTER:{username}:{password}".encode('utf-8')) # Отправляем запрос на регистрацию.
            except Exception as e: # Обработка ошибок отправки.
                messagebox.showerror("Ошибка регистрации", f"Не удалось отправить запрос на регистрацию: {e}", parent=self.master) # Сообщение об ошибке.
                self.disconnect_from_server() # Отключаемся от сервера.

    def send_login_request(self): # Метод для отправки запроса на вход.
        username = self.auth_username_entry.get().strip() # Получаем имя пользователя.
        password = self.auth_password_entry.get().strip() # Получаем пароль.
        if not username or not password: # Проверяем, что поля не пустые.
            messagebox.showwarning("Предупреждение", "Пожалуйста, введите имя пользователя и пароль для входа.", parent=self.master) # Предупреждение.
            return # Выходим из метода.

        if self.connect_to_server_once(): # Пытаемся подключиться к серверу.
            try:
                self.client_socket.send(f"LOGIN:{username}:{password}".encode('utf-8')) # Отправляем запрос на вход.
            except Exception as e: # Обработка ошибок отправки.
                messagebox.showerror("Ошибка входа", f"Не удалось отправить запрос на вход: {e}", parent=self.master) # Сообщение об ошибке.
                self.disconnect_from_server() # Отключаемся от сервера.

    def send_public_message(self): # Метод для отправки публичного сообщения.
        if not self.connected or not self.username: # Проверяем, подключен ли клиент и авторизован ли.
            messagebox.showerror("Ошибка", "Вы не подключены или не вошли в систему.", parent=self.master) # Сообщение об ошибке.
            return # Выходим.

        message = self.message_entry_public.get() # Получаем текст сообщения.
        if message: # Если сообщение не пустое.
            try:
                self.client_socket.send(f"CHAT:{message}".encode('utf-8')) # Отправляем сообщение на сервер.
                self.display_public_message(f"Вы: {message}") # Отображаем свое сообщение в чате.
                self.message_entry_public.delete(0, tk.END) # Очищаем поле ввода.
            except Exception as e: # Обработка ошибок отправки.
                messagebox.showerror("Ошибка отправки", f"Не удалось отправить сообщение: {e}", parent=self.master) # Сообщение об ошибке.
                self.disconnect_from_server() # Отключаемся от сервера.

    def send_public_message_event(self, event): # Метод-обработчик события (например, нажатия Enter).
        self.send_public_message() # Вызываем метод отправки публичного сообщения.

    def request_user_list(self): # Метод для запроса списка пользователей.
        if self.connected and self.username: # Проверяем, подключен ли клиент и авторизован ли.
            try:
                self.client_socket.send("GET_USERS".encode('utf-8')) # Отправляем запрос на список пользователей.
            except Exception as e: # Обработка ошибок.
                print(f"Ошибка при запросе списка пользователей: {e}") # Выводим ошибку в консоль.

    def filter_users(self, event=None): # Метод для фильтрации списка пользователей при поиске.
        search_query = self.search_entry.get().strip().lower() # Получаем поисковый запрос.
        self.search_results_listbox.delete(0, tk.END) # Очищаем список результатов.
        for user in sorted(self.all_registered_users): # Перебираем всех зарегистрированных пользователей.
            # Показываем только тех, с кем еще нет открытой вкладки
            if search_query in user.lower() and user not in self.private_chat_tabs: # Если запрос найден в имени и нет открытой вкладки.
                self.search_results_listbox.insert(tk.END, user) # Добавляем пользователя в список результатов.

    def create_or_switch_private_chat_tab(self, event=None, partner_username=None): # Метод для создания или переключения на вкладку личного чата.
        """Создает новую вкладку для личного чата или переключается на существующую."""
        if partner_username is None: # Если вызов идет от Listbox (клик пользователя)
            selected_indices = self.search_results_listbox.curselection() # Получаем индекс выбранного элемента.
            if not selected_indices: # Если ничего не выбрано.
                return # Выходим.
            index = selected_indices[0] # Получаем первый выбранный индекс.
            partner_username = self.search_results_listbox.get(index) # Получаем имя пользователя.

            # Очищаем поле поиска и список результатов после выбора
            self.search_entry.delete(0, tk.END) # Очищаем поле поиска.
            self.filter_users() # Обновим список, чтобы убрать выбранного пользователя

        if partner_username == self.username: # Если пользователь пытается начать чат с самим собой.
            messagebox.showwarning("Ошибка", "Вы не можете начать чат с самим собой.", parent=self.master) # Предупреждение.
            return # Выходим.

        if partner_username in self.private_chat_tabs: # Если вкладка уже существует.
            # Если вкладка уже существует, просто переключаемся на нее
            self.notebook.select(self.private_chat_tabs[partner_username]['tab_id']) # Переключаемся на вкладку.
            self.current_private_chat_partner = partner_username # Обновляем текущего партнера.
            self.private_chat_tabs[partner_username]['entry_widget'].focus_set() # Устанавливаем фокус на поле ввода.
            return # Выходим.

        # --- Создаем новую вкладку для личного чата ---
        chat_tab_frame = ttk.Frame(self.notebook, style='Card.TFrame', padding=10) # Создаем новый фрейм для вкладки.
        
        # Заголовок чата (можно сделать динамическим, включающим статус)
        chat_header_label = ttk.Label(chat_tab_frame, text=f"Личный чат с: {partner_username}", font=FONT_HEADING, # Заголовок чата.
                                      background=COLOR_BG_CARD, foreground=COLOR_TEXT_ACCENT) # Стили.
        chat_header_label.pack(side=tk.TOP, fill=tk.X, pady=5) # Размещаем заголовок.

        # Кнопка закрытия вкладки (находится рядом с заголовком)
        # Это не стандартная функциональность ttk.Notebook, но можно реализовать
        # через создание фрейма заголовка или добавлением кнопки внутри вкладки.
        # Для простоты, пока сделаем кнопку закрытия внутри самой вкладки вверху.
        close_button = ttk.Button(chat_tab_frame, text="X", width=3, style='Secondary.TButton', # Кнопка закрытия вкладки.
                                  command=lambda p=partner_username: self.close_private_chat_tab(p)) # Привязываем закрытие вкладки.
        close_button.place(relx=1.0, rely=0, anchor="ne", x=-5, y=5) # Размещаем кнопку в правом верхнем углу.

        # Текстовое поле для сообщений чата
        messages_text_widget = scrolledtext.ScrolledText( # Текстовое поле для личных сообщений.
            chat_tab_frame, # Родительский виджет.
            wrap=tk.WORD, # Перенос строк.
            state='disabled', # Только для чтения.
            font=FONT_CHAT, # Шрифт.
            bg=COLOR_BG_MAIN, # Цвет фона.
            fg=COLOR_TEXT_PRIMARY, # Цвет текста.
            insertbackground=COLOR_TEXT_PRIMARY, # Цвет курсора.
            borderwidth=0, # Без рамки.
            relief="flat", # Без рельефа.
            highlightbackground=COLOR_BG_MAIN, # Цвет рамки.
            highlightthickness=0 # Толщина рамки.
        )
        messages_text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) # Размещаем текстовое поле.

        # Поле ввода сообщения и кнопка отправки
        input_frame = ttk.Frame(chat_tab_frame, style='Card.TFrame') # Фрейм для поля ввода и кнопки.
        input_frame.pack(fill=tk.X, pady=(5, 0), padx=5) # Размещаем фрейм.

        message_entry = ttk.Entry(input_frame, font=FONT_NORMAL) # Поле ввода для личных сообщений.
        message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5)) # Размещаем поле ввода.
        message_entry.bind("<Return>", lambda event: self.send_private_message(partner_username, message_entry)) # Привязываем отправку по Enter.

        send_button = ttk.Button(input_frame, text="Отправить", command=lambda: self.send_private_message(partner_username, message_entry)) # Кнопка "Отправить".
        send_button.pack(side=tk.RIGHT) # Размещаем кнопку.

        # Добавляем новую вкладку в Notebook
        tab_id = self.notebook.add(chat_tab_frame, text=partner_username, sticky="nsew") # Добавляем новую вкладку.
        self.notebook.select(tab_id) # Сразу переключаемся на новую вкладку.
        self.current_private_chat_partner = partner_username # Обновляем текущего партнера.
        
        # Сохраняем ссылки на виджеты для этого чата
        self.private_chat_tabs[partner_username] = { # Сохраняем информацию о новой вкладке.
            'tab_id': tab_id, # ID вкладки.
            'text_widget': messages_text_widget, # Виджет текста.
            'entry_widget': message_entry, # Виджет поля ввода.
            'frame': chat_tab_frame # Фрейм вкладки.
        }

        # Запрашиваем историю для новой вкладки
        self.request_private_chat_history(partner_username) # Запрашиваем историю чата.
        message_entry.focus_set() # Устанавливаем фокус на поле ввода.


    def close_private_chat_tab(self, partner_username): # Метод для закрытия вкладки личного чата.
        """Закрывает вкладку личного чата."""
        if partner_username in self.private_chat_tabs: # Если вкладка для этого пользователя существует.
            tab_info = self.private_chat_tabs[partner_username] # Получаем информацию о вкладке.
            self.notebook.forget(tab_info['tab_id']) # Удаляем вкладку из Notebook.
            del self.private_chat_tabs[partner_username] # Удаляем из словаря.

            # Если закрыли текущую активную вкладку, сбрасываем current_private_chat_partner
            if self.current_private_chat_partner == partner_username: # Если закрыта активная вкладка.
                self.current_private_chat_partner = None # Сбрасываем текущего партнера.
                # Переключаемся на вкладку "Общий Чат" или "Новый Чат"
                self.notebook.select(self.public_chat_tab) # Переключаемся на вкладку публичного чата.
            
            self.filter_users() # Обновим список пользователей для поиска, если пользователь стал доступен снова

    def request_private_chat_history(self, partner_username): # Метод для запроса истории личного чата.
        if self.connected and self.username: # Если подключен и авторизован.
            try:
                self.client_socket.send(f"HISTORY_REQUEST:{partner_username}".encode('utf-8')) # Отправляем запрос истории.
            except Exception as e: # Обработка ошибок.
                print(f"Ошибка при запросе истории чата с {partner_username}: {e}") # Выводим ошибку.

    def send_private_message(self, partner_username, entry_widget): # Метод для отправки личного сообщения.
        """Отправляет личное сообщение выбранному пользователю."""
        if not self.connected or not self.username: # Если не подключен или не авторизован.
            messagebox.showerror("Ошибка", "Вы не подключены или не вошли в систему.", parent=self.master) # Сообщение об ошибке.
            return # Выходим.
        if not partner_username: # Если партнер не выбран.
            messagebox.showwarning("Ошибка", "Выберите пользователя для личного чата.", parent=self.master) # Предупреждение.
            return # Выходим.

        message = entry_widget.get() # Получаем текст сообщения.
        if message: # Если сообщение не пустое.
            try:
                self.client_socket.send(f"PRIVATE_MSG:{partner_username}:{message}".encode('utf-8')) # Отправляем личное сообщение.
                # Отображаем сообщение в активном чате
                self.display_private_message(partner_username, f"Вы: {message}") # Отображаем свое сообщение.
                entry_widget.delete(0, tk.END) # Очищаем поле ввода.
            except Exception as e: # Обработка ошибок.
                messagebox.showerror("Ошибка отправки ЛС", f"Не удалось отправить личное сообщение: {e}", parent=self.master) # Сообщение об ошибке.
                self.disconnect_from_server() # Отключаемся от сервера.

    # В этой версии, send_private_message_event больше не нужен напрямую, 
    # так как привязка к <Return> теперь передает partner_username и entry_widget
    # def send_private_message_event(self, event):
    #    self.send_private_message(self.current_private_chat_partner, self.message_entry_private)


    def disconnect_from_server(self, reason="Вы были отключены."): # Метод для отключения от сервера.
        if not self.connected: # Если уже не подключен.
            return # Выходим.

        try:
            self.connected = False # Сбрасываем флаг подключения.
            if self.client_socket: # Если сокет существует.
                self.client_socket.close() # Закрываем сокет.
                self.client_socket = None # Сбрасываем сокет.
            self.display_public_message(f"--- Отключено от сервера: {reason} ---") # Отображаем сообщение об отключении.
            self.show_auth_interface() # Показываем интерфейс авторизации.
            self.username = "" # Сбрасываем имя пользователя.
            self.current_private_chat_partner = None # Сбрасываем текущего партнера.

            self.messages_text.config(state='normal') # Разрешаем редактирование публичного чата.
            self.messages_text.delete(1.0, tk.END) # Очищаем публичный чат.
            self.messages_text.config(state='disabled') # Запрещаем редактирование.

            # Закрываем все динамически созданные вкладки чатов
            for partner in list(self.private_chat_tabs.keys()): # Перебираем все открытые личные чаты.
                self.notebook.forget(self.private_chat_tabs[partner]['tab_id']) # Удаляем вкладку.
                del self.private_chat_tabs[partner] # Удаляем из словаря.
            
            self.search_entry.delete(0, tk.END) # Очищаем поле поиска.
            self.search_results_listbox.delete(0, tk.END) # Очищаем список результатов поиска.
            self.filter_users() # Обновим список доступных пользователей

        except Exception as e: # Обработка ошибок отключения.
            messagebox.showerror("Ошибка отключения", f"Ошибка при отключении: {e}", parent=self.master) # Сообщение об ошибке.

    def on_closing(self): # Метод, вызываемый при закрытии окна приложения.
        if self.connected: # Если клиент подключен.
            self.disconnect_from_server("Закрытие приложения.") # Отключаемся от сервера с сообщением.
        self.master.destroy() # Уничтожаем главное окно Tkinter.


if __name__ == "__main__": # Точка входа в программу, если файл запускается напрямую.
    root = tk.Tk() # Создаем главное окно Tkinter.
    app = ChatClient(root) # Создаем экземпляр класса ChatClient.
    root.protocol("WM_DELETE_WINDOW", app.on_closing) # Привязываем метод on_closing к событию закрытия окна.
    root.mainloop() # Запускаем основной цикл Tkinter для обработки событий.
