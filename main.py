import os
import sys
import time
import pandas as pd
from threading import Timer
from datetime import datetime

if not os.path.exists(os.path.join(os.getcwd(), "lib")):
    print("Can't find library.")
    sys.exit()
else:
    sys.path.append(os.path.join(os.getcwd(), "lib"))
import files
import client

"""
TODO:
1. Добавить подробное описание на GitHub.
2. Добавить проверку доступа к http-серверу.
3. Сделать графический интерфейс.
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
        # Считывание настроек, плана и команд
        self.settings = files.read_settings()
        # Получение доступных путей для выходных файлов давлений и протокола
        pressures_name = self.settings.loc["pressures"][0]
        self.settings.loc["pressures"][0] = files.get_available_path(pressures_name)
        protocol_name = self.settings.loc["protocol"][0]
        self.settings.loc["protocol"][0] = files.get_available_path(protocol_name)

        # Считывание плана и команд
        self.plan = files.read_plan(self.settings.loc["plan"][0])
        self.commands = files.read_commands(self.settings.loc["commands"][0])

        # Инициализация DataFrame-ов данных и протокола
        data = pd.DataFrame(columns=["Time", "0", "1", "2", "3", "4", "5"])
        data = data.set_index("Time")
        protocol_cols = ["Action", "Type", "Begin", "Priority", "Pressure", "Channel"]
        protocol = pd.DataFrame(columns=protocol_cols)
        protocol = protocol.set_index("Action")

        # Запись заголовков файлов давлений и протокола
        data.to_csv(self.settings.loc["pressures"][0])
        protocol.to_csv(self.settings.loc["protocol"][0])

        # Инициализация текущего этапа измерений
        self.stage = 0 # Первый этап
        self.is_first_stage = True # Первый этап
        self.is_end = False # Не конец

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
        time_begin = self.time_begin

        settings = self.settings
        plan = self.plan
        commands = self.commands

        # Если этап не первый, то перейти к следующему этапу
        if not self.is_first_stage:
            self.stage += 1

        # Если номер текущего этапа меньше, чем количество этапов, то начать этот
        # этап и выполнить обработку команд. Иначе - закрыть все реле и завершить
        # цикл
        if self.stage < len(plan):
            # Выполнить обработку команд
            client.process(settings, plan.iloc[self.stage], commands)

            # Добавить запись в протокол
            protocol_cols = ["Action", "Type",
                             "Begin", "Priority",
                             "Pressure", "Channel"]
            record = pd.DataFrame(columns=protocol_cols)
            record = record.set_index("Action")
            # Действие
            action = plan.iloc[self.stage]["Action"]
            # Тип
            type = plan.iloc[self.stage]["Type"]
            # Время
            time_precision = int(settings.loc["time precision"][0])
            time_format = "{0:." + str(time_precision) + "f}"
            begin = time_format.format(time.time()  - time_begin)
            # Приоритет
            priority = str(plan.iloc[self.stage]["Priority"])
            if priority == "p":
                priority = "Pressure"
            elif priority == "t" or priority == str(float('nan')):
                priority = "Time"
            # Давление
            pressure = str(plan.iloc[self.stage]["Pressure"])
            if pressure == str(float('nan')):
                pressure = "-"
            # Канал
            channel = str(plan.iloc[self.stage]["Channel"])
            if channel == str(float('nan')):
                channel = "-"
            # Формирование записи
            record.loc[action] = [type, begin, priority, pressure, channel]
            # Добавить запись в файл протокола
            record.to_csv(self.settings.loc["protocol"][0], header=False, mode="a")

            # Запустить таймер
            duration = plan.iloc[self.stage]["Duration"]
            # Преобразование длительности из формата "%H:%M:%S" в float
            duration = datetime.strptime(duration, "%H:%M:%S")
            duration = duration.hour * 60**2 + duration.minute * 60 + duration.second

            self.is_first_stage = False

            self.timer = Timer(duration, self.sequence)
            self.timer.start()
        else:
            # Завершить цикл
            self.is_end = True

    def loop(self):
        """
        Цикл программы по считыванию данных с http-сервера.
        """
        time_begin = self.time_begin

        settings = self.settings
        plan = self.plan
        commands = self.commands

        stage = self.stage

        timer = self.timer

        # Если не поступил код завершения
        if not self.is_end:
            # Продолжение работы таймера
            t = Timer(float(settings.loc["sample rate"][0]), self.loop)
            t.start()

            # Получение данных давления
            info = client.get_info(settings, time_begin)
            # <CONSOLE>
            pressures_str = "\t".join(str(value) for value in info.iloc[0])
            info_str = "\t".join([info.index[0], pressures_str])
            print(info_str)
            #self.data = self.data.append(info, ignore_index=True)
            # Добавить запись в файл данных
            info.to_csv(self.settings.loc["pressures"][0], header=False, mode="a")

            # Если приоритет работы этапа - давление, то выполнение проверки превышения
            # давления. Если проверка пройдена, то перейти к следующему этапу
            if str(plan.iloc[stage]["Priority"]) == "p":
                channel = plan.iloc[stage]["Channel"]
                pressure = float(plan.iloc[stage]["Pressure"])
                # Корректное сравнение float c заданной точностью pp
                pp = settings.iloc[stage]["pressure precision"]
                if abs(pressure - self.data.iloc[-1][channel]) >= 10**(-pp):
                    timer.close()
                    self.sequence()

def main():
    """
    Главная функция.
    """
    super = Supervisor()
    super.start()

if __name__ == '__main__':
    main()
