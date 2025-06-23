# server.py
import socket
import threading
import sqlite3
import hashlib
import time # Для меток времени

HOST = '192.168.9.215'
PORT = 12345

# Словарь для хранения активных клиентских сокетов, где ключ - имя пользователя, значение - сокет.
# Это позволит быстро найти сокет по имени получателя для личных сообщений.
active_clients = {} # {username: client_socket}
client_sockets_map = {} # {client_socket: username} - для обратного поиска

# --- Функции для работы с базой данных SQLite ---

def init_db():
    """Инициализирует базу данных и создает таблицы пользователей и личных сообщений, если их нет."""
    conn = sqlite3.connect('chat_users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS private_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_username TEXT NOT NULL,
            receiver_username TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (sender_username) REFERENCES users(username),
            FOREIGN KEY (receiver_username) REFERENCES users(username)
        )
    ''')
    conn.commit()
    conn.close()
    print("База данных SQLite инициализирована.")

def hash_password(password):
    """Хеширует пароль с использованием SHA256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def register_user(username, password):
    """Регистрирует нового пользователя."""
    conn = sqlite3.connect('chat_users.db')
    cursor = conn.cursor()
    try:
        password_hash = hash_password(password)
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    """Проверяет учетные данные пользователя."""
    conn = sqlite3.connect('chat_users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_password_hash = result[0]
        if stored_password_hash == hash_password(password):
            return True
    return False

def save_private_message(sender, receiver, message):
    """Сохраняет личное сообщение в базу данных."""
    conn = sqlite3.connect('chat_users.db')
    cursor = conn.cursor()
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    cursor.execute("INSERT INTO private_messages (sender_username, receiver_username, message, timestamp) VALUES (?, ?, ?, ?)",
                   (sender, receiver, message, timestamp))
    conn.commit()
    conn.close()

def get_private_messages_history(user1, user2):
    """Возвращает историю личных сообщений между двумя пользователями."""
    conn = sqlite3.connect('chat_users.db')
    cursor = conn.cursor()
    # Получаем сообщения, где user1 отправитель и user2 получатель ИЛИ наоборот
    cursor.execute('''
        SELECT sender_username, receiver_username, message, timestamp
        FROM private_messages
        WHERE (sender_username = ? AND receiver_username = ?)
           OR (sender_username = ? AND receiver_username = ?)
        ORDER BY timestamp
    ''', (user1, user2, user2, user1))
    messages = cursor.fetchall()
    conn.close()
    return messages

def get_all_registered_users():
    """Возвращает список всех зарегистрированных пользователей."""
    conn = sqlite3.connect('chat_users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

# --- Функции для обработки клиентов ---

def broadcast_public_message(message, sender_socket):
    """
    Рассылает сообщение всем подключенным клиентам в общем чате.
    """
    sender_name = client_sockets_map.get(sender_socket)
    for user_name, client_sock in list(active_clients.items()):
        if client_sock != sender_socket: # Не отправляем сообщение обратно отправителю
            try:
                client_sock.send(message.encode('utf-8'))
            except:
                # Если отправить не удалось, значит клиент отключился
                print(f"Ошибка отправки публичного сообщения {user_name}. Удаляем клиента.")
                remove_client(client_sock)

def remove_client(client_socket):
    """
    Удаляет клиента из списка активных и сообщает остальным о его отключении.
    """
    if client_socket in client_sockets_map:
        username = client_sockets_map[client_socket]
        del client_sockets_map[client_socket]
        if username in active_clients:
            del active_clients[username]
        print(f"Отключился: {username}")
        broadcast_public_message(f"--- {username} покинул чат. ---", None) # None, т.к. это системное сообщение
        client_socket.close()

def handle_client(client_socket, address):
    """
    Обрабатывает сообщения от конкретного клиента.
    """
    print(f"Подключился: {address}")
    current_username = None

    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            parts = data.split(':', 2) # Разделяем только по первому и второму двоеточию
            command = parts[0]

            if command == "REGISTER":
                if len(parts) < 3:
                    client_socket.send("ERROR: Неверный формат регистрации.".encode('utf-8'))
                    continue
                _, username, password = parts
                if register_user(username, password):
                    client_socket.send("REGISTER_SUCCESS".encode('utf-8'))
                    print(f"Зарегистрирован новый пользователь: {username}")
                else:
                    client_socket.send("REGISTER_FAIL: Пользователь уже существует.".encode('utf-8'))
            elif command == "LOGIN":
                if len(parts) < 3:
                    client_socket.send("ERROR: Неверный формат входа.".encode('utf-8'))
                    continue
                _, username, password = parts
                if authenticate_user(username, password):
                    if username in active_clients: # Проверка на уже залогиненного пользователя
                        client_socket.send("LOGIN_FAIL: Этот пользователь уже онлайн.".encode('utf-8'))
                        print(f"Попытка повторного входа: {username}")
                        continue

                    current_username = username
                    active_clients[current_username] = client_socket # Добавляем в список активных
                    client_sockets_map[client_socket] = current_username # Обратная ссылка
                    client_socket.send(f"LOGIN_SUCCESS:{current_username}".encode('utf-8'))
                    print(f"Пользователь {current_username} вошел в систему.")
                    broadcast_public_message(f"--- {current_username} присоединился к чату. ---", None)
                else:
                    client_socket.send("LOGIN_FAIL: Неверное имя пользователя или пароль.".encode('utf-8'))
            elif command == "CHAT": # Общий чат
                if current_username:
                    if len(parts) < 2: continue
                    _, message = parts
                    print(f"Получено публичное от {current_username}: {message}")
                    full_message = f"{current_username}: {message}"
                    broadcast_public_message(full_message, client_socket)
                else:
                    client_socket.send("ERROR: Вы не авторизованы для отправки сообщений.".encode('utf-8'))
            elif command == "PRIVATE_MSG": # Личное сообщение
                if current_username:
                    if len(parts) < 3:
                        client_socket.send("ERROR: Неверный формат личного сообщения.".encode('utf-8'))
                        continue
                    _, receiver_username, message = parts
                    print(f"Получено личное от {current_username} для {receiver_username}: {message}")

                    save_private_message(current_username, receiver_username, message) # Сохраняем в БД

                    if receiver_username in active_clients:
                        try:
                            # Отправляем сообщение получателю
                            active_clients[receiver_username].send(f"PRIVATE_FROM:{current_username}:{message}".encode('utf-8'))
                            # Отправляем подтверждение отправителю (опционально, можно не отправлять, если клиент сам отображает)
                            # client_socket.send(f"PRIVATE_SENT:{receiver_username}:{message}".encode('utf-8'))
                        except Exception as e:
                            print(f"Ошибка отправки личного сообщения {current_username} -> {receiver_username}: {e}")
                            client_socket.send(f"ERROR: Не удалось отправить личное сообщение {receiver_username}.".encode('utf-8'))
                    else:
                        continue
                else:
                    client_socket.send("ERROR: Вы не авторизованы для отправки личных сообщений.".encode('utf-8'))
            elif command == "HISTORY_REQUEST": # Запрос истории личных сообщений
                if current_username:
                    if len(parts) < 2:
                        client_socket.send("ERROR: Неверный формат запроса истории.".encode('utf-8'))
                        continue
                    _, target_user = parts
                    history = get_private_messages_history(current_username, target_user)
                    history_str = ""
                    for sender, receiver, msg, timestamp in history:
                        # Форматируем как "Отправитель (Время): Сообщение"
                        if sender == current_username:
                            history_str += f"Вы ({timestamp}): {msg}\n"
                        else:
                            history_str += f"{sender} ({timestamp}): {msg}\n"
                    if history_str:
                        client_socket.send(f"HISTORY_RESPONSE:{target_user}:{history_str.strip()}".encode('utf-8'))
                    else:
                        client_socket.send(f"HISTORY_RESPONSE:{target_user}:Нет сообщений.".encode('utf-8'))
                else:
                    client_socket.send("ERROR: Вы не авторизованы для просмотра истории.".encode('utf-8'))
            elif command == "GET_USERS": # Запрос списка всех зарегистрированных пользователей
                if current_username:
                    all_users = get_all_registered_users()
                    # Отфильтровываем себя из списка
                    all_users_except_me = [u for u in all_users if u != current_username]
                    client_socket.send(f"USER_LIST:{','.join(all_users_except_me)}".encode('utf-8'))
                else:
                    client_socket.send("ERROR: Вы не авторизованы для получения списка пользователей.".encode('utf-8'))
            else:
                client_socket.send("ERROR: Неизвестная команда.".encode('utf-8'))

    except ConnectionResetError:
        print(f"Соединение с {address} принудительно разорвано.")
    except Exception as e:
        print(f"Ошибка при обработке клиента {address}: {e}")
    finally:
        remove_client(client_socket)
        print(f"Соединение с {address} закрыто.")

def start_server():
    """Запускает сервер."""
    init_db()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Сервер слушает на {HOST}:{PORT}")

    while True:
        client_socket, address = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, address))
        client_handler.start()

if __name__ == "__main__":
    start_server()