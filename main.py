import os
import re
import sys
import time
import requests
import pandas as pd
from threading import Timer
from datetime import datetime

#sys.path.append(os.path.join(os.getcwd(), "lib"))
sys.path.append(os.path.join(os.getcwd(), "pyvm", "lib"))
import files
import client

"""
TODO:
1. Добавить подробное описание на GitHub.
2. Учесть (!).
3. Обработать исключения.
4. Добавить проверку доступа к http-серверу.
5. Сделать графический интерфейс.
"""

class Supervisor:
    """
    Основной класс для программы. Следит за исполнением основных циклов.
    """
    def __init__(self):
        """
        Конструктор класса Supervisor. Инициализация атрибутов.
        """
        # Время начала исполнения программы
        self.time_begin = time.time()
        # Инициализация DataFrame-ов данных и протокола
        self.data = pd.DataFrame(columns=["Time", "0", "1", "2", "3", "4", "5"])
        self.protocol = pd.DataFrame(columns=["Action", "Type", "Begin", "End"])
        # Считывание настроек, плана и команд
        # (!) Добавить проверку существования файла настроек. Считать
        # настройки из default_settings и из них создать файл, если файл не
        # существует
        self.settings = files.read_settings("settings.csv")
        self.plan = files.read_plan(settings.loc["plan"][0])
        self.commands = files.read_commands(settings.loc["commands"][0])

        # Инициализация текущего этапа измерений
        self.stage = 0

        # Инициализация таймера цикла для выполнения последовательности команд
        self.timer = float("nan")

    def start(self):
        """
        Начало исполнения циклов.
        """
        # Время начала исполнения программы
        self.time_begin = time.time()
        # Запуск цикла выполнения последовательности команд
        self.sequence()
        # Запуск цикла по считыванию данных с http-сервера
        self.loop()

    def sequence(self):
        """
        Цикл программы по выполнению последовательности команд.
        """
        settings = self.settings
        plan = self.plan
        commands = self.commands
        # Если номер текущего этапа меньше, чем количество этапов, то начать этот
        # этап и выполнить обработку команд. Иначе - закрыть все реле и завершить
        # цикл
        if self.stage < len(plan):
            # Выполнить обработку команд
            client.process(settings, plan.iloc[self.stage], commands)
            # Начать этап
            duration = plan.iloc[self.stage]["Duration"]
            # Преобразование длительности из формата "%H:%M:%S" в float
            duration = datetime.strptime(duration, "%H:%M:%S")
            duration = duration.hour * 60**2 + duration.minute * 60 + duration.second
            self.stage += 1
            self.timer = Timer(duration, self.sequence)
            self.timer.start()
        else:
            # Завершить цикл
            self.stage = -1 # код завершения

    def loop(self):
        """
        Цикл программы по считыванию данных с http-сервера.
        """
        time_begin = self.time_begin

        settings = self.settings
        plan = self.plan
        commands = self.commands

        stage = self.stage

        timer = selt.timer

        # Получение данных давления с заданной частотой
        info = client.get_info(settings, time_begin)
        print("\t".join(str(value) for value in info.iloc[0]))
        self.data = self.data.append(info, ignore_index=True) # Информация с датчиков

        # Если приоритет работы этапа - давление, то выполнение проверки превышения
        # давления. Если проверка пройдена, то перейти к следующему этапу
        if plan.iloc[stage]["Priority"] == "p":
            channel = plan.iloc[stage]["Channel"]
            pressure = float(plan.iloc[stage]["Pressure"])
            # Корректное сравнение float c заданной точностью pp
            pp = settings.iloc[stage]["pressure precision"]
            if abs(pressure - self.data.iloc[-1][channel]) >= 10**(-pp):
                timer.close()
                self.sequence()

        # Продолжение работы таймера, если не поступил код завершения
        if stage != -1:
            t = Timer(float(settings.loc["sample rate"][0]), self.loop)
            t.start()

def main():
    """
    Главная функция.
    """
    try:
        super = Supervisor()
        super.start()
    finally:
        # (!) Сохранить данные в папки "Протоколы измерений", "Давления" с
        # именами settings.loc["protocol"][0] и settings.loc["pressures"][0]
        pass

if __name__ == '__main__':
    main()
