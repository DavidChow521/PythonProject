# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022-04-01 18:29:27
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : yaml_config.py
# @Software: PyCharm
import os
import yaml


class YamlConfig(object):
    def __init__(self, file='config.yaml'):
        # 获取yaml文件路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        yamlPath = os.path.join(base_dir, file)
        if not os.path.exists(yamlPath):
            raise FileNotFoundError("No such file: config.yaml")
        # open方法打开直接读出来
        f = open(yamlPath, 'r', encoding='utf-8')
        cfg = f.read()
        # 用load方法转字典
        self._congfig = yaml.load(cfg, Loader=yaml.CLoader)

    def get(self, name):
        return self._congfig.get(name)


global_yaml_config = YamlConfig()
