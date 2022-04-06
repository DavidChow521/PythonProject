# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022-04-01 18:29:27
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : ini_config.py
# @Software: PyCharm
import os
import configparser


class IniConfig(object):
    def __init__(self, file='config.ini'):
        curPath = os.path.join(os.getcwd(), file)
        if not os.path.exists(curPath):
            raise FileNotFoundError("No such file: config.ini")
        self._config = configparser.ConfigParser()
        self._config.read(self._path, encoding='utf-8-sig')
        self._configRaw = configparser.RawConfigParser()
        self._configRaw.read(self._path, encoding='utf-8-sig')

    def get(self, section, name):
        return self._config.get(section, name)

    def getRaw(self, section, name):
        return self._configRaw.get(section, name)


global_ini_config = IniConfig()
