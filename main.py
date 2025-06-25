# -*- coding: utf-8 -*-
import os
import json
import time
import socket
import threading
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from pandastable import Table, config  # type: ignore

import Socket
import Pipe
import MemoryMappedFile

HOST = socket.gethostbyname(socket.gethostname())
PORT = 12345


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Анализатор передачи данных")
        self.root.geometry("400x300")
        self.root.configure(bg='black', )

        tk.Label(self.root, text="Выберите режим", font=(
            "Lucida Console", 14), fg="green", bg="black").pack(pady=20)

        tk.Button(self.root,
                  text="Клиент",
                  command=self.open_client_window,
                  width=20,
                  fg="green",
                  bg="black",
                  activebackground="green",
                  overrelief="groove",
                  font=("Lucida Console", 12)).pack(pady=10)
        tk.Button(self.root,
                  text="Сервер",
                  command=self.open_server_window,
                  width=20,
                  fg="green",
                  bg="black",
                  activebackground="green",
                  font=("Lucida Console", 12)).pack(pady=10)
        tk.Button(self.root,
                  text="Выход",
                  command=self.root.destroy,
                  width=20,
                  fg="green",
                  bg="black",
                  activebackground="green",
                  font=("Lucida Console", 12)).pack(pady=10)

        root.mainloop()

    def open_client_window(self):
        print("Client")
        self.root.withdraw()
        ClientWindow(self.root)

    def open_server_window(self):
        print("Server")
        self.root.withdraw()
        ServerWindow(self.root)


class ServerWindow:
    def __init__(self, main_root: tk.Tk):
        self.main_root = main_root
        self.root = tk.Toplevel(main_root)
        self.root.title("Анализатор передачи данных: Сервер")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.configure(bg='black', )

        self.transmission_methods = {
            "Socket": Socket.SocketServer,
            "Pipe": Pipe.PipeServer,
            "Memory Mapped File": MemoryMappedFile.MMFServer
        }
        self.selected_method = tk.StringVar(value="Socket")
        self.stop_event = threading.Event()
        self.server_thread = None
        self.data = {
            "file_name": None,
            "body": None,
            "start_time": None
        }

        tk.Label(self.root, text="IP адрес", fg="green", bg="black").place(
            relheight=0.05, relwidth=0.3, relx=0.05, rely=0.03)
        self.host = tk.Entry(self.root,
                             textvariable=tk.StringVar(value=str(HOST)),
                             width=30,
                             state="readonly",
                             fg="green",
                             bg="black",
                             readonlybackground="black")
        self.host.place(relheight=0.05, relwidth=0.3, relx=0.05, rely=0.10)
        tk.Label(self.root, text="Порт:", fg="green", bg="black").place(
            relheight=0.05, relwidth=0.3, relx=0.05, rely=0.17)
        self.port = tk.Entry(self.root, textvariable=tk.StringVar(
            value=str(PORT)), width=10,  fg="green", bg="black")
        self.port.place(relheight=0.05, relwidth=0.3, relx=0.05, rely=0.24)

        tk.Label(self.root,
                 text="Вид межпроцессного взаимодействия:",
                 fg="green",
                 bg="black").place(relheight=0.05,
                                   relwidth=0.3,
                                   relx=0.05,
                                   rely=0.31)
        option_menu = tk.OptionMenu(
            self.root, self.selected_method, *self.transmission_methods.keys())
        option_menu.config(fg="green", bg="black", activebackground="green")
        option_menu.place(relheight=0.05, relwidth=0.3, relx=0.05, rely=0.38)

        tk.Button(self.root,
                  text="Запустить Сервер",
                  command=self.server_thread_start,
                  fg="green", bg="black",
                  activebackground="green",
                  overrelief="groove").place(relheight=0.05,
                                             relwidth=0.3,
                                             relx=0.05,
                                             rely=0.45)
        tk.Button(self.root,
                  text="Остановить Сервер",
                  command=self.stop_server,
                  fg="green", bg="black",
                  activebackground="green",
                  overrelief="groove").place(relheight=0.05,
                                             relwidth=0.3,
                                             relx=0.05,
                                             rely=0.52)
        tk.Button(self.root,
                  text="Отобразить полученные данные",
                  command=self.open_data_window,
                  fg="green",
                  bg="black",
                  activebackground="green",
                  overrelief="groove").place(relheight=0.05,
                                             relwidth=0.5,
                                             relx=0.425,
                                             rely=0.92)
        tk.Button(self.root, text="Назад",
                  command=self.on_close,
                  fg="green",
                  bg="black",
                  activebackground="green",
                  overrelief="groove").place(relheight=0.05,
                                             relwidth=0.3,
                                             relx=0.05,
                                             rely=0.92)

        tk.Label(self.root, text="Вывод:", fg="green", bg="black").place(
            relheight=0.05, relwidth=0.55, relx=0.4, rely=0.03)
        self.status_text = tk.Text(self.root, fg="green", bg="black")
        self.status_text.place(
            relheight=0.8, relwidth=0.55, relx=0.4, rely=0.08)

    def open_data_window(self):
        self.root.withdraw()
        DataWindow(self.root, self.data)

    def update_status(self, message: str):
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)

    def server_thread_start(self):
        if self.server_thread:
            messagebox.showerror("Error", "Сервер уже запущен")
            return

        if not self.port.get().isnumeric():
            messagebox.showerror("Error", "Не корректный порт")
            return

        self.server_thread = threading.Thread(
            target=self.start_server, daemon=True)
        self.server_thread.start()

    def start_server(self):
        server = self.transmission_methods[self.selected_method.get()](
            self.update_status, self.host.get(), int(self.port.get()))
        if server:
            self.update_status(f"Сервер {self.selected_method.get()} запущен")
        server.process(self.stop_event, self.data)
        del server

    def stop_server(self):
        if self.server_thread:
            self.stop_event.set()
            self.server_thread.join()
            self.stop_event.clear()
            self.server_thread = None
            self.update_status("Сервер остановлен")

    def on_close(self):
        self.stop_server()
        self.root.destroy()
        self.main_root.deiconify()


class DataWindow():
    def __init__(self, main_root: tk.Tk, data):
        self.main_root = main_root
        self.root = tk.Toplevel(main_root)
        self.root.title("Анализатор передачи данных: Полученные данные")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.configure(bg='black', )

        self.data = data
        self.table = pt = Table(self.root,
                                dataframe=data['body'],
                                showtoolbar=True,
                                showstatusbar=True,
                                fg="green",
                                bg="black",
                                activebg="green",
                                overrelief="groove",)
        pt.show()
        options = {'colheadercolor': 'green', 'floatprecision': 5}
        config.apply_options(options, pt)
        pt.show()

        # tk.Label(self.root, text="Информация по передаче:").pack(pady=5)
        # self.status_text = tk.Text(self.root, height=12, width=60)
        # self.status_text.pack()

    # def update_status(self, message: str):
    #     self.status_text.insert(tk.END, f"{message}\n")
    #     self.status_text.see(tk.END)

    def on_close(self):
        self.root.destroy()
        self.main_root.deiconify()


class ClientWindow:
    def __init__(self, main_root: tk.Tk):
        self.main_root = main_root
        self.root = tk.Toplevel(main_root)
        self.root.title("Анализатор передачи данных: Клиент")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.configure(bg='black', )

        self.transmission_methods = {
            "Socket": Socket.SocketClient,
            "Pipe": Pipe.PipeClient,
            "Memory Mapped File": MemoryMappedFile.MMFClient
        }
        self.selected_method = tk.StringVar(value="Socket")
        self.selected_file = tk.StringVar()
        self.client = None
        self.send_thread = None

        tk.Label(self.root, text="IP адрес", fg="green", bg="black").place(
            relheight=0.05, relwidth=0.3, relx=0.05, rely=0.03)
        self.host = tk.Entry(self.root, textvariable=tk.StringVar(
            value=str(HOST)), width=30, fg="green", bg="black")
        self.host.place(relheight=0.05, relwidth=0.3, relx=0.05, rely=0.10)
        tk.Label(self.root, text="Порт:", fg="green", bg="black").place(
            relheight=0.05, relwidth=0.3, relx=0.05, rely=0.17)
        self.port = tk.Entry(self.root, textvariable=tk.StringVar(
            value=str(PORT)), width=10,  fg="green", bg="black")
        self.port.place(relheight=0.05, relwidth=0.3, relx=0.05, rely=0.24)

        tk.Label(self.root,
                 text="Вид межпроцессного взаимодействия:",
                 fg="green",
                 bg="black").place(relheight=0.05,
                                   relwidth=0.3,
                                   relx=0.05,
                                   rely=0.31)
        option_menu = tk.OptionMenu(
            self.root, self.selected_method, *self.transmission_methods.keys())
        option_menu.config(fg="green", bg="black", activebackground="green")
        option_menu.place(relheight=0.05, relwidth=0.3, relx=0.05, rely=0.38)

        tk.Label(self.root,
                 text="Выбранный файл:",
                 fg="green",
                 bg="black").place(relheight=0.05,
                                   relwidth=0.3,
                                   relx=0.05,
                                   rely=0.45)
        tk.Entry(self.root,
                 textvariable=self.selected_file,
                 width=50,
                 state='readonly',
                 fg="green",
                 bg="black",
                 readonlybackground="black").place(relheight=0.05,
                                                   relwidth=0.3,
                                                   relx=0.05,
                                                   rely=0.52)
        self.browse_button = tk.Button(self.root,
                                       text="Выбрать файл:",
                                       command=self.browse_file,
                                       fg="green",
                                       bg="black",
                                       activebackground="green",
                                       overrelief="groove")
        self.browse_button.place(
            relheight=0.05, relwidth=0.3, relx=0.05, rely=0.59)

        tk.Button(self.root,
                  text="Запустить клиент",
                  command=self.start_client,
                  fg="green",
                  bg="black",
                  activebackground="green",
                  overrelief="groove").place(relheight=0.05,
                                             relwidth=0.3,
                                             relx=0.05,
                                             rely=0.66)
        tk.Button(self.root, text="Отправить",
                  command=self.start_send_thread,
                  fg="green",
                  bg="black",
                  activebackground="green",
                  overrelief="groove").place(relheight=0.05,
                                             relwidth=0.3,
                                             relx=0.05,
                                             rely=0.73)
        tk.Button(self.root, text="Отключиться",
                  command=self.stop_client,
                  fg="green",
                  bg="black",
                  activebackground="green",
                  overrelief="groove").place(relheight=0.05,
                                             relwidth=0.3,
                                             relx=0.05,
                                             rely=0.80)
        tk.Button(self.root, text="Назад",
                  command=self.on_close,
                  fg="green",
                  bg="black",
                  activebackground="green",
                  overrelief="groove").place(relheight=0.05,
                                             relwidth=0.3,
                                             relx=0.05,
                                             rely=0.92)

        tk.Label(self.root, text="Вывод:", fg="green", bg="black").place(
            relheight=0.05, relwidth=0.55, relx=0.4, rely=0.03)
        self.status_text = tk.Text(self.root, fg="green", bg="black")
        self.status_text.place(
            relheight=0.8, relwidth=0.55, relx=0.4, rely=0.08)

    def update_status(self, message: str):
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)

    def browse_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.selected_file.set(file_path)

    def start_client(self):
        if not self.client:
            try:
                self.client = self.transmission_methods[
                    self.selected_method.get()
                ](
                    self.update_status, self.host.get(), int(self.port.get()))
                self.update_status(
                    f"Клиент {self.selected_method.get()} запущен")
            except socket.timeout as e:
                self.update_status(e)
                self.client = None
            except OSError as e:
                self.update_status(e)
                self.client = None

    def start_send_thread(self):
        if self.send_thread:
            messagebox.showerror("Error", "Предыдущая отправка не завершилась")
            return
        if not self.client:
            messagebox.showerror("Error", "Клиент не запущен")
            return

        file_path = self.selected_file.get()

        if not file_path:
            messagebox.showerror("Error", "Пожалуйста, выберите файл")
            return

        if not os.path.exists(file_path):
            messagebox.showerror("Error", "Файл не найден")
            return

        self.send_thread = threading.Thread(target=self.send, daemon=True)
        self.send_thread.start()

    def send(self):
        file_path = self.selected_file.get()
        self.update_status(f"Отправка файла {os.path.basename(file_path)}")
        self.client.send(preprocessing(file_path))
        self.send_thread = None

    def stop_client(self):
        if self.client:
            self.client.close()
            self.client = None
            self.send_thread = None
            self.update_status("Подключение завершено")

    def on_close(self):
        self.stop_client()
        self.root.destroy()
        self.main_root.deiconify()


def preprocessing(file_path):
    df = pd.read_csv(file_path, delimiter=';', low_memory=False)
    df = df.drop_duplicates(keep="first")
    df = df.dropna()
    data = {
        "file_name": os.path.basename(file_path),
        "body": df.to_json(),
        "start_time": time.time()
    }
    data = json.dumps(data)
    data = bytes(data, encoding="utf-8")
    return data


def main():
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
