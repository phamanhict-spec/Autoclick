from selenium_driverless.sync import webdriver
from selenium_driverless.types.by import By
import time
import random
import re
import base64
import socket
import threading
from urllib.parse import urlsplit, unquote

try:
    import config
except ImportError:
    raise SystemExit("Chua co file config.py - hay copy config.example.py thanh config.py va dien thong tin.")


class LocalProxyForwarder:
    """Proxy trung gian chay tren may (127.0.0.1), tu dong gan user/pass roi chuyen tiep sang proxy that.

    Chrome khong nhan user/pass trong --proxy-server, con set_single_proxy() cua selenium_driverless
    can extension ma Chrome ban moi (137+) khong cho nap nua. Vi vay Chrome se ket noi toi proxy
    trung gian nay (khong can mat khau), proxy trung gian them header xac thuc va gui sang proxy that.
    """

    def __init__(self, proxy_url):
        p = urlsplit(proxy_url)
        self.upstream = (p.hostname, p.port or 80)
        creds = f"{unquote(p.username or '')}:{unquote(p.password or '')}"
        self.auth_header = b"Proxy-Authorization: Basic " + base64.b64encode(creds.encode()) + b"\r\n"
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("127.0.0.1", 0))
        self.server.listen(100)
        self.port = self.server.getsockname()[1]
        threading.Thread(target=self._accept_loop, daemon=True).start()

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}"

    def _accept_loop(self):
        while True:
            client, _ = self.server.accept()
            threading.Thread(target=self._handle, args=(client,), daemon=True).start()

    def _handle(self, client):
        upstream = None
        try:
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = client.recv(65536)
                if not chunk:
                    return
                data += chunk
            head, body = data.split(b"\r\n\r\n", 1)
            lines = [l for l in head.split(b"\r\n")
                     if not l.lower().startswith((b"proxy-authorization:", b"proxy-connection:", b"connection:"))]
            if not lines[0].upper().startswith(b"CONNECT"):
                # moi request http thuong dung 1 ket noi rieng de request nao cung co header xac thuc
                lines.append(b"Connection: close")
            request = b"\r\n".join(lines) + b"\r\n" + self.auth_header + b"\r\n" + body
            upstream = socket.create_connection(self.upstream, timeout=30)
            upstream.settimeout(None)
            upstream.sendall(request)
            t = threading.Thread(target=self._pipe, args=(upstream, client), daemon=True)
            t.start()
            self._pipe(client, upstream)
            t.join()
        except OSError:
            pass
        finally:
            for s in (client, upstream):
                if s:
                    try:
                        s.close()
                    except OSError:
                        pass

    @staticmethod
    def _pipe(src, dst):
        try:
            while True:
                chunk = src.recv(65536)
                if not chunk:
                    break
                dst.sendall(chunk)
        except OSError:
            pass
        finally:
            try:
                dst.shutdown(socket.SHUT_WR)
            except OSError:
                pass


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
            if urlsplit(self.proxy).username:
                # proxy co user/pass -> di qua proxy trung gian (xem LocalProxyForwarder)
                self.forwarder = LocalProxyForwarder(self.proxy)
                option.add_argument(f"--proxy-server={self.forwarder.url}")
            else:
                option.add_argument(f"--proxy-server={self.proxy}")
        option.add_argument(f"--user-agent={self.agent}")
        self.driver = webdriver.Chrome(options=option)
        self.driver.normalize_window()

    def url(self, path=""):
        """Tao url day du tu SERVER_URL, vd: self.url('dorf1.php')."""
        return f"{self.base_url}/{path.lstrip('/')}"

    def human_click(self, element):
        """Click vao 1 diem ngau nhien quanh tam element thay vi dung tam.

        Tu tinh toa do click (khong dung element.click() cua selenium_driverless vi ham do goi
        np.cross voi vector 2 chieu - NumPy ban moi da bo, se bao loi ValueError).
        """
        o = self.click_offset
        rect = self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});"
            "const r = arguments[0].getBoundingClientRect();"
            "return [r.left, r.top, r.width, r.height];", element)
        time.sleep(random.uniform(0.2, 0.5))
        left, top, width, height = rect
        if width < 1 or height < 1:
            # element khong hien thi (kich thuoc 0) -> click bang JS
            self.driver.execute_script("arguments[0].click();", element)
            return
        x = left + width * random.uniform(0.5 - o, 0.5 + o)
        y = top + height * random.uniform(0.5 - o, 0.5 + o)
        self.driver.current_pointer.click(x, y)

    def human_write(self, element, text):
        """Click vao o nhap lieu (lech tam nhu human_click) roi go text."""
        self.human_click(element)
        time.sleep(random.uniform(0.2, 0.5))
        element.write(text, click_on=False)

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
        self.human_write(login, f"{self.user}")
        time.sleep(2)
        password = self.driver.find_element(By.XPATH, """//input[@type='password']""", timeout=10)
        self.human_write(password, f"{self.passw}")
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
