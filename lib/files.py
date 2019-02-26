import os
import pandas as pd

"""
Основные функции для работы с входными файлами и создания выходных файлов:
настройки по умолчанию, чтение файла настроек, чтение плана, чтение команд.
"""

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
    #settings_path = os.path.join(os.getcwd(), "pyvm", settings_name)
    settings_path = os.path.join(os.getcwd(), settings_name)

    # Считывание файла с командами
    # (!) Возможно, нужно будет изменить разделитель (sep) на ";"
    settings = pd.read_csv(settings_path, sep=",", index_col=0,
                          dtype={'Settings': str, 'Values': str})

    return settings

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
    # (!) Возможно, нужно будет изменить разделитель (sep) на ";"
    initial_plan = pd.read_csv(plan_path, sep=",")
    expanded_plan = pd.DataFrame(columns=initial_plan.columns)

    last_repeat = 0
    for i in range(len(initial_plan)):
        # Обработка повторений (repeat)
        if initial_plan.iloc[i]["Action"] == "repeat":
            number = int(initial_plan.iloc[i]["Type"])
            for j in range(number - 1):
                expanded_plan = expanded_plan.append(initial_plan[last_repeat:i],
                                                     ignore_index=True)
            last_repeat = i + 1
        # Добавление строк с обыкновенными командами (не repeat)
        else:
            expanded_plan = expanded_plan.append(initial_plan.iloc[i],
                                                 ignore_index=True)

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
