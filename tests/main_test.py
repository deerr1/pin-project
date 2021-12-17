import os, sys
import subprocess
import unittest
from sqlalchemy import create_engine, text
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
ROOT_DIR = str((BASE_DIR / '..').absolute())


class MainTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        os.chdir(ROOT_DIR)
        cls._proc = subprocess.Popen(["docker-compose", "up"], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        while True:
            s = cls._proc.stdout.readline().decode('cp1251')
            print(s)
            if s.find('ready to accept connections') > -1:
                break
        cls.db_connect = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5432/pin')

        time.sleep(10)
    
    def test_incorrect_input(self):

        options = webdriver.ChromeOptions()
        chrome_driver = ChromeDriverManager().install()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=options, executable_path=chrome_driver)
        
        driver.get("http://localhost:8082/")
        self.assertEqual(driver.title, 'pin', 'Открыто не то окно')

        # Переход на страницу авторизации
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(1) > div > div:nth-child(3) > button')
        elem.click()
        time.sleep(1)

        # Отправить пустые поля
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div:nth-child(4) > button')
        elem.click()
        time.sleep(1)

        # Проверка предупреждений
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > label:nth-child(2) > div > div.q-field__bottom.row.items-start.q-field__bottom--animated > div > div')
        self.assertEqual(elem.text, 'Введите логин', 'Нет сообщения об ошибке')

        # Переход на страницу регистрации
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div:nth-child(5) > button > span.q-btn__content.text-center.col.items-center.q-anchor--skip.justify-center.row > span')
        elem.click()
        time.sleep(1)

        # Некорректный ввод почты
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[2]//input")
        elem.send_keys('jojir90142')
        time.sleep(1)

        # Отправить форму регистрации
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div:nth-child(6) > button')
        elem.send_keys(Keys.ENTER)
        time.sleep(1)

        # Проверка предупреждений
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > label:nth-child(3) > div > div.q-field__bottom.row.items-start.q-field__bottom--animated > div > div')
        self.assertEqual(elem.text, 'Вы неправильно ввели почту', 'Нет сообщения об ошибке')

        # Ввод пароля
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[3]//input")
        elem.send_keys('qwe12')
        time.sleep(1)

        # Неверный повтор пароля
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[4]//input")
        elem.send_keys('qwe123321')
        time.sleep(1)

        # Отправить форму регистрации
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div:nth-child(6) > button')
        elem.send_keys(Keys.ENTER)
        time.sleep(1)

        # Проверка предупреждений
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > label:nth-child(4) > div > div.q-field__bottom.row.items-start.q-field__bottom--animated > div > div')
        self.assertEqual(elem.text, 'Пароль слишком короткий', 'Нет сообщения об ошибке')

        # Проверка предупреждений
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > label:nth-child(5) > div > div.q-field__bottom.row.items-start.q-field__bottom--animated > div > div')
        self.assertEqual(elem.text, 'Введенный пароль не равен введеному выше', 'Нет сообщения об ошибке')

        driver.close()
    
    def test_registration(self):

        options = webdriver.ChromeOptions()
        chrome_driver = ChromeDriverManager().install()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=options, executable_path=chrome_driver)
        
        driver.get("http://localhost:8082/#/Registration")
        self.assertEqual(driver.title, 'pin', 'Открыто не то окно')
        
        # Заполнение формы регистрации
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[1]//input")
        elem.send_keys('jojir')
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[2]//input")
        elem.send_keys('jojir90142@nefacility.com')
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[3]//input")
        elem.send_keys('qwe123321')
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[4]//input")
        elem.send_keys('qwe123321')
        time.sleep(0.2)

        # Отправить форму регистрации
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div:nth-child(6) > button')
        elem.send_keys(Keys.ENTER)
        time.sleep(1)

        with self.db_connect.connect() as connect:
            rows = connect.execute(text('SELECT * FROM public.users_customuser WHERE email LIKE :email'), email='jojir90142@nefacility.com').fetchall()
            self.assertGreaterEqual(len(rows), 0, 'Нет пользователя в базе')

            self.assertEqual(rows[0][7], 'jojir90142@nefacility.com', 'Неправильно созданный пользователь')

        # Проверка регистрации
        for _ in range(20):
            time.sleep(1)
            try:
                elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > h4')
                if elem.text == 'Авторизация':
                    break
            except NoSuchElementException:
                continue
        else:
            self.assert_(False, 'Ошибка при регистрации')

        driver.close()

    def test_check_registered_user(self):

        options = webdriver.ChromeOptions()
        chrome_driver = ChromeDriverManager().install()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=options, executable_path=chrome_driver)
        
        driver.get("http://localhost:8082/#/Registration")
        self.assertEqual(driver.title, 'pin', 'Открыто не то окно')

        # Заполнение формы регистрации
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[1]//input")
        elem.send_keys('jojir')
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[2]//input")
        elem.send_keys('jojir90142@nefacility.com')
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[3]//input")
        elem.send_keys('qwe123321')
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[4]//input")
        elem.send_keys('qwe123321')
        time.sleep(0.2)

        # Отправить форму регистрации
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div:nth-child(6) > button')
        elem.send_keys(Keys.ENTER)
        time.sleep(1)

        # Проверка предупреждений
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div.q-mx-xl.text-red')
        self.assertEqual(elem.text, 'Пользователь с такими данными уже существует', 'Нет сообщения об ошибке')

    def test_add_other_user(self):
        options = webdriver.ChromeOptions()
        chrome_driver = ChromeDriverManager().install()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=options, executable_path=chrome_driver)

        driver.get("http://localhost:8082/#/Registration")
        self.assertEqual(driver.title, 'pin', 'Открыто не то окно')

        # Создание второго пользователя
        # Заполнение формы регистрации
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[1]//input")
        elem.send_keys('popug')
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[2]//input")
        elem.send_keys('popug12345@mail.ru')
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[3]//input")
        elem.send_keys('qwe123321')
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-gutter-md']/label[4]//input")
        elem.send_keys('qwe123321')
        time.sleep(0.2)

        # Отправить форму регистрации
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div:nth-child(6) > button')
        elem.send_keys(Keys.ENTER)
        time.sleep(2)

        with self.db_connect.connect() as connect:
            rows = connect.execute(text('SELECT * FROM public.users_customuser WHERE email LIKE :email'), email='popug12345@mail.ru').fetchall()
            self.assertGreaterEqual(len(rows), 0, 'Нет пользователя в базе')

            self.assertEqual(rows[0][7], 'popug12345@mail.ru', 'Неправильно созданный пользователь')

        # Проверка регистрации
        for _ in range(20):
            time.sleep(1)
            try:
                elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > h4')
                if elem.text == 'Авторизация':
                    break
            except NoSuchElementException:
                continue
        else:
            self.assert_(False, 'Ошибка при регистрации')

        driver.close()

    def test_auth(self):

        options = webdriver.ChromeOptions()
        chrome_driver = ChromeDriverManager().install()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=options, executable_path=chrome_driver)
        
        driver.get("http://localhost:8082/#/Login")
        self.assertEqual(driver.title, 'pin', 'Открыто не то окно')

        # Заполнение формы авторизации
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-form q-gutter-md']/label[1]//input")
        elem.send_keys('jojir')
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-form q-gutter-md']/label[2]//input")
        elem.send_keys('qwe123321')
        time.sleep(0.2)

        # Войти
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div:nth-child(4) > button')
        elem.send_keys(Keys.ENTER)

        # Проверка авторизации
        for _ in range(10):
            time.sleep(1)
            try:
                elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(1) > div > div:nth-child(3) > button')
                elem.click()
                elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(6) > div > div > div:nth-child(2) > div.q-item__section.column.q-item__section--main.justify-center > div')
                if elem.text == 'Выйти':
                    break
            except NoSuchElementException:
                continue
        else:
            self.assert_(False, 'Не удалось авторизоваться')

        # Выйти
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(6) > div > div > div:nth-child(2) > div.q-item__section.column.q-item__section--main.justify-center > div')
        elem.click()
        time.sleep(1)

        driver.close()

    def test_add_boards(self):
        options = webdriver.ChromeOptions()
        chrome_driver = ChromeDriverManager().install()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=options, executable_path=chrome_driver)
        
        driver.get("http://localhost:8082/#/Login")
        self.assertEqual(driver.title, 'pin', 'Открыто не то окно')

        # Заполнение формы авторизации
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-form q-gutter-md']/label[1]//input")
        elem.send_keys('jojir')
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-form q-gutter-md']/label[2]//input")
        elem.send_keys('qwe123321')
        time.sleep(0.2)

        # Войти
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div:nth-child(4) > button')
        elem.send_keys(Keys.ENTER)

        # Проверка авторизации
        for _ in range(10):
            time.sleep(1)
            try:
                elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(1) > div > div:nth-child(3) > button')
                elem.click()
                elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(6) > div > div > div:nth-child(2) > div.q-item__section.column.q-item__section--main.justify-center > div')
                if elem.text == 'Выйти':
                    break
            except NoSuchElementException:
                continue
        else:
            self.assert_(False, 'Не удалось авторизоваться')

        # Перейти в профиль
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(6) > div > div > div:nth-child(1) > div.q-item__section.column.q-item__section--main.justify-center > div')
        elem.click()
        time.sleep(1)

        # Добавить открытую доску
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(2) > div.q-pa-md > div > div > div.q-tab-panels.q-panel-parent > div > div > div.Button > button')
        elem.click()
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(6) > div > div > div:nth-child(2)')
        elem.click()
        time.sleep(0.2)

        # Проверка отправки пустых полей
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(7) > div > div.q-dialog__inner.flex.no-pointer-events.q-dialog__inner--minimized.q-dialog__inner--standard.fixed-full.flex-center > div > div > form > div:nth-child(4) > button.q-btn.q-btn-item.non-selectable.no-outline.q-btn--standard.q-btn--rectangle.bg-orange.text-white.q-btn--actionable.q-focusable.q-hoverable')
        elem.click()
        time.sleep(0.2)

        # Проверка предупреждений
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(7) > div > div.q-dialog__inner.flex.no-pointer-events.q-dialog__inner--minimized.q-dialog__inner--standard.fixed-full.flex-center > div > div > form > label.q-field.row.no-wrap.items-start.q-field--outlined.q-input.q-field--rounded.q-field--labeled.q-field--error.q-field--highlighted.q-field--with-bottom > div > div.q-field__bottom.row.items-start.q-field__bottom--animated > div > div')
        self.assertEqual(elem.text, 'Заполните название', 'Нет сообщения об ошибке')

        # Заполнение формы создания доски
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-form q-gutter-md']/label[1]//input")
        elem.send_keys("Jojir's board")
        time.sleep(0.2)

        # Отправить форму
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(7) > div > div.q-dialog__inner.flex.no-pointer-events.q-dialog__inner--minimized.q-dialog__inner--standard.fixed-full.flex-center > div > div > form > div:nth-child(4) > button.q-btn.q-btn-item.non-selectable.no-outline.q-btn--standard.q-btn--rectangle.bg-orange.text-white.q-btn--actionable.q-focusable.q-hoverable')
        elem.click()
        time.sleep(1)

        # Проверка создания доски
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(2) > div.q-pa-md > div > div > div.q-tab-panels.q-panel-parent > div > div > div.folders > div:nth-child(1) > div > div.q-img__content.absolute-full.q-anchor--skip > div')
        self.assertEqual(elem.text, "Jojir's board lock_open", 'Название доски не соответствует заданному')

        # ------------------------------------------------------------------------------------------------------------------

        # Добавить закрытую доску
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(6) > div > div > div:nth-child(2)')
        elem.click()
        time.sleep(0.2)

        # Заполнение формы создания доски
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-form q-gutter-md']/label[1]//input")
        elem.send_keys("Jojir's board lock")
        time.sleep(0.2)

        # Выбор типа доски (закрытая)
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(7) > div > div.q-dialog__inner.flex.no-pointer-events.q-dialog__inner--minimized.q-dialog__inner--standard.fixed-full.flex-center > div > div > form > label.q-field.row.no-wrap.items-start.q-field--outlined.q-select.q-field--auto-height.q-select--without-input.q-select--without-chips.q-select--single.q-field--float.q-field--labeled > div')
        elem.click()
        time.sleep(0.5)

        elem: WebElement = driver.find_element(By.XPATH, "//div[@class='q-virtual-scroll__content']/div[2]")
        elem.click()
        time.sleep(0.2)

        # Отправить форму
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(7) > div > div.q-dialog__inner.flex.no-pointer-events.q-dialog__inner--minimized.q-dialog__inner--standard.fixed-full.flex-center > div > div > form > div:nth-child(4) > button.q-btn.q-btn-item.non-selectable.no-outline.q-btn--standard.q-btn--rectangle.bg-orange.text-white.q-btn--actionable.q-focusable.q-hoverable')
        elem.click()
        time.sleep(1)

        # Проверка создания доски
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(2) > div.q-pa-md > div > div > div.q-tab-panels.q-panel-parent > div > div > div.folders > div:nth-child(2) > div > div.q-img__content.absolute-full.q-anchor--skip > div')
        self.assertEqual(elem.text, "Jojir's board lock lock", 'Название доски не соответствует заданному')

        driver.close()

    def test_add_pin(self):
        options = webdriver.ChromeOptions()
        chrome_driver = ChromeDriverManager().install()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=options, executable_path=chrome_driver)
        
        driver.get("http://localhost:8082/#/Login")
        self.assertEqual(driver.title, 'pin', 'Открыто не то окно')

        # Заполнение формы авторизации
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-form q-gutter-md']/label[1]//input")
        elem.send_keys('jojir')
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-form q-gutter-md']/label[2]//input")
        elem.send_keys('qwe123321')
        time.sleep(0.2)

        # Войти
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div:nth-child(4) > button')
        elem.send_keys(Keys.ENTER)

        # Проверка авторизации
        for _ in range(10):
            time.sleep(1)
            try:
                elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(1) > div > div:nth-child(3) > button')
                elem.click()
                elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(6) > div > div > div:nth-child(2) > div.q-item__section.column.q-item__section--main.justify-center > div')
                if elem.text == 'Выйти':
                    break
            except NoSuchElementException:
                continue
        else:
            self.assert_(False, 'Не удалось авторизоваться')

        # Перейти в профиль
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(6) > div > div > div:nth-child(1) > div.q-item__section.column.q-item__section--main.justify-center > div')
        elem.click()
        time.sleep(1)

        # Добавить пин на доску
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(2) > div.q-pa-md > div > div > div.q-tab-panels.q-panel-parent > div > div > div.Button > button')
        elem.click()
        time.sleep(0.5)

        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(6) > div > div > div:nth-child(1)')
        elem.click()
        time.sleep(0.5)

        # Отправить пустую форму
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(7) > div > div.q-dialog__inner.flex.no-pointer-events.q-dialog__inner--minimized.q-dialog__inner--standard.fixed-full.flex-center > div > form > div.row.self-center.q-mx-lg.q-mt-xl > button.q-btn.q-btn-item.non-selectable.no-outline.q-btn--standard.q-btn--rectangle.bg-orange.text-white.q-btn--actionable.q-focusable.q-hoverable')
        elem.click()
        time.sleep(0.5)

        # Проверка предупреждения
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(7) > div > div.q-dialog__inner.flex.no-pointer-events.q-dialog__inner--minimized.q-dialog__inner--standard.fixed-full.flex-center > div > form > div.row.justify-between.q-mx-lg > div.col-6 > label.q-field.row.no-wrap.items-start.q-field--outlined.q-input.q-field--rounded.q-field--labeled.q-field--error.q-field--highlighted.q-field--with-bottom > div > div.q-field__bottom.row.items-start.q-field__bottom--animated > div > div')
        self.assertEqual(elem.text, "Заполните название", 'Нет сообщения об ошибке')

        # Выбрать доску
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(7) > div > div.q-dialog__inner.flex.no-pointer-events.q-dialog__inner--minimized.q-dialog__inner--standard.fixed-full.flex-center > div > form > div.row.justify-between.q-mx-lg > div.col-6 > div > label > div > div')
        elem.click()
        time.sleep(0.5)

        elem: WebElement = driver.find_element(By.XPATH, "//div[@class='q-virtual-scroll__content']/div[1]")
        elem.click()
        time.sleep(0.5)

        # Название пина
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-form column justify-around q-mt-lg']//label[1]//input")
        elem.send_keys("Попуг")
        time.sleep(0.2)

        # Описание пина
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-form column justify-around q-mt-lg']//label[2]//textarea")
        elem.send_keys("Красивый попуг")
        time.sleep(0.2)

        # Загрузка изображения
        img = str(Path(__file__).parent.absolute()) + '/img/popug.jpg'
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(7) > div > div.q-dialog__inner.flex.no-pointer-events.q-dialog__inner--minimized.q-dialog__inner--standard.fixed-full.flex-center > div > form > div.row.justify-between.q-mx-lg > div.col-5.column.justify-between > div > div.q-uploader__header.bg-orange > div > a > span.q-btn__content.text-center.col.items-center.q-anchor--skip.justify-center.row > input')
        elem.send_keys(img)
        time.sleep(2)

        # Отправить форму
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(7) > div > div.q-dialog__inner.flex.no-pointer-events.q-dialog__inner--minimized.q-dialog__inner--standard.fixed-full.flex-center > div > form > div.row.self-center.q-mx-lg.q-mt-xl > button.q-btn.q-btn-item.non-selectable.no-outline.q-btn--standard.q-btn--rectangle.bg-orange.text-white.q-btn--actionable.q-focusable.q-hoverable')
        elem.click()
        time.sleep(2)

        # Проверка созданного пина на доске
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(2) > div.q-pa-md > div > div > div.q-tab-panels.q-panel-parent > div > div > div.folders > div:nth-child(1)')
        elem.click()
        time.sleep(1)

        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(2) > div > div > div > figure > div.q-card__actions.justify-start.q-card__actions--horiz.row > div')
        self.assertEqual(elem.text, "Попуг", 'Нет созданного пина на доске')

        # Проверка созданного пина на главной странице
        driver.get("http://localhost:8082/")
        time.sleep(0.1)

        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(2) > div > div > div > figure > div.q-card__actions.justify-start.q-card__actions--horiz.row > div')
        self.assertEqual(elem.text, "Попуг", 'Нет созданного пина на доске')

        driver.close()
    
    def test_save_other_user_pin(self):
        options = webdriver.ChromeOptions()
        chrome_driver = ChromeDriverManager().install()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=options, executable_path=chrome_driver)

        driver.get("http://localhost:8082/#/Login")
        self.assertEqual(driver.title, 'pin', 'Открыто не то окно')
        
        # Заполнение формы авторизации
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-form q-gutter-md']/label[1]//input")
        elem.send_keys('popug')
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-form q-gutter-md']/label[2]//input")
        elem.send_keys('qwe123321')
        time.sleep(0.2)

        # Войти
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div:nth-child(4) > button')
        elem.send_keys(Keys.ENTER)

        # Проверка авторизации
        for _ in range(10):
            time.sleep(1)
            try:
                elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(1) > div > div:nth-child(3) > button')
                elem.click()
                elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(6) > div > div > div:nth-child(2) > div.q-item__section.column.q-item__section--main.justify-center > div')
                if elem.text == 'Выйти':
                    break
            except NoSuchElementException:
                continue
        else:
            self.assert_(False, 'Не удалось авторизоваться')
        
        # Открыть чужой пин
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(2) > div > div > div')
        elem.click()
        time.sleep(1)

        # Выбрать доску
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(2) > div > div > div > div.row.col-6 > div.row.justify-between.col-12 > div.row.justify-between.col-9.self-center > label > div > div')
        elem.click()
        time.sleep(0.5)

        # Создать доску
        elem: WebElement = driver.find_element(By.XPATH, "//div[@class='q-menu q-position-engine scroll']/button")
        elem.click()
        time.sleep(0.5)

        # Заполнение формы создания доски
        elem: WebElement = driver.find_element(By.XPATH, "//form[@class='q-form q-gutter-md']//label[1]//input")
        elem.send_keys("Новая доска")
        time.sleep(0.5)

        # Отправить форму
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(7) > div > div.q-dialog__inner.flex.no-pointer-events.q-dialog__inner--minimized.q-dialog__inner--standard.fixed-full.flex-center > div > div > form > div:nth-child(4) > button.q-btn.q-btn-item.non-selectable.no-outline.q-btn--standard.q-btn--rectangle.bg-orange.text-white.q-btn--actionable.q-focusable.q-hoverable')
        elem.click()
        time.sleep(1)

        # Выбрать доску
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(2) > div > div > div > div.row.col-6 > div.row.justify-between.col-12 > div.row.justify-between.col-9.self-center > label > div > div')
        elem.click()
        time.sleep(0.1)
        elem.click()
        time.sleep(0.1)

        elem: WebElement = driver.find_element(By.XPATH, "//div[@class='q-virtual-scroll__content']/div[1]")
        elem.click()
        time.sleep(0.2)

        # Сохранить пин
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, "#app > div:nth-child(2) > div > div > div > div.row.col-6 > div.row.justify-between.col-12 > div.row.justify-between.col-9.self-center > button")
        elem.click()
        time.sleep(0.2)

        # Сохранить название пина
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, "#app > div:nth-child(2) > div > div > div > div.row.col-6 > div.column.q-mx-sm.col-12 > div.self-center.q-my-sm.text-h5")
        pin_text = elem.text

        # Переход в свой профиль
        driver.get('http://localhost:8082/#/profile/popug')
        time.sleep(2)

        # Проверка пина на своей доске
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(2) > div.q-pa-md > div > div > div.q-tab-panels.q-panel-parent > div > div > div.folders > div:nth-child(1)')
        elem.click()
        time.sleep(0.2)

        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(2) > div > div > div > figure > div.q-card__actions.justify-start.q-card__actions--horiz.row > div')
        self.assertEqual(elem.text, pin_text, 'Нет сохраненного пина на доске')

        driver.close()
    
    @classmethod
    def tearDownClass(cls):
        del cls.db_connect
        os.system(f"docker-compose stop")
        cls._proc.terminate()
        del cls._proc
        os.system(f"docker-compose rm -f db")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(MainTestCase('test_incorrect_input'))
    suite.addTest(MainTestCase('test_registration'))
    suite.addTest(MainTestCase('test_check_registered_user'))
    suite.addTest(MainTestCase('test_add_other_user'))
    suite.addTest(MainTestCase('test_auth'))
    suite.addTest(MainTestCase('test_add_boards'))
    suite.addTest(MainTestCase('test_add_pin'))
    suite.addTest(MainTestCase('test_save_other_user_pin'))
    return suite

if __name__ == "__main__":
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())
