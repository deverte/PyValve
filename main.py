import pandas as pd
import os
from datetime import datetime
import requests
import re
import time
from threading import Timer

"""
TODO:
1. Выполнить рефакторинг (изменить названия переменных и функций для лучшей
читаемости кода).
2. Разделить файл на модули.
3. Учесть (!).
4. Обработать исключения.
5. Добавить проверку доступа к http-серверу.
6. Сделать графический интерфейс.
7. Добавить подробное описание на GitHub.
"""

def read_plan(plan_name):
    """
    Считывает файл плана и преобразует его в развернутый вид. То есть,
    если есть повторения (repeat), то разворачивает тело данного цикла в
    последовательность команд заданное количество раз.

    Параметры:
    plan_name - имя файла плана. Тип - string.

    Возвращает DataFrame файла плана в развернутом виде.
    Тип - pandas.DataFrame.
    """
    # Получение пути для файла плана (временная проблема с путями)
    # (!) Добавить проверку существования файла
    #plan_path = os.path.join(os.getcwd(), "plan.csv")
    #plan_path = os.path.join(os.getcwd(), "pyvm", plan_name)
    plan_path = os.path.join(os.getcwd(), plan_name)

    # Считывание файла конфигруации и создание его развернутой версии
    initial_plan = pd.read_csv(plan_path, sep=";")
    expanded_plan = pd.DataFrame(columns=initial_plan.columns)

    last_repeat = 0
    for i in range(len(initial_plan)):
        # Обработка повторений (repeat)
        if initial_plan.iloc[i]["Action"] == "repeat":
            number = int(initial_plan.iloc[i]["Type"])
            for j in range(number - 1):
                expanded_plan = expanded_plan.append(initial_plan[last_repeat:i], ignore_index=True)
            last_repeat = i + 1
        # Добавление строк с обыкновенными командами (не repeat)
        else:
            expanded_plan = expanded_plan.append(initial_plan.iloc[i], ignore_index=True)

    return expanded_plan

def read_commands(commands_name):
    """
    Считывает файл с командами.

    Параметры:
    commands_name - имя файла с командами. Тип - string.

    Возвращает DataFrame с командами. Тип - pandas.DataFrame.
    """
    # Получение пути для файла команд (временная проблема с путями)
    # (!) Добавить проверку существования файла
    #plan_path = os.path.join(os.getcwd(), "plan.csv")
    #commands_path = os.path.join(os.getcwd(), "pyvm", commands_name)
    commands_path = os.path.join(os.getcwd(), commands_name)

    # Считывание файла с командами
    # (!) Возможно, нужно будет изменить разделитель (sep) на ";"
    commands = pd.read_csv(commands_path, sep=",", index_col=0,
                          dtype={'Command': str, 'Signal': str, 'Modifier': str})

    return commands

def read_settings(settings_name):
    """
    Считывает файл с настройками.

    Параметры:
    settings_name - имя файла с настройками. Тип - string.

    Возвращает DataFrame с настройками. Тип - pandas.DataFrame.
    """
    # Получение пути для файла настроек (временная проблема с путями)
    # (!) Добавить проверку существования файла
    #settings_path = os.path.join(os.getcwd(), "plan.csv")
    settings_path = os.path.join(os.getcwd(), "pyvm", settings_name)
    #settings_path = os.path.join(os.getcwd(), settings_name)

    # Считывание файла с командами
    # (!) Возможно, нужно будет изменить разделитель (sep) на ";"
    settings = pd.read_csv(settings_path, sep=",", index_col=0,
                          dtype={'Settings': str, 'Values': str})

    return settings

def default_settings():
    """
    Возвращает настройки по умолчанию. Тип - pandas.DataFrame.
    """
    settings = {'Settings': ['SERVER',
                             'ip',
                             'on',
                             'off',
                             'INPUT_FILES',
                             'plan',
                             'commands',
                             'OUTPUT FILES',
                             'protocol',
                             'pressures',
                             'RECORDING',
                             'sample rate',
                             'time precision',
                             'pressure precision'],
                'Values': [float('nan'),
                           'http://192.168.1.54/',
                           '1',
                           '0',
                           float('nan'),
                           'plan.csv',
                           'commands.csv',
                           float('nan'),
                           'protocol.csv',
                           'pressures.csv',
                           float('nan'),
                           '0.25',
                           '3',
                           '3']}
    settings = pd.DataFrame.from_dict(settings)
    return settings

def send(ip, command):
    """
    Посылает команду http серверу.

    Параметры:
    ip - IP-адрес сервера. Тип - str.
    command - команда, посылаемая серверу. Тип - str.
    """
    # (!) Добавить обработку ошибок подключения и т.д.
    response = requests.get("/".join(ip, command))

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
    #response = requests.get(settings.loc["ip"][0])
    #file = response.content
    file = open("/home/deverte/Projects/Sorption/Automation/deverte/192.168.1.54.html", "r")

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

def loop(settings, timer, time_begin, plan, commands, data, stage):
    """
    Цикл программы по считыванию данных с http-сервера.

    Параметры:
    settings - файл с настройками. Тип - pandas.DataFrame.
    timer - таймер текущего этапа. Тип - threading.Timer.
    time_begin - время начала исполнения программы. Тип - float.
    plan - файл плана в развернутом виде. Тип - pandas.DataFrame.
    commands - DataFrame с командами. Тип - pandas.DataFrame.
    data - DataFrame с временем и показаниями датчиков. Тип - pandas.DataFrame.
    stage - текущий этап в последовательности команд. Тип - int.
    """

    # Получение данных давления с заданной частотой
    info = get_info(settings, time_begin)
    print("\t".join(str(value) for value in info.iloc[0]))
    data = data.append(info, ignore_index=True) # Информация с датчиков

    # Если приоритет работы этапа - давление, то выполнение проверки превышения
    # давления. Если проверка пройдена, то перейти к следующему этапу
    if plan.iloc[stage]["Priority"] == "p":
        channel = plan.iloc[stage]["Channel"]
        pressure = float(plan.iloc[stage]["Pressure"])
        if pressure >= data.iloc[-1][channel]:
            sequence(settings, timer, plan, commands, stage)

    # Продолжение работы таймера, если не поступил код завершения
    if stage != -1:
        arguments = [settings, timer, time_begin, plan, commands, data, stage]
        t = Timer(float(settings.loc["sample rate"][0]), loop, args=arguments)
        t.start()

def process(settings, signal, commands):
    """
    Обработка команд.

    Параметры:
    settings - файл с настройками. Тип - pandas.DataFrame.
    signal - текущий этап. Тип - pandas.DataFrame.
    commands - DataFrame с командами. Тип - pandas.DataFrame.
    """
    # ЗАКРЫТИЕ ВСЕХ РЕЛЕ
    send(settings.loc["ip"][0], command("1" * 10, settings.loc["off"][0]))

    # Строка, посылаемая серверу в качестве сигнала
    signal_str = ""
    # Проверка наличия команды из файла плана в файле с командами
    if signal["Action"] in commands.index:
        # ФОРМИРОВАНИЕ СИГНАЛА
        # Получение строки-сигнала в бинарном виде (тип str)
        signal_str = commands.loc[signal["Action"]]["Signal"]

        # Добавление модификаторов (медленный поток, проточная система и т.д.)
        for command in commands:
            # Если команда - модификатор и присутствует в файле плана, то
            # бинарно сложить строку-сигнал и модификатор
            if command["Modifier"] == "Yes":
                if command in signal["Type"]:
                    # Преобразование строки-сигнала в int
                    signal_int = int(signal_str, 2)
                    # Преобразование строки-модификатора в int
                    modifier_int = int(command["Signal"], 2)
                    # Бинарное сложение
                    signal_int = bin(signal_int | modifier_int)[2:]
                    # Добавление нулей в начало (для корректного формирования
                    # сигнала)
                    zeros = "0" * (len(signal_str) - len(signal_int))
                    signal_int = zeros + signal_int

        # ОТПРАВКА СИГНАЛА НА СЕРВЕР
        send(settings.loc["ip"][0], command(signal_str, settings.loc["on"][0]))

def sequence(settings, timer, plan, commands, stage):
    """
    Цикл программы по выполнению последовательности команд.

    Параметры:
    settings - файл с настройками. Тип - pandas.DataFrame.
    timer - таймер текущего этапа. Тип - threading.Timer.
    plan - файл плана в развернутом виде. Тип - pandas.DataFrame.
    commands - DataFrame с командами. Тип - pandas.DataFrame.
    stage - текущий этап в последовательности команд. Тип - int.
    """
    # Завершение предыдущего этапа
    timer.cancel()
    # Если номер текущего этапа меньше, чем количество этапов, то начать этот
    # этап и выполнить обработку команд. Иначе - закрыть все реле и завершить
    # цикл
    if stage < len(plan):
        # Выполнить обработку команд
        process(settings, plan.iloc[stage], commands)
        # Начать этап
        duration = plan.iloc[current_stage]["Duration"]
        arguments = [settings, timer, plan, commands, stage + 1]
        timer = Timer(duration, sequence, args=arguments)
        timer.start()
    else:
        # Завершить цикл
        stage = -1 # код завершения
        timer.close()

def main():
    """
    Главная функция.
    """
    try:
        # Время начала исполнения программы
        time_begin = time.time()
        # Инициализация DataFrame-ов данных, считывание настроек, плана и команд
        data = pd.DataFrame(columns=["Time", "0", "1", "2", "3", "4", "5"])
        # (!) Добавить проверку существования файла настроек. Считать
        # настройки из default_settings и из них создать файл, если файл не
        # существует
        settings = read_settings("settings.csv")
        plan = read_plan(settings.loc["plan"][0])
        commands = read_commands(settings.loc["commands"][0])

        # Инициализация текущего этапа измерений
        stage = 0

        # Инициализация таймера цикла для выполнения последовательности команд
        arguments = [settings, timer, plan, commands, stage]
        timer = Timer(100, sequence, args=arguments)
        # Запуск цикла выполнения последовательности команд
        sequence(settings, timer, plan, commands, stage)
        # Запуск цикла по считыванию данных с http-сервера
        loop(settings, timer, time_begin, plan, commands, data, stage)
    finally:
        # (!) Сохранить данные в папки "Протоколы измерений", "Давления" с
        # именами settings.loc["protocol"][0] и settings.loc["pressures"][0]
        pass

main()
