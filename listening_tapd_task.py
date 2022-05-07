# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022/4/27 13:59
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : listening_tapd_task.py
# @Software: PyCharm

import datetime
import requests
from bs4 import BeautifulSoup
from chinese_calendar import is_workday

global_config = [

]


class ListeningTapdTask():
    def __init__(self):
        self.now_datetime = datetime.datetime.now()

        # 是否工作日
        if is_workday(self.now_datetime.date()):
            for x in global_config:
                self._cookies = x["tapd_cookie"]
                self._feishu_user_open_ids = x["feishu_user_open_id"]
                self._robot_url = x["feishu_robot_url"]
                for project_id in x["tapd_project_id"]:
                    self._project_id = project_id
                    resp = requests.get(f'https://www.tapd.cn/{project_id}/prong/tasks', headers=self._get_headers(),
                                        cookies=self._get_cookies(),
                                        proxies=self._get_proxies())
                    self.execute(resp)

    def _get_proxies(self):
        return {"http": None, "https": None}

    def _get_headers(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.3319.102 Safari/537.36'
        }

    def _get_cookies(self):
        cookies = {}
        for line in self._cookies.split(';'):
            k, v = line.split('=', 1)
            cookies[k] = v
        return cookies;

    def _get_template(self, href, title, iteration, iteration_href, status, hour, open_id, from_time, to_time):
        return {"extra": {"tag": "button", "text": {"content": "👉 去处理", "tag": "plain_text"}, "type": "primary",
                          "url": href}, "tag": "div",
                "text": {
                    "content": f"**{title}** \n🔹 迭代：[{iteration}]({iteration_href})\n🔔 状态：{status}\n⌚ 工时：{hour} 天\n🙈 处理人：<at id={open_id}></at>\n📅 预计时间：{from_time} 至 {to_time}",
                    "tag": "lark_md"}}

    def _get_add_task_template(self, from_time, to_time, open_id):
        return {"extra": {"tag": "button", "text": {"content": "👉 去处理", "tag": "plain_text"}, "type": "danger",
                          "url": f"https://www.tapd.cn/{self._project_id}/prong/tasks/add"}, "tag": "div",
                "text": {"content": f"**⚠ 未找到今日任务** \n📅 预计时间：{from_time} 至 {to_time}\n🙈 处理人：<at id={open_id}></at>",
                         "tag": "lark_md"}}

    def execute(self, resp):
        task_list = self._get_task_list(resp.content)
        if len(task_list) != 0:
            card_msg = self._get_message(task_list)
            if card_msg != None:
                # print(card_msg)
                self._send(card_msg)
        print('执行结束！')

    def _get_task_list(self, html_content):
        task_list = []
        soup = BeautifulSoup(html_content, "lxml")
        self._project_name = soup.select_one(".project-name").text
        rows = soup.select("#task_table tbody tr")
        for row in rows[1:]:
            title = row.select('td')[2].get('title')
            title_href = row.select('td')[2].find('a').get('href')
            iteration = row.select('td')[5].find('a').get('title')
            iteration_href = row.select('td')[5].find('a').get('href')
            status = row.select('td')[6].find('a').get('title')
            user = row.select('td')[8].find('span').get('tapd_title')
            from_time = row.select('td')[9].get('title')
            to_time = row.select('td')[10].get('title')
            working_hour = row.select('td')[11].get('title')

            if self._feishu_user_open_ids.__contains__(user):
                task_list.append({
                    "title": title,
                    "title_href": title_href,
                    "iteration": iteration,
                    "iteration_href": iteration_href,
                    "status": status,
                    "user": user,
                    "from_time": from_time,
                    "to_time": to_time,
                    "working_hour": working_hour
                })

        return task_list

    def _get_message(self, task_list):
        _init_msg = {"msg_type": "interactive", "card": {"config": {"enable_forward": True}, "elements": [],
                                                         "header": {"template": "orange",
                                                                    "title": {"content": self._project_name,
                                                                              "tag": "plain_text"}}}}
        card_msg = {"msg_type": "interactive", "card": {"config": {"enable_forward": True}, "elements": [],
                                                        "header": {"template": "orange",
                                                                   "title": {"content": self._project_name,
                                                                             "tag": "plain_text"}}}}
        expires_time = datetime.datetime(year=self.now_datetime.year, month=self.now_datetime.month,
                                         day=self.now_datetime.day)
        # 查找当天任务 9,10
        if self.now_datetime.hour >= 9 and self.now_datetime.hour <= 10:
            for u in self._feishu_user_open_ids:
                is_exists = False
                for x in task_list:
                    to_date_time = datetime.datetime.strptime(x["to_time"], "%Y-%m-%d")
                    if u == x["user"] and to_date_time >= expires_time:
                        is_exists = True
                        break

                if is_exists == False:
                    _extra = self._get_add_task_template(expires_time.strftime("%Y-%m-%d"),
                                                         expires_time.strftime("%Y-%m-%d"),
                                                         self._feishu_user_open_ids[u])
                    card_msg["card"]["elements"].append(_extra)
                    if len(task_list) != 0:
                        card_msg["card"]["elements"].append({"tag": "hr"})

        # 正常任务提醒 设置时段 18,19,20
        for x in task_list:
            to_date_time = datetime.datetime.strptime(x["to_time"], "%Y-%m-%d")
            from_date_time = datetime.datetime.strptime(x["from_time"], "%Y-%m-%d")
            if (self.now_datetime.hour >= 18 and self.now_datetime.hour <= 20 and to_date_time == expires_time and x[
                "status"] != "已完成") or (
                    self.now_datetime.hour >= 9 and self.now_datetime.hour <= 10 and from_date_time == expires_time and
                    x["status"] == "未开始"):
                _extra = self._get_template(x["title_href"], x["title"], x["iteration"], x["iteration_href"],
                                            x["status"], x["working_hour"],
                                            self._feishu_user_open_ids[x["user"]], x["from_time"], x["to_time"])
                card_msg["card"]["elements"].append(_extra)
                if len(task_list) != task_list.index(x):
                    card_msg["card"]["elements"].append({"tag": "hr"})

        if _init_msg == card_msg:
            return None

        card_msg["card"]["elements"].append(
            {"elements": [{"content": self.now_datetime.strftime('%Y-%m-%d %H:%M:%S'), "tag": "lark_md"}],
             "tag": "note"})

        return card_msg

    def _send(self, data):
        resp = requests.post(self._robot_url, json=data, proxies=self._get_proxies())
        if resp.status_code == 200:
            return True
        return False


ListeningTapdTask()
