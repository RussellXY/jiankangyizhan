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
#chrome_options.add_argument("--save-page-as-mhtml")
browser = webdriver.Chrome(
desired_capabilities=capabilities, options=chrome_options)
loginUrl = "https://hk.sz.gov.cn:8118/userPage/login"
ticketUrl = "https://hk.sz.gov.cn:8118/passInfo/detail"
host = "https://hk.sz.gov.cn:8118"

class TicketGetter:

    def __init__(self):
        self.loginCookies = []
    
    def saveCurrentHtml(self, name):
        try:
            with open('{}.html'.format(name), 'wb') as f:   # 根据5楼的评论，添加newline=''
                f.write(browser.page_source.encode('utf-8'))
        except Exception as error:
            print(error)

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

    def macNotify(self, title, subtitle, message):
        t = '-title {!r}'.format(title)
        s = '-subtitle {!r}'.format(subtitle)
        m = '-message {!r}'.format(message)
        os.system('terminal-notifier {}'.format(' '.join([m, t, s])))

    def windowsNotify(self, title, message):
        # windows系统通知 pip install win10toast
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(title, message)

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
                if self.is403():
                    time.sleep(3*60)
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
        path = 'cookies.pkl'
        if os.path.exists(path):
            os.remove(path)
        cookies = browser.get_cookies()
        with open(path, 'wb') as fw:
            pickle.dump(cookies, fw)

    def waitForTicket(self):
        loopFlag = True
        while loopFlag:
            if browser.current_url == loginUrl:
                self.login()

            timeArray = time.localtime()
            jsTime = time.strftime("%Y-%m-%d %H:%M:%S")
            nowTime = jsTime[11:19]

            if (timeArray.tm_hour >= 10) and (timeArray.tm_hour < 20):
                browser.get(ticketUrl)
                indexes = [3,2,4,5,6,7,1]
                for index in indexes:
                    try:
                        bookBtn = browser.find_element_by_xpath('//*[@id="divSzArea"]/section[{}]/div/div[3]/div/a'.format(index))
                        bookBtn.click()
                        time.sleep(0.5)
                        try:
                            browser.find_element_by_id('TencentCaptcha').click()
                        except Exception as error:
                            print(error)
                        loopFlag = False
                        break
                    except Exception as error:
                        continue
                    
                time.sleep(1.5)
                if self.is403():
                    time.sleep(3*60)
                    # print("当前无票，正在刷票...")
            else:
                print("{} 还未到抢票时间".format(nowTime))
                time.sleep(0.5)

    def notifyAndWait(self):
        self.save()
        # 预定确认页面验证码自动填写和提交
        try:
            system = platform.system()
            if system == "Windows":
                # windows系统通知 pip install win10toast
                self.windowsNotify(title='注意', message='抢到票了')
            elif system == "Darwin":
                # mac系统通知
                self.macNotify(title='注意', subtitle='注意', message='抢到票了')
        except Exception as error:
            print(error)
    
    def waitForConfirm(self):
            while True:
                try:
                    confirmBtn = browser.find_element_by_id('btn_confirmOrder')
                    btnClass = confirmBtn.get_attribute('class')
                    if (btnClass.__contains__('Btn-l-gray')):
                        time.sleep(0.5)
                        continue
                    confirmBtn.click()
                    break
                except Exception as error:
                    time.sleep(0.5)
                finally:
                    print("等待确认")
                    time.sleep(5)

    def save(self):
        with open('download.html', 'wb') as f:
            time.sleep(2)
            f.write(browser.page_source.encode('utf-8', 'ignore'))
    
    def is403(self):
        content = browser.page_source
        return content.__contains__('403')

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
        self.waitForConfirm()


if __name__ == '__main__':
    while True:
        try:
            getter = TicketGetter()
            getter.run()
        except Exception as error:
            print(error)
