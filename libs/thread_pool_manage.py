# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022/4/2 11:08
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : thread_pool_manage.py
# @Software: PyCharm

from threading import Thread

class ThreadPoolManage(Thread):
    """
    多线程

    :return result
    """
    def __init__(self, func, *args):
        super(ThreadPoolManage, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        """
        获取函数返回值
        """
        try:
            return self.result  # 如果子线程不使用join方法，此处可能会报没有self.result的错误
        except Exception:
            return None
