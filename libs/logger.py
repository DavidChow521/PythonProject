# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022-04-01 18:29:27
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : logger.py
# @Software: PyCharm
import logging
import logging.handlers

logger = logging.getLogger()


class Logger(object):
    def __init__(self, file='appliction.log'):
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(levelname)s - %(asctime)s - %(pathname)s[line:%(lineno)d] - %(process)d-%(threadName)s ↴\n%(message)s \n')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        file_handler = logging.handlers.RotatingFileHandler(
            file, maxBytes=10485760, backupCount=15, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


Logger()
