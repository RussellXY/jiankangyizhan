from asyncio import sleep
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import ddddocr
import cv2
import time
import os
import platform
import time
import pickle

capabilities = webdriver.DesiredCapabilities.CHROME

# proxy setting
# prox = Proxy()
# prox.proxy_type = ProxyType.MANUAL
# prox.socks_proxy = '127.0.0.1:7891'
# prox.socks_version = 5
# prox.add_to_capabilities(capabilities)

chrome_options = Options()
#chrome_options.add_argument("--user-data-dir=chrome-data")
browser = webdriver.Chrome(
    desired_capabilities=capabilities, options=chrome_options)
loginUrl = "https://hk.sz.gov.cn:8118/userPage/login"
ticketUrl = "https://hk.sz.gov.cn:8118/passInfo/detail"


class TicketGetter:

    def __init__(self):
        self.loginCookies = []

    def verify(self):
        img_ = browser.find_element_by_id("img_verify")
        data = img_.screenshot_as_png  # 截图的方法是最好的！
        with open('code.png', 'wb') as f:
            f.write(data)

        # 卷王ocr
        ocr = ddddocr.DdddOcr()
        image = cv2.imread("code.png")
        img2 = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        img2 = cv2.inRange(img2, lowerb=110, upperb=255)
        _, img_bytes = cv2.imencode('.png', img2)
        img_bytes = img_bytes.tobytes()
        res = ocr.classification(img_bytes)
        # print(res)
        return res

    def macNotify(title, subtitle, message):
        t = '-title {!r}'.format(title)
        s = '-subtitle {!r}'.format(subtitle)
        m = '-message {!r}'.format(message)
        os.system('terminal-notifier {}'.format(' '.join([m, t, s])))

    def windowsNotify(title, message):
        # windows系统通知 pip install win10toast
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast("注意", "抢到票了!!!")

    def loginByMyself(self):
        while browser.current_url == loginUrl:
            time.sleep(1)

    def login(self):
        while browser.current_url == loginUrl:
            # 可能有弹出框的话就先去掉弹出框
            try:
                time.sleep(1)
                browser.find_element_by_xpath(
                    '//button[@type="button" and @onclick="closeLoginHint()"]').click()
            except Exception as error:
                print(error)

            try:
                accountType = Select(
                    browser.find_element_by_id('select_certificate'))
                accountType.select_by_value('3')

                account = browser.find_element_by_id('input_idCardNo')
                account.clear()
                account.send_keys('')  # 需要在此输入通行证号码

                password = browser.find_element_by_id('input_pwd')
                password.clear()
                password.send_keys('')  # 需要在此输入密码

                # 自动识别验证码
                verifyCode = browser.find_element_by_id('input_verifyCode')
                verifyCode.clear()
                verifyCode.send_keys(self.verify())

                browser.find_element_by_id('btn_login').click()
                time.sleep(1.5)
                if browser.current_url == loginUrl:
                    browser.find_element_by_id("img_verify").click()
                    time.sleep(0.5)
                    continue

                self.saveCookies()
            except Exception as error:
                time.sleep(1)
                browser.find_element_by_id("img_verify").click()
                print('登陆失败重新登陆')

    def getCookies(self):
        """ 读取保存的cookies """
        try:
            with open('cookies.pkl', 'rb') as fr:
                cookies = pickle.load(fr)

            self.loginCookies.clear()
            for cookie in cookies:
                self.loginCookies.append(cookie)
            return True
        except Exception as e:
            print('-' * 10, '加载cookies失败', '-' * 10)
            print(e)
            return False

    def saveCookies(self):
        cookies = browser.get_cookies()
        with open('cookies.pkl', 'wb') as fw:
            pickle.dump(cookies, fw)

    def waitForTicket(self):
        while True:
            if browser.current_url == loginUrl:
                self.login()

            timeArray = time.localtime()
            jsTime = time.strftime("%Y-%m-%d %H:%M:%S")
            nowTime = jsTime[11:19]

            if (timeArray.tm_hour >= 10) and (timeArray.tm_hour < 20):
                browser.get(ticketUrl)
                try:
                    browser.find_element_by_class_name('orange').click()
                    break
                except Exception:
                    time.sleep(2)
                    print("当前无票，正在刷票...")
            else:
                print("{} 还未到抢票时间".format(nowTime))
                time.sleep(0.5)

    def notifyAndWait(self):
        # 预定确认页面验证码自动填写和提交
        try:
            # browser.get_screenshot_as_file('spider/screenshot.png')
            # element = browser.find_element_by_id('img_verify')
            # left = int(element.location['x'])
            # top = int(element.location['y'])
            # right = int(element.location['x'] + element.size['width'])
            # bottom = int(element.location['y'] + element.size['height'])
            # im = Image.open('spider/screenshot.png')
            # im = im.crop((left, top, right, bottom))
            # im.save('spider/code.png')
            # ocr=ddddocr.DdddOcr()
            # img=cv2.imread("spider/code.png")
            # img2 = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            # img2 = cv2.inRange(img2, lowerb=110, upperb=255)
            # _,img_bytes=cv2.imencode('.png', img2)
            # img_bytes=img_bytes.tobytes()
            # res=ocr.classification(img_bytes)
            # print(res)
            # verifyCode1=browser.find_element_by_id('checkCode')
            # verifyCode1.send_keys(res)
            # browser.find_element_by_id('btnSubmit').click()
            # browser.find_element_by_xpath("//span[text()=\"确定\"]").click()
            system = platform.system()
            if system == "Windows":
                # windows系统通知 pip install win10toast
                self.windowsNotify(title='注意', message='抢到票了')
            elif system == "Darwin":
                # mac系统通知
                self.macNotify(title='注意', subtitle='注意', message='抢到票了')
        except Exception as error:
            print(error)
        finally:
            while True:
                time.sleep(5)
                print('抢到票了')

    def run(self):
        hasCookies = self.getCookies()
        if hasCookies == False:
            browser.get(loginUrl)
            self.login()
        else:
            browser.get(loginUrl)
            for cookies in self.loginCookies:
                browser.add_cookie(cookies)
            browser.get(loginUrl)
            # self.loginByMyself()
            time.sleep(0.5)

        browser.set_page_load_timeout(200)
        browser.set_script_timeout(200)
        self.waitForTicket()
        self.notifyAndWait()


if __name__ == '__main__':
    while True:
        try:
            getter = TicketGetter()
            getter.run()
        except Exception as error:
            print(error)
