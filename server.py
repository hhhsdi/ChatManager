# server.py
import socket # Импортируем модуль socket для работы с сетевыми соединениями.
import threading # Импортируем модуль threading для создания и управления потоками.
import sqlite3 # Импортируем модуль sqlite3 для работы с базой данных SQLite.
import hashlib # Импортируем модуль hashlib для хеширования паролей.
import time # Импортируем модуль time для получения меток времени.

HOST = '192.168.9.215' # Определяем IP-адрес хоста, на котором будет запущен сервер.
PORT = 12345 # Определяем порт, который будет слушать сервер.

# Словарь для хранения активных клиентских сокетов, где ключ - имя пользователя, значение - сокет.
# Это позволит быстро найти сокет по имени получателя для личных сообщений.
active_clients = {} # {username: client_socket} - Отображение имени пользователя на его сокет.
client_sockets_map = {} # {client_socket: username} - Обратное отображение сокета на имя пользователя.

# --- Функции для работы с базой данных SQLite ---

def init_db():
    """Инициализирует базу данных и создает таблицы пользователей и личных сообщений, если их нет."""
    conn = sqlite3.connect('chat_users.db') # Устанавливаем соединение с базой данных 'chat_users.db' (создаст, если нет).
    cursor = conn.cursor() # Создаем объект курсора для выполнения SQL-запросов.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, # Уникальный идентификатор пользователя (автоинкремент).
            username TEXT UNIQUE NOT NULL, # Имя пользователя (уникальное, не может быть пустым).
            password_hash TEXT NOT NULL # Хеш пароля пользователя (не может быть пустым).
        )
    ''') # Выполняем SQL-запрос для создания таблицы 'users', если она не существует.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS private_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, # Уникальный идентификатор сообщения.
            sender_username TEXT NOT NULL, # Имя пользователя отправителя.
            receiver_username TEXT NOT NULL, # Имя пользователя получателя.
            message TEXT NOT NULL, # Текст сообщения.
            timestamp TEXT NOT NULL, # Метка времени отправки сообщения.
            FOREIGN KEY (sender_username) REFERENCES users(username), # Внешний ключ, ссылающийся на username в таблице users.
            FOREIGN KEY (receiver_username) REFERENCES users(username) # Внешний ключ, ссылающийся на username в таблице users.
        )
    ''') # Выполняем SQL-запрос для создания таблицы 'private_messages', если она не существует.
    conn.commit() # Применяем изменения к базе данных.
    conn.close() # Закрываем соединение с базой данных.
    print("База данных SQLite инициализирована.") # Выводим сообщение об успешной инициализации.

def hash_password(password):
    """Хеширует пароль с использованием SHA256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest() # Кодируем пароль в UTF-8, хешируем SHA256 и возвращаем в виде шестнадцатеричной строки.

def register_user(username, password):
    """Регистрирует нового пользователя."""
    conn = sqlite3.connect('chat_users.db') # Устанавливаем соединение с базой данных.
    cursor = conn.cursor() # Создаем курсор.
    try:
        password_hash = hash_password(password) # Хешируем пароль.
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash)) # Вставляем нового пользователя в таблицу.
        conn.commit() # Применяем изменения.
        return True # Возвращаем True, если регистрация успешна.
    except sqlite3.IntegrityError: # Обработка ошибки, если пользователь с таким именем уже существует (нарушение UNIQUE-ограничения).
        return False # Возвращаем False, если пользователь уже существует.
    finally:
        conn.close() # В любом случае закрываем соединение.

def authenticate_user(username, password):
    """Проверяет учетные данные пользователя."""
    conn = sqlite3.connect('chat_users.db') # Устанавливаем соединение с базой данных.
    cursor = conn.cursor() # Создаем курсор.
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,)) # Выбираем хеш пароля для данного имени пользователя.
    result = cursor.fetchone() # Получаем результат запроса (первую строку).
    conn.close() # Закрываем соединение.

    if result: # Если пользователь найден.
        stored_password_hash = result[0] # Получаем сохраненный хеш пароля.
        if stored_password_hash == hash_password(password): # Сравниваем хеш введенного пароля с сохраненным.
            return True # Возвращаем True, если пароли совпадают.
    return False # Возвращаем False, если пользователь не найден или пароль неверный.

def save_private_message(sender, receiver, message):
    """Сохраняет личное сообщение в базу данных."""
    conn = sqlite3.connect('chat_users.db') # Устанавливаем соединение с базой данных.
    cursor = conn.cursor() # Создаем курсор.
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) # Получаем текущую метку времени в формате YYYY-MM-DD HH:MM:SS.
    cursor.execute("INSERT INTO private_messages (sender_username, receiver_username, message, timestamp) VALUES (?, ?, ?, ?)",
                   (sender, receiver, message, timestamp)) # Вставляем личное сообщение в таблицу.
    conn.commit() # Применяем изменения.
    conn.close() # Закрываем соединение.

def get_private_messages_history(user1, user2):
    """Возвращает историю личных сообщений между двумя пользователями."""
    conn = sqlite3.connect('chat_users.db') # Устанавливаем соединение с базой данных.
    cursor = conn.cursor() # Создаем курсор.
    # Получаем сообщения, где user1 отправитель и user2 получатель ИЛИ наоборот
    cursor.execute('''
        SELECT sender_username, receiver_username, message, timestamp
        FROM private_messages
        WHERE (sender_username = ? AND receiver_username = ?)
           OR (sender_username = ? AND receiver_username = ?)
        ORDER BY timestamp
    ''', (user1, user2, user2, user1)) # Выбираем все сообщения между двумя пользователями, отсортированные по времени.
    messages = cursor.fetchall() # Получаем все найденные сообщения.
    conn.close() # Закрываем соединение.
    return messages # Возвращаем список сообщений.

def get_all_registered_users():
    """Возвращает список всех зарегистрированных пользователей."""
    conn = sqlite3.connect('chat_users.db') # Устанавливаем соединение с базой данных.
    cursor = conn.cursor() # Создаем курсор.
    cursor.execute("SELECT username FROM users") # Выбираем все имена пользователей.
    users = [row[0] for row in cursor.fetchall()] # Извлекаем имена пользователей из результатов.
    conn.close() # Закрываем соединение.
    return users # Возвращаем список имен пользователей.

# --- Функции для обработки клиентов ---

def broadcast_public_message(message, sender_socket):
    """
    Рассылает сообщение всем подключенным клиентам в общем чате.
    """
    sender_name = client_sockets_map.get(sender_socket) # Получаем имя отправителя по его сокету.
    for user_name, client_sock in list(active_clients.items()): # Итерируем по копии словаря активных клиентов, чтобы избежать ошибок при изменении словаря во время итерации.
        if client_sock != sender_socket: # Не отправляем сообщение обратно отправителю (он сам его отобразит).
            try:
                client_sock.send(message.encode('utf-8')) # Отправляем сообщение клиенту.
            except:
                # Если отправить не удалось, значит клиент отключился
                print(f"Ошибка отправки публичного сообщения {user_name}. Удаляем клиента.") # Выводим сообщение об ошибке.
                remove_client(client_sock) # Удаляем отключившегося клиента.

def remove_client(client_socket):
    """
    Удаляет клиента из списка активных и сообщает остальным о его отключении.
    """
    if client_socket in client_sockets_map: # Если сокет клиента присутствует в словаре.
        username = client_sockets_map[client_socket] # Получаем имя пользователя по сокету.
        del client_sockets_map[client_socket] # Удаляем запись из обратного отображения.
        if username in active_clients: # Если имя пользователя присутствует в словаре активных клиентов.
            del active_clients[username] # Удаляем запись из словаря активных клиентов.
        print(f"Отключился: {username}") # Выводим сообщение об отключении пользователя.
        broadcast_public_message(f"--- {username} покинул чат. ---", None) # Сообщаем всем остальным об отключении.
        client_socket.close() # Закрываем сокет клиента.

def handle_client(client_socket, address):
    """
    Обрабатывает сообщения от конкретного клиента.
    """
    print(f"Подключился: {address}") # Выводим информацию о подключении нового клиента.
    current_username = None # Инициализируем имя пользователя текущего клиента как None.

    try:
        while True: # Бесконечный цикл для получения сообщений от клиента.
            data = client_socket.recv(1024).decode('utf-8') # Получаем данные от клиента (до 1024 байт) и декодируем их.
            if not data: # Если данных нет, значит клиент отключился.
                break # Выходим из цикла.

            parts = data.split(':', 2) # Разделяем полученные данные на части по первому и второму двоеточию (команда, аргументы).
            command = parts[0] # Первая часть - это команда.

            if command == "REGISTER": # Если команда - "REGISTER".
                if len(parts) < 3: # Проверяем, достаточно ли аргументов.
                    client_socket.send("ERROR: Неверный формат регистрации.".encode('utf-8')) # Отправляем сообщение об ошибке.
                    continue # Переходим к следующей итерации цикла.
                _, username, password = parts # Извлекаем имя пользователя и пароль.
                if register_user(username, password): # Пытаемся зарегистрировать пользователя.
                    client_socket.send("REGISTER_SUCCESS".encode('utf-8')) # Отправляем сообщение об успехе.
                    print(f"Зарегистрирован новый пользователь: {username}") # Выводим информацию в консоль.
                else:
                    client_socket.send("REGISTER_FAIL: Пользователь уже существует.".encode('utf-8')) # Отправляем сообщение о неудаче (пользователь уже существует).
            elif command == "LOGIN": # Если команда - "LOGIN".
                if len(parts) < 3: # Проверяем, достаточно ли аргументов.
                    client_socket.send("ERROR: Неверный формат входа.".encode('utf-8')) # Отправляем сообщение об ошибке.
                    continue # Переходим к следующей итерации.
                _, username, password = parts # Извлекаем имя пользователя и пароль.
                if authenticate_user(username, password): # Пытаемся аутентифицировать пользователя.
                    if username in active_clients: # Проверка на уже залогиненного пользователя
                        client_socket.send("LOGIN_FAIL: Этот пользователь уже онлайн.".encode('utf-8')) # Сообщаем, что пользователь уже онлайн.
                        print(f"Попытка повторного входа: {username}") # Выводим информацию в консоль.
                        continue # Переходим к следующей итерации.

                    current_username = username # Устанавливаем текущее имя пользователя для этого сокета.
                    active_clients[current_username] = client_socket # Добавляем клиента в словарь активных клиентов.
                    client_sockets_map[client_socket] = current_username # Добавляем обратную ссылку.
                    client_socket.send(f"LOGIN_SUCCESS:{current_username}".encode('utf-8')) # Отправляем сообщение об успешном входе.
                    print(f"Пользователь {current_username} вошел в систему.") # Выводим информацию в консоль.
                    broadcast_public_message(f"--- {current_username} присоединился к чату. ---", None) # Сообщаем всем о присоединении нового пользователя.
                else:
                    client_socket.send("LOGIN_FAIL: Неверное имя пользователя или пароль.".encode('utf-8')) # Отправляем сообщение о неудаче (неверные данные).
            elif command == "CHAT": # Общий чат
                if current_username: # Если пользователь авторизован.
                    if len(parts) < 2: continue # Проверяем наличие сообщения.
                    _, message = parts # Извлекаем сообщение.
                    print(f"Получено публичное от {current_username}: {message}") # Выводим публичное сообщение в консоль сервера.
                    full_message = f"{current_username}: {message}" # Формируем полное сообщение для рассылки.
                    broadcast_public_message(full_message, client_socket) # Рассылаем сообщение всем подключенным клиентам.
                else:
                    client_socket.send("ERROR: Вы не авторизованы для отправки сообщений.".encode('utf-8')) # Отправляем ошибку, если не авторизован.
            elif command == "PRIVATE_MSG": # Личное сообщение
                if current_username: # Если пользователь авторизован.
                    if len(parts) < 3: # Проверяем, достаточно ли аргументов.
                        client_socket.send("ERROR: Неверный формат личного сообщения.".encode('utf-8')) # Отправляем ошибку.
                        continue # Переходим к следующей итерации.
                    _, receiver_username, message = parts # Извлекаем получателя и сообщение.
                    print(f"Получено личное от {current_username} для {receiver_username}: {message}") # Выводим информацию в консоль сервера.

                    save_private_message(current_username, receiver_username, message) # Сохраняем личное сообщение в базу данных.

                    if receiver_username in active_clients: # Если получатель онлайн.
                        try:
                            # Отправляем сообщение получателю
                            active_clients[receiver_username].send(f"PRIVATE_FROM:{current_username}:{message}".encode('utf-8')) # Отправляем сообщение получателю.
                            # Отправляем подтверждение отправителю (опционально, можно не отправлять, если клиент сам отображает)
                            # client_socket.send(f"PRIVATE_SENT:{receiver_username}:{message}".encode('utf-8'))
                        except Exception as e: # Обработка ошибок отправки.
                            print(f"Ошибка отправки личного сообщения {current_username} -> {receiver_username}: {e}") # Выводим ошибку.
                            client_socket.send(f"ERROR: Не удалось отправить личное сообщение {receiver_username}.".encode('utf-8')) # Отправляем ошибку отправителю.
                    else:
                        continue # Если получатель оффлайн, просто сохраняем сообщение и продолжаем.
                else:
                    client_socket.send("ERROR: Вы не авторизованы для отправки личных сообщений.".encode('utf-8')) # Отправляем ошибку, если не авторизован.
            elif command == "HISTORY_REQUEST": # Запрос истории личных сообщений
                if current_username: # Если пользователь авторизован.
                    if len(parts) < 2: # Проверяем наличие аргумента.
                        client_socket.send("ERROR: Неверный формат запроса истории.".encode('utf-8')) # Отправляем ошибку.
                        continue # Переходим к следующей итерации.
                    _, target_user = parts # Извлекаем имя пользователя, с которым запрашивается история.
                    history = get_private_messages_history(current_username, target_user) # Получаем историю из БД.
                    history_str = "" # Инициализируем строку для истории.
                    for sender, receiver, msg, timestamp in history: # Форматируем каждое сообщение из истории.
                        # Форматируем как "Отправитель (Время): Сообщение"
                        if sender == current_username: # Если отправитель - текущий пользователь.
                            history_str += f"Вы ({timestamp}): {msg}\n" # Форматируем как "Вы: Сообщение".
                        else:
                            history_str += f"{sender} ({timestamp}): {msg}\n" # Форматируем как "ИмяОтправителя: Сообщение".
                    if history_str: # Если история не пуста.
                        client_socket.send(f"HISTORY_RESPONSE:{target_user}:{history_str.strip()}".encode('utf-8')) # Отправляем историю клиенту.
                    else:
                        client_socket.send(f"HISTORY_RESPONSE:{target_user}:Нет сообщений.".encode('utf-8')) # Отправляем сообщение, если истории нет.
                else:
                    client_socket.send("ERROR: Вы не авторизованы для просмотра истории.".encode('utf-8')) # Отправляем ошибку, если не авторизован.
            elif command == "GET_USERS": # Запрос списка всех зарегистрированных пользователей
                if current_username: # Если пользователь авторизован.
                    all_users = get_all_registered_users() # Получаем список всех зарегистрированных пользователей.
                    # Отфильтровываем себя из списка
                    all_users_except_me = [u for u in all_users if u != current_username] # Удаляем текущего пользователя из списка.
                    client_socket.send(f"USER_LIST:{','.join(all_users_except_me)}".encode('utf-8')) # Отправляем список пользователей клиенту.
                else:
                    client_socket.send("ERROR: Вы не авторизованы для получения списка пользователей.".encode('utf-8')) # Отправляем ошибку, если не авторизован.
            else:
                client_socket.send("ERROR: Неизвестная команда.".encode('utf-8')) # Отправляем ошибку для неизвестной команды.

    except ConnectionResetError: # Обработка ошибки, если соединение было принудительно разорвано (например, клиент закрыл окно).
        print(f"Соединение с {address} принудительно разорвано.") # Выводим сообщение.
    except Exception as e: # Общая обработка других исключений.
        print(f"Ошибка при обработке клиента {address}: {e}") # Выводим информацию об ошибке.
    finally:
        remove_client(client_socket) # В любом случае удаляем клиента и закрываем сокет.
        print(f"Соединение с {address} закрыто.") # Выводим сообщение о закрытии соединения.

def start_server():
    """Запускает сервер."""
    init_db() # Инициализируем базу данных.

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Создаем TCP/IP сокет сервера.
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Устанавливаем опцию для повторного использования адреса (полезно при быстрой перезагрузке сервера).
    server_socket.bind((HOST, PORT)) # Привязываем сокет к указанному IP-адресу и порту.
    server_socket.listen(5) # Начинаем слушать входящие соединения (максимум 5 в очереди).
    print(f"Сервер слушает на {HOST}:{PORT}") # Выводим сообщение о запуске сервера.

    while True: # Бесконечный цикл для приема новых подключений.
        client_socket, address = server_socket.accept() # Принимаем новое входящее соединение. Возвращает новый сокет для клиента и его адрес.
        client_handler = threading.Thread(target=handle_client, args=(client_socket, address)) # Создаем новый поток для обработки этого клиента.
        client_handler.start() # Запускаем поток обработки клиента.

if __name__ == "__main__": # Точка входа в программу, если файл запускается напрямую.
    start_server() # Запускаем сервер.
