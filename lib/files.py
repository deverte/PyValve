import os
import sys
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
                           'protocols/protocol.csv',
                           'pressures/pressures.csv',
                           float('nan'),
                           '0.25',
                           '3',
                           '3']}
    settings = pd.DataFrame.from_dict(settings)
    settings = settings.set_index("Settings")
    return settings

def read_settings(settings_name="settings.csv"):
    """
    Считывает файл с настройками.

    Параметры:
    settings_name - имя файла с настройками. Тип - str.

    Возвращает DataFrame с настройками. Тип - pandas.DataFrame.
    """
    # Проверка существования файла настроек. Если файл не существует, то
    # считываются настройки из default_settings и из них создается файл.
    # Получение пути для файла настроек
    settings_path = os.path.join(os.getcwd(), settings_name)
    if not os.path.exists(settings_path):
        settings = default_settings()
        settings.to_csv("settings.csv")
    else:
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
    plan_name - имя файла плана. Тип - str.

    Возвращает DataFrame файла плана в развернутом виде.
    Тип - pandas.DataFrame.
    """
    # Получение пути для файла плана
    plan_path = os.path.join(os.getcwd(), plan_name)
    if not os.path.exists(plan_path):
        print("Plan file \"" + plan_name + "\" does not exist!")
        sys.exit()

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
    commands_path = os.path.join(os.getcwd(), commands_name)
    if not os.path.exists(commands_path):
        print("Commands file \"" + commands_name + "\" does not exist!")
        sys.exit()

    # Считывание файла с командами
    # (!) Возможно, нужно будет изменить разделитель (sep) на ";"
    commands = pd.read_csv(commands_path, sep=",", index_col=0,
                          dtype={'Command': str, 'Signal': str, 'Modifier': str})

    return commands

def get_available_path(name):
    """
    Получает доступный путь для файла с заданным именем. Если файл существует,
    добавляет "_i" перед расширением файла, где i - номер первого не
    повторяющегося имени файла с таким же форматом имени. Например, если
    существуют файлы "data.csv", "data_1.csv", то функция вернет путь для файла
    с именем "data_2.csv".

    Параметры:
    name - соответствующее имя файла. Тип - str.

    Возвращает доступный путь для файла с заданным именем. Тип - str.
    """
    # Создание форматов для путей файлов
    pure_format = "{}{}"
    format = "{}_{}{}"
    # Учет расширения файла (если есть)
    dot_index = name.rfind(".")
    extension = ""
    if dot_index != -1:
        extension = name[dot_index:]
        name = name[:dot_index]
    # Инициализация "чистого" пути (по файлу настроек)
    path = os.path.join(os.getcwd(), pure_format.format(name, extension))
    # Создание дополнительных директорий (если нужно)
    os.makedirs(os.path.join(os.getcwd(), os.path.split(path)[0]), exist_ok=True)
    # Если файл существует, то проверить, существует ли файл "file_i.ext",
    # (file - имя директории + имя файла без расширения, i - итератор по
    # одинаковым именам файлов, ext - расширение файла).
    # [Первая проверка осуществляется без учета i]
    i = 1
    while True:
        if os.path.exists(path):
            path = os.path.join(os.getcwd(), format.format(name, str(i), extension))
            i += 1
        else:
            break
    return path
