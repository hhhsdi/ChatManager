import socket
import threading

class ChatServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}  # {client_socket: (address, nickname)}
        self.lock = threading.Lock()

    def start(self):
        """Запуск сервера"""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Сервер запущен на {self.host}:{self.port}")

        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"Подключился клиент: {client_address}")

                # Запрашиваем никнейм
                client_socket.send("Введите ваш никнейм: ".encode('utf-8'))
                nickname = client_socket.recv(1024).decode('utf-8').strip()

                with self.lock:
                    self.clients[client_socket] = (client_address, nickname)

                # Оповещаем всех о новом пользователе
                self.broadcast(f"{nickname} присоединился к чату!", exclude=client_socket)

                # Запускаем поток для обработки сообщений
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,),
                    daemon=True
                )
                thread.start()

        except KeyboardInterrupt:
            print("Сервер остановлен.")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket):
        """Обработка сообщений от клиента"""
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break  # Клиент отключился

                nickname = self.clients[client_socket][1]
                self.broadcast(f"{nickname}: {message}")

            except (ConnectionResetError, BrokenPipeError):
                break

        # Удаляем клиента при отключении
        with self.lock:
            nickname = self.clients[client_socket][1]
            del self.clients[client_socket]
            self.broadcast(f"{nickname} покинул чат.")

    def broadcast(self, message, exclude=None):
        """Отправка сообщения всем клиентам, кроме исключённого"""
        with self.lock:
            for client in self.clients:
                if client != exclude:
                    try:
                        client.send(message.encode('utf-8'))
                    except (ConnectionResetError, BrokenPipeError):
                        continue

if __name__ == "__main__":
    server = ChatServer()
    server.start()