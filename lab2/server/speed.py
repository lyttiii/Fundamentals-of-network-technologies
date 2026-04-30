import time
import os
import threading

mutex = threading.Lock()


class FileData:
    def __init__(self, fileName, totalSize):
        self.fileName = fileName
        self.totalSize = totalSize
        now = time.perf_counter()
        self.startTimePoint = now
        self.prelastTimePoint = now
        self.lastTimeStamp = now
        self.receivedSize = os.path.getsize("uploads/" + self.fileName)
        self.isFinished = False

    def show(self):
        if not self.isFinished:
            now = time.perf_counter()
            newReceivedSize = os.path.getsize("uploads/" + self.fileName)

            avgSpeed = (newReceivedSize / (now - self.startTimePoint))
            momentSpeed = ((newReceivedSize - self.receivedSize) / (now - self.lastTimeStamp))

            print(f"|  file name: {self.fileName}  "
                  f"|  avg speed: {avgSpeed: .2f} bytes/s  "
                  f"|  moment speed: {momentSpeed: .2f} bytes/s  "
                  f"|  received: {newReceivedSize} bytes "
                  f"|  total size: {self.totalSize} bytes |")

            if (newReceivedSize == self.totalSize):
                self.isFinished = True
            else:
                self.receivedSize = newReceivedSize
                self.lastTimeStamp = now


class SpeedMeter:
    def __init__(self):
        self.filesToReceiveDict = dict()

    def addFile(self, fileName, totalSize):
        mutex.acquire()
        try:
            self.filesToReceiveDict[fileName] = FileData(fileName, totalSize)
        finally:
            mutex.release()

    def showingThread(self):
        while True:
            mutex.acquire()
            try:
                for key in self.filesToReceiveDict:
                    fileData = self.filesToReceiveDict[key]
                    fileData.show()
            finally:
                mutex.release()

            time.sleep(3)

