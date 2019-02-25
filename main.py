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
2. Выполнить рефакторинг (изменить названия переменных и функций для лучшей
читаемости кода).
3. Учесть (!).
4. Обработать исключения.
5. Добавить проверку доступа к http-серверу.
6. Сделать графический интерфейс.
"""

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
    info = client.get_info(settings, time_begin)
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
        client.process(settings, plan.iloc[stage], commands)
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
        settings = files.read_settings("settings.csv")
        plan = files.read_plan(settings.loc["plan"][0])
        commands = files.read_commands(settings.loc["commands"][0])

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
