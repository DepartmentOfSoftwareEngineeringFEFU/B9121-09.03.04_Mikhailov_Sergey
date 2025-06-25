import json
import time
import pandas as pd
import socket
import gc


class SocketServer():
    def __init__(self, update_status, host, port):
        self.update_status = update_status
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()
        self.conn = None
        self.file_size = None

    def process(self, stop_event, data):
        try:
            while not stop_event.is_set():
                try:
                    if not self.conn:
                        self.server.settimeout(1.0)
                        self.conn, addr = self.server.accept()
                        self.update_status(f"Подключился клиент {addr[0]}:{addr[1]}")
                        self.conn.sendall(bytes("Подключение к серверу успешно", "utf-8"))
                    else:
                        if not self.file_size:
                            self.conn.settimeout(1.0)
                            self.file_size = int.from_bytes(self.conn.recv(16), byteorder='big')
                            if self.file_size == 0:
                                self.file_size = None
                                self.conn = None
                                self.update_status("Клиент отключился")
                            else:
                                new_data = b''
                                self.update_status(f"Ожидается файл размером {self.file_size} байт")
                        else:
                            chunk = None
                            while len(new_data) < self.file_size:
                                chunk = self.conn.recv(1048576)
                                if not chunk:
                                    break
                                new_data += chunk
                            else:
                                end_time = time.time()
                                new_data = json.loads(bytes(new_data).decode("utf-8"))
                                data['file_name'] = new_data['file_name']
                                data['start_time'] = new_data['start_time']
                                data['body'] = pd.read_json(new_data['body'])
                                del new_data
                                duration = end_time - data['start_time']
                                speed = self.file_size/1024/duration
                                response = f"\nПередача данных прошла успешно.\nНазвание файла: {data['file_name']}\nСпособ передачи: Socket\nОбъём данных: {self.file_size/1024} килобайт.\nВремя передачи: {duration} секунд.\nСкорость передачи: {speed} килобайт в секунду\n"
                                self.conn.sendall(bytes(response, "utf-8"))
                                self.update_status(response)

                                # Очистка
                                self.file_size = None
                                del end_time
                                del duration
                                del speed
                                del response
                                del chunk
                                gc.collect()
                except socket.timeout:
                    continue
                except OSError as e:
                    if stop_event.is_set():
                        self.update_status("Сервер остановлен по запросу")
                    else:
                        self.update_status(f"Ошибка сервера: {e}")
                    break
        finally:
            self.server.close()
            self.server = None


class SocketClient():
    def __init__(self, update_status, host, port):
        self.update_status = update_status
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.update_status(self.socket.recv(8192).decode('utf-8'))

    def send(self, data):
        try:
            self.socket.send(len(data).to_bytes(8, byteorder='big'))
            self.socket.sendall(data)
            self.update_status(self.socket.recv(8192).decode("utf-8"))
        except ConnectionAbortedError as e:
            print(e)
            self.update_status("Сервер отключен. Выключите клиент, перезапустите сервер и подключите клиент снова.")

    def close(self):
        self.socket.close()
        self.socket = None
