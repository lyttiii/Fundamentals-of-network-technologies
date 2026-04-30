import socket
import sys
import ipaddress
import os
import signal


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def signal_handler(sig, _):
    clear_screen()
    print("Выход..")
    sys.exit(0)


class Client:
    def __init__(self, file_path, ip_addr, port):
        try:
            ipaddress.ip_address(ip_addr)
        except ValueError:
            raise ValueError("Неправильно введён IP-адрес.")

        if not (0 < int(port) < 65536):
            raise ValueError("Неправильно введён порт.")

        if not os.path.exists(file_path):
            raise ValueError("Файл не существует.")

        self.file_path = file_path
        self.ip_address = ip_addr
        self.port = int(port)

    def send_file(self, client_socket):
        file_name = os.path.basename(self.file_path)
        file_name_size = len(file_name.encode('utf-8'))
        file_size = os.path.getsize(self.file_path)

        print(f"Отправка файла '{file_name}' размером {file_size} байт.")

        # Отправка информации о файле
        client_socket.send(file_name_size.to_bytes(4, byteorder='big'))
        client_socket.send(file_name.encode('utf-8'))
        client_socket.send(file_size.to_bytes(8, byteorder='big'))

        # Отправка файла по частям
        with open(self.file_path, 'rb') as file:
            while True:
                data = file.read(65536)  # 64 KB буфер
                if not data:
                    break
                client_socket.sendall(data)

        # Получение результата передачи
        sending_result = client_socket.recv(1)
        if sending_result == b'\x01':
            print("Файл успешно принят сервером.")
        else:
            print("Ошибка: Файл повреждён при передаче.")

    def connect_and_send(self):
        clear_screen()
        print(f"Соединение с сервером {self.ip_address}:{self.port}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.connect((self.ip_address, self.port))
                print("Соединение успешно установлено.")
                self.send_file(client_socket)
            except ConnectionRefusedError:
                print("Ошибка: сервер недоступен.")
            except Exception as e:
                print(f"Ошибка передачи файла: {e}")


def run():
    try:
        _, file_path, ip_addr, port = sys.argv
        client = Client(file_path, ip_addr, port)
    except ValueError as e:
        print(e)
        print("Usage: python client.py <file_path> <server_ip> <server_port>")
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    client.connect_and_send()


if __name__ == "__main__":
    run()
