
# # -*- coding:utf-8 -*-
from libs.selenium_login import Login
from libs.yaml_config import global_yaml_config

__DEF__ = {
    "url": global_yaml_config.get('Yapi').get('url'),
    "account": global_yaml_config.get('Yapi').get('account'),
    "password": global_yaml_config.get('Yapi').get('password'),
}

__FILTER__ = global_yaml_config.get('Yapi').get('filter')


def callback(driver):
    # 自定义处理方法
    driver.find_element_by_class_name('ant-radio-group').click()


Login.process(__DEF__, __FILTER__, callback)
