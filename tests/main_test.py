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


class MainTest(unittest.TestCase):

    def setUp(self) -> None:
        os.chdir(ROOT_DIR)
        self._proc = subprocess.Popen(["docker-compose", "up"], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        while True:
            s = self._proc.stdout.readline().decode('cp1251')
            print(s)
            if s.find('ready to accept connections') > -1:
                break
        self.db_connect = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5444/pin')
    
    def test_main(self):
        options = webdriver.ChromeOptions()
        chrome_driver = ChromeDriverManager().install()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=options, executable_path=chrome_driver)
        driver.get("http://localhost:8082/")
        self.assertEqual(driver.title, 'pin', 'Открыто не то окно')

        # Переход на страницу авторизации
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div:nth-child(1) > div > div:nth-child(3) > button')
        elem.click()
        time.sleep(0.1)

        # Переход на страницу регистрации
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div:nth-child(5) > button > span.q-btn__content.text-center.col.items-center.q-anchor--skip.justify-center.row > span')
        elem.click()
        time.sleep(0.1)
        
        # Заполнение формы регистрации
        # //form[@class='q-field__native q-placeholder']/label[1]//input
        elem: WebElement = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/form/label[1]/div/div[1]/div/input")
        elem.send_keys('jojir')
        time.sleep(0.1)

        elem: WebElement = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/form/label[2]/div/div[1]/div/input")
        elem.send_keys('jojir90142@nefacility.com')
        time.sleep(0.1)

        elem: WebElement = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/form/label[3]/div/div[1]/div/input")
        elem.send_keys('qwe123321')
        time.sleep(0.1)

        elem: WebElement = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/form/label[4]/div/div[1]/div/input")
        elem.send_keys('qwe123321')
        time.sleep(0.1)

        # Отправить форму регистрации
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div:nth-child(6) > button')
        elem.click()
        time.sleep(0.1)

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

        with self.db_connect.connect() as connect:
            rows = connect.execute(text('SELECT * FROM public.users_customuser WHERE email LIKE :email'), email='jojir90142@nefacility.com').fetchall()
            self.assertGreaterEqual(len(rows), 0, 'Нет пользователя в базе')

            self.assertEqual(rows[0][7], 'jojir90142@nefacility.com', 'Неправильно созданный пользователь')
        
        # # Вернуться к странице авторизации
        # elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#window_reg > form > div:nth-child(7) > button > span.q-btn__content.text-center.col.items-center.q-anchor--skip.justify-center.row > span')
        # elem.click()
        # time.sleep(0.1)

        # Заполнение формы авторизации
        elem: WebElement = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/form/label[1]/div/div[1]/div/input")
        elem.send_keys('jojir')
        time.sleep(0.1)

        elem: WebElement = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/form/label[2]/div/div[1]/div/input")
        elem.send_keys('qwe123321')
        time.sleep(0.1)

        # Войти
        elem: WebElement = driver.find_element(By.XPATH, '//*[@id="window_reg"]/form/div[1]/button')
        elem.click()

        # Проверка авторизации
        for _ in range(10):
            time.sleep(1)
            try:
                elem: WebElement = driver.find_element(By.CSS_SELECTOR, '#app > div > div:nth-child(1) > div > div:nth-child(3) > button.q-btn.q-btn-item.non-selectable.no-outline.q-btn--standard.q-btn--rectangle.bg-black.text-white.q-btn--actionable.q-focusable.q-hoverable.q-btn-dropdown.q-btn-dropdown--simple.text-orange > span.q-btn__content.text-center.col.items-center.q-anchor--skip.justify-center.row.no-wrap.text-no-wrap > i.notranslate.material-icons.q-icon.q-btn-dropdown__arrow.q-btn-dropdown__arrow-container')
                elem.click()
                elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(5) > div > div > div:nth-child(2) > div.q-item__section.column.q-item__section--main.justify-center > div')
                if elem.text == 'Выйти':
                    break
            except NoSuchElementException:
                continue
        else:
            self.assert_(False, 'Не удалось авторизоваться')

        # Выйти
        elem: WebElement = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(5) > div > div > div:nth-child(2) > div.q-item__section.column.q-item__section--main.justify-center > div')
        elem.click()
        time.sleep(3)

        driver.close()
    
    def tearDown(self) -> None:
        del self.db_connect
        os.system(f"docker-compose stop")
        self._proc.terminate()
        del self._proc
        os.system(f"docker-compose rm -f db")

if __name__ == "__main__":
    unittest.main()
