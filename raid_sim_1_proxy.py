from selenium_driverless.sync import webdriver
from selenium_driverless.types.by import By
import time
import random
import re

try:
    import config
except ImportError:
    raise SystemExit("Chua co file config.py - hay copy config.example.py thanh config.py va dien thong tin.")


class BotTravian:
    def __init__(self):
        self.base_url = config.SERVER_URL.rstrip('/')
        self.maxtime = config.MAX_CYCLE_SLEEP
        self.mintime = config.MIN_CYCLE_SLEEP
        self.passw = config.PASSWORD
        self.user = config.USERNAME
        self.sim_village = config.SIM_VILLAGE_NAME
        self.click_offset = min(max(config.CLICK_OFFSET, 0), 0.45)
        self.proxy = config.PROXY
        self.agent = config.USER_AGENT
        self.dangnhap = False

        option = webdriver.ChromeOptions()
        if self.proxy:
            option.add_argument(f"--proxy-server={self.proxy}")
        option.add_argument(f"--user-agent={self.agent}")
        self.driver = webdriver.Chrome(options=option)
        if self.proxy:
            self.driver.set_single_proxy(self.proxy)
        self.driver.normalize_window()

    def url(self, path=""):
        """Tao url day du tu SERVER_URL, vd: self.url('dorf1.php')."""
        return f"{self.base_url}/{path.lstrip('/')}"

    def human_click(self, element):
        """Click vao 1 diem ngau nhien quanh tam element thay vi dung tam."""
        o = self.click_offset
        try:
            element.click(
                bias_a=random.uniform(0.5 - o, 0.5 + o),
                bias_b=random.uniform(0.5 - o, 0.5 + o),
                spread_a=random.uniform(0.6, 1.0),
                spread_b=random.uniform(0.6, 1.0),
                border=0.1,
            )
        except TypeError:
            # phien ban selenium_driverless cu khong ho tro tham so bias/spread
            element.click()

    def cyclesleep(self):
        t = random.randint(self.mintime, self.maxtime)
        print(f" sleep {t} giay")
        time.sleep(t)

    @staticmethod
    def randomsleep(z=1):
        t = random.randint(1, 3)
        time.sleep(t * z)

    def login(self):
        self.driver.get(self.url(), wait_load=True)
        self.randomsleep()
        login = self.driver.find_element(By.XPATH, "//input[contains(@name,'name')]", timeout=10)
        login.write(f"{self.user}")
        time.sleep(2)
        password = self.driver.find_element(By.XPATH, """//input[@type='password']""", timeout=10)
        password.write(f"{self.passw}")
        time.sleep(2)
        try:
            logas = self.driver.find_element(By.XPATH, """(//div[contains(.,'Login')])[13]""", timeout=10)
            self.human_click(logas)
        except:
            pass
        self.randomsleep(4)
        self.dangnhap = True

    def farmlist(self):
        try:
            #find farmlist plus link
            link = self.driver.find_element(By.XPATH,
                                            """//span[@class='name'][contains(.,'Farmlist')]""",
                                            timeout=10)
            self.human_click(link)
            time.sleep(4)
        except:
            print('Khong tim duoc farmlist plus link')
            pass
        try:
            farmlist = self.driver.find_element(By.XPATH,
                                            """(//div[contains(.,'Start all farm lists')])[10]""",
                                            timeout=10)
            self.human_click(farmlist)
            time.sleep(11)
            print('Da click farmlist')
        except:
            print('Khong click duoc all farm')
            pass

    def open_sim_village(self):
        """Mo trang mo tai nguyen (dorf1) cua lang SIM bang cach click vao ten lang."""
        try:
            self.driver.get(self.url('dorf1.php'), wait_load=True)
            self.randomsleep(1)
            village = self.driver.find_element(
                By.XPATH, f"""//*[normalize-space(text())='{self.sim_village}']""", timeout=10)
            self.human_click(village)
            self.randomsleep(1)
            dorf = self.driver.find_element(By.XPATH, """//a[@href='/dorf1.php']""", timeout=10)
            self.human_click(dorf)
            self.randomsleep(1)
        except:
            print(f'Khong mo duoc lang {self.sim_village}')

    def sim(self):
        self.open_sim_village()
        upgrade = []
        for i in range(1, 19):
            try:
                button = self.driver.find_element(By.XPATH, f"""//a[@href='/build.php?id={i}']""", timeout=10)
                button_class = self.driver.execute_script('return arguments[0].className;', button)
                button_class = str(button_class).strip()

                #print(button_class)

                if button_class[:4] == 'good':
                    lver = re.findall(r'level(\d+)', button_class.replace(' ', ''))
                    level = int(lver[-1]) if lver else 0
                    upgrade.append((level, i))
            except:
                pass
        upgrade.sort()
        #print(upgrade)
        upgrade = upgrade[:2]
        #print(upgrade)
        for _, bton in upgrade:
            try:
                button = self.driver.find_element(By.XPATH, f"""//a[@href='/build.php?id={bton}']""", timeout=10)
                self.human_click(button)
                time.sleep(2)
                butoonup = self.driver.find_element(By.XPATH, """//button[@class='textButtonV1 green build']""", timeout=3)
                self.human_click(butoonup)
                time.sleep(2)
            except:
                pass
            time.sleep(2)
            try:
                self.driver.refresh()
                self.open_sim_village()
            except:
                pass
        print('Da sim lang')

    def trangchu(self):
        if self.dangnhap:
            self.driver.refresh()
            self.driver.get(self.url('dorf1.php'), wait_load=True)
            self.randomsleep()
            return True
        else:
            return False

    def thoatra(self):
        self.driver.refresh()
        self.randomsleep()
        thoatra = self.driver.find_element(By.XPATH, """(//a[@href='/logout'])[2]""", timeout=10)
        self.human_click(thoatra)
        self.driver.get(self.url())

    def quit(self):
        self.driver.refresh()
        self.driver.quit()


if __name__ == "__main__":
    bot = BotTravian()
    while True:
        if bot.dangnhap == False:
            bot.login()
        bot.sim()
        #bot.farmlist()
        #time.sleep(2)
        #bot.traincap()
        bot.cyclesleep()
