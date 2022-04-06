# # -*- coding:utf-8 -*-
from selenium import webdriver
import time


class Login(object):

    def process(__DEF__, __FILTER__, func):

        driver = webdriver.Chrome()
        driver.maximize_window()
        # 等待10s
        driver.implicitly_wait(10)

        # 如果不是安装的浏览器，需要设置地址
        # options = webdriver.ChromeOptions()
        # options.binary_location = "E:\Chrome\Application\chrome.exe"
        # driver = webdriver.Chrome(chrome_options = options)

        driver.get(__DEF__.get("url"))
        time.sleep(1)

        element = "driver.find_element_by_"
        element_event = ""
        element_login = ""
        isLogin = False

        # 回调处理特殊情况
        func(driver)

        for item in __FILTER__:
            for textbox in __FILTER__.get(item):
                if item == "login":
                    if (
                            textbox == "id" or textbox == "class_name" or textbox == "name" or textbox == "tag_name" or textbox == "css_selector" or textbox == "xpath"):
                        element_login = element + textbox + \
                                        '(__FILTER__.get("' + item + '").get("' + textbox + '"))'
                    elif textbox == "event":
                        element_event = "." + \
                                        __FILTER__.get(item).get(textbox) + "()"
                    else:
                        pass
                elif item == "captcha":
                    isLogin = __FILTER__.get(item).get(textbox)
                else:
                    if (
                            textbox == "id" or textbox == "class_name" or textbox == "name" or textbox == "tag_name" or textbox == "css_selector" or textbox == "xpath"):
                        time.sleep(2)
                        eval(element + textbox + '(__FILTER__.get("' + item + '").get("' +
                             textbox + '")).send_keys(__DEF__.get("' + item + '"))')

        if isLogin == 0:
            eval(element_login + element_event)

        input('Press Ctrl+C to exit.')
