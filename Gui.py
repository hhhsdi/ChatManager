import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading

class ChatClientGUI:
    def __init__(self, master):
        self.master = master
        master.title("Чат-клиент")
        
        # Настройка сокета (подключение к серверу)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect(('localhost', 12345))  # Подключение к серверу
        except ConnectionRefusedError:
            messagebox.showerror("Ошибка", "Сервер недоступен!")
            master.destroy()
            return

        # GUI элементы
        self.chat_area = scrolledtext.ScrolledText(master, state='disabled', wrap=tk.WORD)
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.msg_frame = tk.Frame(master)
        self.msg_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.msg_entry = tk.Entry(self.msg_frame, width=50)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.msg_entry.bind("<Return>", self.send_message)  # Отправка по Enter
        self.msg_entry.focus_set()  # Фокус на поле ввода при запуске

        self.send_button = tk.Button(self.msg_frame, text="Отправить", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=5)

        # Поток для приёма сообщений
        self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receive_thread.start()

    def send_message(self, event=None):
        """Отправка сообщения на сервер"""
        message = self.msg_entry.get()
        if message:
            try:
                self.client_socket.send(message.encode('utf-8'))
                self.msg_entry.delete(0, tk.END)
            except ConnectionResetError:
                messagebox.showerror("Ошибка", "Соединение с сервером потеряно!")
                self.master.destroy()

    def receive_messages(self):
        """Приём сообщений от сервера"""
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break  # Сервер отключился
                
                self.chat_area.config(state='normal')
                self.chat_area.insert(tk.END, message + "\n")
                self.chat_area.config(state='disabled')
                self.chat_area.yview(tk.END)  # Автопрокрутка вниз
                
            except (ConnectionResetError, OSError):
                if not self.master.winfo_exists():  # Если окно уже закрыто
                    break
                messagebox.showerror("Ошибка", "Соединение с сервером потеряно!")
                self.master.after(0, self.master.destroy)
                break

    def on_closing(self):
        """Закрытие соединения при выходе"""
        try:
            self.client_socket.close()
        except:
            pass
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    client_gui = ChatClientGUI(root)
    root.protocol("WM_DELETE_WINDOW", client_gui.on_closing)
    root.mainloop()