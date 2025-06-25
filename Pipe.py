import os
import json
import time
import pandas as pd
import gc

data_path = "data.bin"
response_path = "responce.bin"


class PipeServer():
    def __init__(self, update_status, *args):
        self.update_status = update_status

    def process(self, stop_event, data):
        while not stop_event.is_set():
            if os.path.exists(data_path):
                with open(data_path, "rb") as pipe:
                    msg = pipe.read()
                    end_time = time.time()
                    self.file_size = len(msg)
                    new_data = json.loads(bytes(msg).decode("utf-8"))
                    data['file_name'] = new_data['file_name']
                    data['start_time'] = new_data['start_time']
                    data['body'] = pd.read_json(new_data['body'])
                    del new_data
                    duration = end_time - data['start_time']
                    speed = self.file_size/1024/duration
                    response = f"\nПередача данных прошла успешно.\nНазвание файла: {data['file_name']}\nСпособ передачи: Pipe\nОбъём данных: {self.file_size/1024} килобайт.\nВремя передачи: {duration} секунд.\nСкорость передачи: {speed} килобайт в секунду\n"
                    self.update_status(response)
                os.remove(data_path)
                with open(response_path, "wb") as pipe:
                    pipe.write(bytes(response, "utf-8"))

                # Очистка
                self.file_size = None
                del msg
                del end_time
                del duration
                del speed
                del response
                gc.collect()


class PipeClient():
    def __init__(self, update_status, *args):
        self.update_status = update_status

    def send(self, data):
        with open(data_path, "wb") as pipe:
            pipe.write(data)
        time.sleep(3)
        while True:
            try:
                if os.path.exists(response_path):
                    with open(response_path, "rb") as pipe:
                        msg = pipe.read()
                        if msg != data:
                            self.update_status(msg.decode('utf-8'))
                            break
            except PermissionError as e:
                print(e)
                continue
        os.remove(response_path)

    def close(self):
        pass
