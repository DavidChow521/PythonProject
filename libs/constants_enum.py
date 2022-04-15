# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022/4/15 13:54
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : constants_enum.py
# @Software: PyCharm

from enum import Enum


class Template(Enum):
    """
    飞书卡片标题配色
    """
    green = 0
    """
    完成/成功
    """
    orange = 1
    """
    警告/警示
    """
    red = 2
    """
    错误/异常
    """
    grey = 3
    """
    失效
    """
