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
2. Поместить КОНСТАНТЫ в файл конфигурации.
3. Разделить файл на модули.
4. Учесть (!).
5. Обработать исключения.
6. Добавить проверку доступа к http-серверу.
7. Сделать графический интерфейс.
8. Добавить репозиторий на GitHub с подробным описанием.
"""

PLAN_NAME = "plan.csv"
COMMANDS_NAME = "commands.csv"

PROTOCOL_NAME = "protocol.csv"
PRESSURES_NAME = "pressures.csv"

TIME_BEGIN = time.time()

IP = "http://192.168.1.54"

ON = "1"
OFF = "0"

SAMPLE_RATE = 0.25

TIME_PRECISION = 3
PRESSURE_PRECISION = 3

def read_plan(plan_name):
    """
    Считывает файл конфигурации и преобразует его в развернутый вид. То есть,
    если есть повторения (repeat), то разворачивает тело данного цикла в
    последовательность команд заданное количество раз.

    Параметры:
    plan_name - имя файла конфигурации. Тип - string.

    Возвращает DataFrame файла конфигурации в развернутом виде.
    Тип - pandas.DataFrame.
    """
    # Получение пути для файла конфигурации (временная проблема с путями)
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

def read_commands(COMMANDS_NAME):
    """
    Считывает файл с командами.

    Параметры:
    COMMANDS_NAME - имя файла с командами. Тип - string.

    Возвращает DataFrame с командами. Тип - pandas.DataFrame.
    """
    # Получение пути для файла конфигурации (временная проблема с путями)
    # (!) Добавить проверку существования файла
    #plan_path = os.path.join(os.getcwd(), "plan.csv")
    #comands_path = os.path.join(os.getcwd(), "pyvm", COMMANDS_NAME)
    comands_path = os.path.join(os.getcwd(), COMMANDS_NAME)

    # Считывание файла с командами
    # (!) Возможно, нужно будет изменить разделитель (sep) на ";"
    commands = pd.read_csv(commands_path, sep=",", index_col=0,
                          dtype={'Command': str, 'Signal': str, 'Modifier': str})

    return commands

def send(command):
    """
    Посылает команду http серверу.

    Параметры:
    command - команда, посылаемая серверу. Тип - str.
    """
    # (!) Добавить обработку ошибок подключения и т.д.
    response = requests.get("/".join(IP, command))

def command(signal, state=ON):
    """
    Преобразует команду из конфига в команду, понятную серверу.

    Параметры:
    signal - строка-сигнал в бинарном виде. Тип - str.

    Возвращает команду, понятную серверу - тип: String.
    """
    return "_".join("/", signal, state, "SETRELAY")

def get_info():
    """
    Считывает показания датчиков с http сервера (html страницы).

    Возвращает время и показания датчиков - тип pandas.DataFrame.
    """
    # Получение страницы с данными
    #response = requests.get(IP)
    #file = response.content
    file = open("/home/deverte/Projects/Sorption/Automation/deverte/192.168.1.54.html", "r")

    # Парсинг страницы, получение давлений
    template = r"(?<=Pressure\dCalibrated:\s)([+-]?\d+[.]\d+)"
    pressures = re.findall(template, file.read())

    # Создание pandas.DataFrame
    df = pd.DataFrame(columns=["Time", "0", "1", "2", "3", "4", "5"])

    # Создание списка из времени и давлений
    time_format = "{0:." + str(TIME_PRECISION) + "f}"
    info = [time_format.format(time.time()  - TIME_BEGIN)]
    pressure_format = "{0:." + str(PRESSURE_PRECISION) + "f}"
    info.extend([pressure_format.format(float(i)) for i in pressures])

    df.loc[0] = info
    return df

def loop(timer, plan, commands, data, stage):
    """
    Цикл программы по считыванию данных с http-сервера.

    Параметры:
    timer - таймер текущего этапа. Тип - threading.Timer.
    plan - файл конфигурации в развернутом виде. Тип - pandas.DataFrame.
    commands - DataFrame с командами. Тип - pandas.DataFrame.
    data - DataFrame с временем и показаниями датчиков. Тип - pandas.DataFrame.
    stage - текущий этап в последовательности команд. Тип - int.
    """

    # Получение данных давления с заданной частотой
    info = get_info()
    print("\t".join(str(value) for value in info.iloc[0]))
    data = data.append(info, ignore_index=True) # Информация с датчиков

    # Если приоритет работы этапа - давление, то выполнение проверки превышения
    # давления. Если проверка пройдена, то перейти к следующему этапу
    if plan.iloc[stage]["Priority"] == "p":
        channel = plan.iloc[stage]["Channel"]
        pressure = float(plan.iloc[stage]["Pressure"])
        if pressure >= data.iloc[-1][channel]:
            sequence(timer, plan, commands, stage)

    # Продолжение работы таймера, если не поступил код завершения
    if stage != -1:
        t = Timer(SAMPLE_RATE, loop, args=[timer, plan, commands, data, stage])
        t.start()

def process(signal, commands):
    """
    Обработка команд.

    Параметры:
    signal - текущий этап. Тип - pandas.DataFrame.
    commands - DataFrame с командами. Тип - pandas.DataFrame.
    """
    # ЗАКРЫТИЕ ВСЕХ РЕЛЕ
    send(command("1" * 10, OFF))

    # Строка, посылаемая серверу в качестве сигнала
    signal_str = ""
    # Проверка наличия команды из файла конфигурации в файле с командами
    if signal["Action"] in commands.index:
        # ФОРМИРОВАНИЕ СИГНАЛА
        # Получение строки-сигнала в бинарном виде (тип str)
        signal_str = commands.loc[signal["Action"]]["Signal"]

        # Добавление модификаторов (медленный поток, проточная система и т.д.)
        for command in commands:
            # Если команда - модификатор и в файле конфигурации, то бинарно
            # сложить строку-сигнал и модификатор
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
        send(command(signal_str, ON))

def sequence(timer, plan, commands, stage):
    """
    Цикл программы по выполнению последовательности команд.

    Параметры:
    timer - таймер текущего этапа. Тип - threading.Timer.
    plan - файл конфигурации в развернутом виде. Тип - pandas.DataFrame.
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
        process(plan.iloc[stage], commands)
        # Начать этап
        duration = plan.iloc[current_stage]["Duration"]
        arguments = [timer, plan, commands, stage + 1]
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
        # Инициализация DataFrame-ов данных, считывание конфигурации и команд
        data = pd.DataFrame(columns=["Time", "0", "1", "2", "3", "4", "5"])
        plan = read_plan(PLAN_NAME)
        commands = read_commands(COMMANDS_NAME)

        # Инициализация текущего этапа измерений
        stage = 0

        # Инициализация таймера цикла для выполнения последовательности команд
        timer = Timer(100, sequence, args=[plan, commands, stage])
        # Запуск цикла выполнения последовательности команд
        sequence(timer, plan, commands, stage)
        # Запуск цикла по считыванию данных с http-сервера
        loop(timer, plan, commands, data, stage)
    finally:
        # (!) Сохранить данные в папки "Протоколы измерений", "Давления" с
        # именами "PROTOCOL_NAME" и "PRESSURES_NAME"
        pass

main()
