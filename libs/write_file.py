# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022/4/12 15:35
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : write_file.py
# @Software: PyCharm

import os


class WriteFile(object):
    """
    写文件

    :param file_name：文件名.后缀名
    """

    def __init__(self, file_name):
        self.file_path = f"{os.getcwd()}\\{file_name}"

    def create(self, content):
        self._write_(content, 'w')

    def append(self, content):
        self._write_(content, 'a')

    def _write_(self, content, mode):
        with open(self.file_path, mode, encoding='utf-8') as f:
            f.write(content)
