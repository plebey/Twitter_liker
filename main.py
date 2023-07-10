from pathlib import Path
from threading import Thread
import threading
import requests
import time
from selenium import webdriver
from selenium.common import TimeoutException, InvalidArgumentException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import sys
import json
import os
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from termcolor import cprint
import colorama
from colorama import Fore
import ads_ids_from_groups as ads_info
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import logging


DIRECTORY = 'C:\.ADSPOWER_GLOBAL\cache'
#chrome_path = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
ADS_IDS_TXT = "ADS_ids.txt"
#START_URL = "https://lumpics.ru/where-are-the-extensions-in-google-chrome/#i-2"
INTENT_LINKS = "intent_links.txt"
COLORS = {
    logging.DEBUG: Fore.WHITE,
    logging.INFO: Fore.CYAN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.MAGENTA
}
FORMATTER = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')


def line_control(file_txt):
    # Удаление пустых строк
    with open(file_txt) as f1:
        lines = f1.readlines()
        non_empty_lines = (line for line in lines if not line.isspace())
        with open(file_txt, "w") as n_f1:
            n_f1.writelines(non_empty_lines)


def ads_ids_from_group(settings):
    with open("settings.json", "r") as file:
        settings = json.load(file)
    ads_ids = ads_info.ads_id_from_api(settings["group_id"])

    if not os.path.exists(ADS_IDS_TXT):
        with open(ADS_IDS_TXT, 'w') as file:
            for ads_id in ads_ids:
                file.write(ads_id + '\n')
        print('ID профилей сохранены в файл: ', ADS_IDS_TXT)
        print('При необходимости, измените их порядок в указанном файле.')


def groups_choose():
    # Обрабатываем запрос на группы
    group_info = ads_info.ads_groups_from_api()
    gr_names = ''
    gr_num = 1
    for key, value in group_info.items():
        gr_names += str(gr_num) + f". {value}\n"
        gr_num += 1
    gr_list = list(group_info.items())
    gr_id = int(input("Выберите номер группы из списка: \n" + gr_names)) - 1
    sel_gr = gr_list[gr_id][0]
    return sel_gr


def set_def_settings():
    # Задание первичных настроек
    if not os.path.exists("settings.json"):
        th_count = input("Введите максимальное количество потоков? (Пример ответа: 3) - ")
        gr_id = groups_choose()
        data = {
            "threads": th_count,
            "group_id": gr_id,
            "http_link": "https://www.google.com/webhp?hl=ru"
        }
        json_data = json.dumps(data, indent=4)
        with open("settings.json", "w") as file:
            file.write(json_data)


def check_links_existing():
    if not os.path.exists(INTENT_LINKS):
        with open(INTENT_LINKS, "w") as file:
            file.write('')
        cprint(f"Файл {INTENT_LINKS} создан. Заполните его и повторите попытку.", "green")
        sys.exit()
    elif os.stat(INTENT_LINKS).st_size == 0:
        cprint(f"Файл {INTENT_LINKS} пуст. Заполните его и повторите попытку", "red")
        sys.exit(0)


def selenium_task(window_id, open_url, http_link, logger):

    resp = requests.get(open_url).json()
    if resp["code"] != 0:
        print(resp["msg"])
        cprint("please check ads_id", "red")
        sys.exit()
    chrome_driver = resp["data"]["webdriver"]
    service = Service(chrome_driver)

    chrome_options = Options()
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-site-isolation-trials")
    chrome_options.add_argument("--disable-popup-blocking")
    #chrome_options.add_argument("--headless=new")
    # chrome_options.add_experimental_option("excludeSwitches", ["disable-popup-blocking"])
    chrome_options.add_experimental_option("debuggerAddress", resp["data"]["ws"]["selenium"])
    # print(service.command_line_args())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    window_handles = driver.window_handles
    driver.switch_to.window(window_handles[-1])

    driver.get(http_link)

    with open(INTENT_LINKS) as file:
        links = [link.strip() for link in file]

    wait = WebDriverWait(driver, 10)

    for link in links:
        try:
            driver.get(link)
            element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div[2]/div[1]')))
            # Нужно для полной прогрузки страницы
            time.sleep(3)
            element.click()

            logger.info(f'<Успех> - acc: {window_id + 1} - link: {link}')
        except:
            logger.error(f'<Ошибка INVALID_LINK> - acc: {window_id + 1} - link: {link}')


    # driver.execute_script('window.open("chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html");')
    # # window_handles = driver.window_handles
    # driver.switch_to.window(driver.window_handles[-1])
    # driver.refresh()
    # # Ввод пароля от MM
    # wait = WebDriverWait(driver, 10)
    # input_element = wait.until(EC.presence_of_element_located((By.ID, "password")))
    # # input_element = driver.find_element(By.ID, "password")
    # if len(passwrds) == 1:
    #     input_element.send_keys(passwrds[0])
    # else:
    #     input_element.send_keys(passwrds[window_id])
    # input_element.send_keys(Keys.ENTER)
    # wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    #driver.close()
    driver.quit()


def settings_management(settings):
    print("Выберите номер изменяемого свойства (0 для выхода из настроек): ")

    for key_id, item in enumerate(settings.items(), start=1):
        # print(settings.items())
        print(str(key_id)+'. '+str(item[0])+': ' + str(item[1]))

    set_id = input()
    set_id = int(set_id)
    chosed_seting = ''
    if set_id == 0:
        main()
    elif set_id == 1:
        chosed_seting = 'threads'
    elif set_id == 2:
        chosed_seting = 'group_id'

    settings[chosed_seting] = input(f"Введите новое значение для {chosed_seting}: ")
    json_data = json.dumps(settings, indent=4)
    with open("settings.json", "w") as file:
        file.write(json_data)
    main()


def colorize_log(record):
    level_color = COLORS.get(record.levelno, Fore.RESET)
    asctime = FORMATTER.formatTime(record, "%Y-%m-%d %H:%M:%S")
    message = f"{level_color}{asctime} - {record.getMessage()}{Fore.RESET}"
    return message


def set_logger():
    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.INFO)
    # Создание обработчика для записи в файл
    file_handler = logging.FileHandler('errors.log')
    file_handler.setLevel(logging.ERROR)
    # Создание обработчика для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    # Создание форматтера для логов
    FORMATTER.format = colorize_log
    # Привязка форматтера к обработчикам
    file_handler.setFormatter(FORMATTER)
    console_handler.setFormatter(FORMATTER)
    # Привязка обработчиков к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def main():
    colorama.init()
    # ads_id_from_cache()
    set_def_settings()
    check_links_existing()

    # Настройка логов
    logger = set_logger()

    # Загрузка параметров
    with open("settings.json", "r") as file:
        settings = json.load(file)

    # Загрузка профилей ads
    ads_ids_from_group(settings)

    line_control(ADS_IDS_TXT)
    line_control(INTENT_LINKS)

    # Загрузка id_ads
    with open(ADS_IDS_TXT, "r") as file:
        # Чтение содержимого файла и запись в список
        ids = file.readlines()
        # Удаление символа новой строки "\n" из каждой строки
        ids = [line.strip() for line in ids]

    cprint("!!!Для перехода в настройки введите 0.", "yellow")
    cprint("Убедитесь, что в intent_links.txt находятся ссылки типа intent, иначе сначала запустите to_intent.py", "red")
    prof_open = input("Номера открываемых профилей (ex: '1, 4-7,10'): ")

    # Переход в настройки
    if len(prof_open) == 1:
        if int(prof_open) == 0:
            settings_management(settings)
            sys.exit(0)

    # Обработка введенных номеров профилей
    prof_open = prof_open.replace(" ", "")
    prof_list = prof_open.split(',')
    open_ids = []
    for elem in prof_list:
        if '-' in elem:
            temp = elem.split('-')
            for pr_id in list(range(int(temp[0]), int(temp[1]))):
                open_ids.append(pr_id)
            open_ids.append((int(temp[1])))
        else:
            open_ids.append(int(elem))
    open_ids = [x - 1 for x in open_ids]

    http_link = settings["http_link"]
    threads_count = settings["threads"]


    # Работа с профилями
    print("Открываются профили: ")
    prof_nums = list(open_ids)
    for i in range(len(prof_nums)):
        prof_nums[i] += 1
    cprint(str(prof_nums), "green")
    del prof_nums

    args1 = ["--disable-popup-blocking", "--disable-web-security"]
    args1 = str(args1).replace("'", '"')


    threads = []
    for window_id in open_ids:
        while True:
            # Получение списка всех активных потоков
            thread_list = threading.enumerate()
            # Получение количества активных потоков
            num_threads = len(thread_list)
            # Вывод количества активных потоков
            #print("Количество запущенных потоков:", num_threads-1)
            if num_threads < int(threads_count)+1:
                ads_id = ids[window_id]
                open_url = "http://localhost:50325/api/v1/browser/start?user_id=" + ads_id + "&open_tabs=1" + f"&launch_args={str(args1)}" + "&headless=1"
                thread = Thread(target=selenium_task, args=(window_id, open_url, http_link, logger))
                time.sleep(1.1)
                logger.info(f'Начато выполнение на профиле: {window_id+1}')
                thread.start()
                threads.append(thread)
                break
            time.sleep(1)

    # Ожидаем завершения всех потоков
    for thread in threads:
        thread.join()
    colorama.deinit()


if __name__ == '__main__':
    main()





