import re
import time
import requests
import pandas as pd

"""
Основные функции клиента: получение информации с сервера, обработка команд из
плана, преобразование команд в понятные для сервера, отправка команд на сервер.
"""

def get_info(settings, time_begin):
    """
    Считывает показания датчиков с http сервера (html страницы).

    Параметры:
    settings - файл с настройками. Тип - pandas.DataFrame.
    time_begin - время начала исполнения программы. Тип - float.

    Возвращает время и показания датчиков - тип pandas.DataFrame.
    """
    # Получение страницы с данными
    response = requests.get(settings.loc["ip"][0])
    file = response.content
    #file = open("/home/deverte/Projects/Sorption/Automation/deverte/192.168.1.54.html", "r")

    # Парсинг страницы, получение давлений
    template = r"(?<=Pressure\dCalibrated:\s)([+-]?\d+[.]\d+)"
    pressures = re.findall(template, file.read())

    # Создание pandas.DataFrame
    df = pd.DataFrame(columns=["Time", "0", "1", "2", "3", "4", "5"])

    # Создание списка из времени и давлений
    time_precision = int(settings.loc["time precision"][0])
    time_format = "{0:." + str(time_precision) + "f}"
    info = [time_format.format(time.time()  - time_begin)]
    pressure_precision = int(settings.loc["pressure precision"][0])
    pressure_format = "{0:." + str(pressure_precision) + "f}"
    info.extend([pressure_format.format(float(i)) for i in pressures])

    df.loc[0] = info
    return df

def process(settings, signal, commands):
    """
    Обработка команд.

    Параметры:
    settings - файл с настройками. Тип - pandas.DataFrame.
    signal - текущий этап. Тип - pandas.DataFrame.
    commands - DataFrame с командами. Тип - pandas.DataFrame.
    """
    on = settings.loc["on"][0]
    off = settings.loc["off"][0]
    # ЗАКРЫТИЕ ВСЕХ РЕЛЕ
    print("/".join([settings.loc["ip"][0], command("1" * 10, off)]))
    #send(settings.loc["ip"][0], command("1" * 10, off))

    # Строка, посылаемая серверу в качестве сигнала
    signal_str = ""
    # Проверка наличия команды из файла плана в файле с командами
    if signal["Action"] in commands.index:
        # ФОРМИРОВАНИЕ СИГНАЛА
        # Получение строки-сигнала в бинарном виде (тип str)
        signal_str = commands.loc[signal["Action"]]["Signal"]

        # Добавление модификаторов (медленный поток, проточная система и т.д.)
        for cmd in commands["Modifier"]:
            # Если команда - модификатор и присутствует в файле плана, то
            # бинарно сложить строку-сигнал и модификатор
            if cmd == "Yes":
                if cmd in str(signal["Type"]):
                    # Преобразование строки-сигнала в int
                    signal_int = int(signal_str, 2)
                    # Преобразование строки-модификатора в int
                    modifier_int = int(cmd["Signal"], 2)
                    # Бинарное сложение
                    signal_int = bin(signal_int | modifier_int)[2:]
                    # Добавление нулей в начало (для корректного формирования
                    # сигнала)
                    zeros = "0" * (len(signal_str) - len(signal_int))
                    signal_int = zeros + signal_int

        # ОТПРАВКА СИГНАЛА НА СЕРВЕР
        #send(settings.loc["ip"][0], command(signal_str, on))
        print("/".join([settings.loc["ip"][0], command(signal_str, on)]))

def command(signal, state):
    """
    Преобразует команду из плана в команду, понятную серверу.

    Параметры:
    signal - строка-сигнал в бинарном виде. Тип - str.
    state - состояние для команды (вкл/выкл [on/off]). Значения "1" и "0".
    Тип - str.

    Возвращает команду, понятную серверу - тип: String.
    """
    return "_".join([signal, state, "SETRELAY"])

def send(ip, cmd):
    """
    Посылает команду http серверу.

    Параметры:
    ip - IP-адрес сервера. Тип - str.
    cmd - команда, посылаемая серверу. Тип - str.
    """
    # (!) Добавить обработку ошибок подключения и т.д.
    response = requests.get("/".join([ip, cmd]))
