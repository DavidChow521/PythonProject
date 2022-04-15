# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022/4/15 14:22
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : feishu_robot_notify.py
# @Software: PyCharm

import datetime
import requests
from libs.constants_enum import Template


class FeiShuRobotNotify(object):
    """
    飞书机器人通知
    """

    def __init__(self, url):
        self.now_datetime = datetime.datetime.now()
        self._url = url
        pass

    def card(self, title, content, email=None, is_at_all=False, template=Template.orange):
        """

        :param title: 标题
        :param content: 内容 支持markdown
        :param email: @指定人邮箱
        :param is_at_all: 是否@所有人
        :param template: 标题模板色
        :return:
        """
        if is_at_all == True:
            content += "<at id=all></at>"
        if email != None and is_at_all == False:
            content += f"<at email={email}></at>"
        data = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "enable_forward": True
                },
                "header": {
                    "template": template.name,
                    "title": {
                        "content": title,
                        "tag": "plain_text"
                    }
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": content,
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "elements": [
                            {
                                "content": self.now_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                                "tag": "lark_md"
                            }
                        ],
                        "tag": "note"
                    }
                ]
            }
        }
        proxies = {"http": None, "https": None}
        resp = requests.post(self._url, json=data, proxies=proxies)
        if resp.status_code == 200:
            return True
        return False
