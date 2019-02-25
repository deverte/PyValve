import re
import requests
import pandas as pd

def send(ip, cmd):
    """
    Посылает команду http серверу.

    Параметры:
    ip - IP-адрес сервера. Тип - str.
    cmd - команда, посылаемая серверу. Тип - str.
    """
    # (!) Добавить обработку ошибок подключения и т.д.
    response = requests.get("/".join(ip, cmd))

def command(signal, state):
    """
    Преобразует команду из плана в команду, понятную серверу.

    Параметры:
    signal - строка-сигнал в бинарном виде. Тип - str.
    state - состояние для команды (вкл/выкл [on/off]). Значения "1" и "0".
    Тип - str.

    Возвращает команду, понятную серверу - тип: String.
    """
    return "_".join("/", signal, state, "SETRELAY")

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
