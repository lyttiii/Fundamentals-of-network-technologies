import psutil
import socket
import sys
from sys import argv
import signal
import os
from pathlib import Path
import threading

from speed import *


def getIpAddress(interface):
    addrs = psutil.net_if_addrs()[interface]
    for addr in addrs:
        if addr.family == socket.AF_INET:
            return addr.address


def signal_handler(sig, _):
    print("Сервер отключен")
    sys.exit(0)


class Server:
    def __init__(self, interfaceName, portStr):
        print("Инициализация сервера..")
        try:
            print("Начинаем получение IP-адреса")
            ipAddress = getIpAddress(interfaceName)
            print(f"Обнаруженный IP-адрес: {ipAddress}")
        except KeyError:
            print(f"Интерфейс {interfaceName} не найден.")
            raise ValueError()

        try:
            port = int(portStr)
        except ValueError:
            print("Неправильно введен порт.")
            raise ValueError()

        if not (0 < port < 65536):
            print("Неправильно введен порт.")
            raise ValueError()

        self.ipAddress = ipAddress
        self.port = port
        print(f"Сервер инициализирован с IP: {self.ipAddress} и портом: {self.port}")

    def receiveFileThread(self, clientSocket, clientAddress):

        fileNameSize = int.from_bytes(clientSocket.recv(2), byteorder='big')

        if fileNameSize > 4096:
            print("Имя файла слишком большое, максимальный размер 4096 байт.")
            clientSocket.close()
            return

        fileName = clientSocket.recv(fileNameSize).decode()

        fileSize = int.from_bytes(clientSocket.recv(8), byteorder='big')


        if fileSize > 1099511627776:
            print("Размер файла слишком большой, максимальный размер 1 терабайт.")
            clientSocket.close()
            return

        remaining_bytes = fileSize
        fdir = Path('uploads')
        fdir.mkdir(parents=True, exist_ok=True)

        with open("uploads/" + fileName, "wb") as file:
            speedMeter.addFile(fileName, fileSize)
            while remaining_bytes > 0:
                chunk_size = min(1024, remaining_bytes)
                data = clientSocket.recv(chunk_size)
                remaining_bytes -= len(data)
                file.write(data)

        uploadedFileSize = os.path.getsize("uploads/" + fileName)
        if uploadedFileSize == fileSize:
            try:
                clientSocket.send((1).to_bytes(1, byteorder='big'))
            finally:
                clientSocket.close()
        else:
            try:
                clientSocket.send((0).to_bytes(1, byteorder='big'))
            finally:
                clientSocket.close()

    def listening(self):
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        serverHost = self.ipAddress
        serverPort = self.port
        serverSocket.bind((serverHost, serverPort))
        print("Сокет успешно привязан.")

        serverSocket.listen(5)
        print(f"Сервер слушает. IP: {self.ipAddress}; порт: {self.port}")

        while True:
            clientSocket, clientAddress = serverSocket.accept()
            print(f"Подключено клиентом {clientAddress}")

            newThread = threading.Thread(target=self.receiveFileThread, args=(clientSocket, clientAddress,),
                                         daemon=True)
            newThread.start()

        serverSocket.close()


def run():
    print("Запуск сервера..")
    try:
        script, port = argv
    except:
        print("Неправильно переданы аргументы!")
        print("usage: sudo python server.py <port>")
        sys.exit(0)

    interface_name = "Беспроводная сеть"
    print(f"Используемый интерфейс: {interface_name}")
    try:
        server = Server(interface_name, port)
    except ValueError:
        print("Не удалось создать необходимые для работы программы экземпляры.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    global speedMeter
    speedMeter = SpeedMeter()
    newThread = threading.Thread(target=speedMeter.showingThread, daemon=True)
    newThread.start()

    server.listening()


if __name__ == "__main__":
    run()
    printf("Сервер запускается")
