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
    https://open.feishu.cn/document/ukTMukTMukTM/uADOwUjLwgDM14CM4ATN
    https://open.feishu.cn/tool/cardbuilder?from=howtoguide
    """

    def __init__(self, url):
        self.now_datetime = datetime.datetime.now()
        self._url = url
        self._card_content = {"msg_type": "interactive", "card": {"config": {"enable_forward": True}, "elements": []}}
        pass

    def card(self, title, content=None, fields=None, openid=None, is_at_all=False, template=Template.orange):
        """
        :param title: 标题
        :param content: 内容 支持markdown
        :param fields: 字段 支持markdown
        :param openid: @指定人openid
        :param is_at_all: 是否@所有人
        :param template: 标题模板色
        :return:
        """
        data = self._card_content
        data["card"].update({"header": {"template": template.name, "title": {"content": title, "tag": "plain_text"}}})

        # 字段
        if fields != None:
            data["card"]["elements"].append(fields)

        # 内容
        if content != None:
            if is_at_all == True:
                content += "<at id=all></at>"
            if openid != None and is_at_all == False:
                content += f"<at id={openid}></at>"
            data["card"]["elements"].append({"tag": "div", "text": {"content": content, "tag": "lark_md"}})

        # 以下追加至最后
        data["card"]["elements"].append({"tag": "hr"})
        data["card"]["elements"].append(
            {"elements": [{"content": self.now_datetime.strftime('%Y-%m-%d %H:%M:%S'), "tag": "lark_md"}],
             "tag": "note"})

        # print(data)
        self._send(data)

    def _send(self, data):
        proxies = {"http": None, "https": None}
        resp = requests.post(self._url, json=data, proxies=proxies)
        if resp.status_code == 200:
            return True
        return False
