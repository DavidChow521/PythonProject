# # -*- coding:utf-8 -*-
from libs.selenium_login import Login
from libs.yaml_config import global_yaml_config

__DEF__ = {
    "url": "https://uat-fip.eminxing.com",
    "account": global_yaml_config.get('SSO').get('account'),
    "password": global_yaml_config.get('SSO').get('password'),
}

__FILTER__ = global_yaml_config.get('SSO').get('filter')


def callback(*args):
    # 自定义处理方法
    print('callback')


Login.process(__DEF__, __FILTER__, callback)












