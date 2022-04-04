from asyncio import sleep
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import ddddocr
from PIL import Image
import requests
import cv2
import numpy as np
import time
#不重要的库
# import winsound
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os
import platform

prox = Proxy()
prox.proxy_type = ProxyType.MANUAL
prox.socks_proxy = '127.0.0.1:7891'
prox.socks_version = 5
capabilities = webdriver.DesiredCapabilities.CHROME
prox.add_to_capabilities(capabilities)

chromedriver = '/usr/local/bin/chromedriver'

browser=webdriver.Chrome(desired_capabilities=capabilities)#需要修改对应browser drive的路径

loginUrl="https://hk.sz.gov.cn:8118/userPage/login"
browser.get(loginUrl)
time.sleep(1)
browser.find_element_by_xpath('//button[@type="button" and @onclick="closeLoginHint()"]').click()

while browser.current_url==loginUrl:
    try:
        accountType=Select(browser.find_element_by_id('select_certificate'))
        accountType.select_by_value('3')

        account=browser.find_element_by_id('input_idCardNo')
        account.clear()
        account.send_keys('E05344677')#需要在此输入通行证号码

        password=browser.find_element_by_id('input_pwd')
        password.clear()
        password.send_keys('95QmqhCGeCackgRp')#需要在此输入密码

        #验证码截取
        browser.get_screenshot_as_file('spider/screenshot.png')
        element = browser.find_element_by_id('img_verify')
        left = int(element.location['x'])
        top = int(element.location['y'])
        right = int(element.location['x'] + element.size['width'])
        bottom = int(element.location['y'] + element.size['height'])
        im = Image.open('spider/screenshot.png')
        im = im.crop((left, top, right, bottom))
        im.save('spider/code.png')

        #验证码识别
        ocr=ddddocr.DdddOcr()
        img=cv2.imread("spider/code.png")
        img2 = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        img2 = cv2.inRange(img2, lowerb=110, upperb=255)
        _,img_bytes=cv2.imencode('.png', img2)
        img_bytes=img_bytes.tobytes()
        res=ocr.classification(img_bytes)
        print(res)

        verifyCode=browser.find_element_by_id('input_verifyCode')
        verifyCode.clear()
        verifyCode.send_keys(res)

        browser.find_element_by_id('btn_login').click()
        time.sleep(1.5)
        if browser.current_url == loginUrl:
            browser.find_element_by_id("img_verify").click()
            time.sleep(0.5)
    except Exception as error:
        time.sleep(1)
        print('登陆失败重新登陆')

#get time by using taobao api，这一行之前的代码可以在10点前执行
import json
from urllib import request
from urllib.request import Request,urlopen
import time

def macNotify(title, subtitle, message):
    t = '-title {!r}'.format(title)
    s = '-subtitle {!r}'.format(subtitle)
    m = '-message {!r}'.format(message)
    os.system('terminal-notifier {}'.format(' '.join([m, t, s])))

def windowsNotify(title, message):
    # windows系统通知 pip install win10toast
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    toaster.show_toast("注意","抢到票了!!!")

browser.set_page_load_timeout(200)
browser.set_script_timeout(200)
c=browser.get_cookies()
cookies={}
for cookie in c:
    cookies[cookie['name']]=cookie['value']
#print(cookies)
head={
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36' 
}
url1="http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp"
r=Request(url1)
js=urlopen(r)
data=js.read()
data=str(data)
dt=int(data[149:162])/1000-time.time()
while 1==1:
    timeArray=time.localtime(time.time()+dt)
    jsTime=time.strftime("%Y-%m-%d %H:%M:%S")
    nowTime=jsTime[11:19]

    if nowTime=="10:00:00":
        ticketUrl="https://hk.sz.gov.cn:8118/passInfo/detail"
        browser.get(ticketUrl)
        #browser.find_element_by_id('a_canBookHotel').click()
        element=WebDriverWait(browser,120,0.1).until(
            EC.presence_of_element_located((By.ID,"divSzArea"))
            )
        try:
            browser.find_element_by_class_name('orange').click()
            print(nowTime)
            break
        except Exception:
            time.sleep(0.8)
            print("当前无票，正在刷票...")
    else:
        time.sleep(1)
        print("{} 当前不在抢票时间，请等待".format(nowTime))
    

#预定确认页面验证码自动填写和提交
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
        windowsNotify(title='注意', message='抢到票了')
    elif system == "Darwin":
        # mac系统通知
        macNotify(title='注意', subtitle='注意', message='抢到票了')
except Exception as error:
    print(error)
finally:
    while 1==1:
        time.sleep(5)
        print('抢到票了')
