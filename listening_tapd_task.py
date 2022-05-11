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
from libs.yaml_config import global_yaml_config
from libs.logger import logger
from libs.write_file import WriteFile as wf


class ListeningTapdTask():
    def __init__(self):
        self.now_datetime = datetime.datetime.now()
        # self.now_datetime = datetime.datetime.strptime('2022-05-19 18:00:00', "%Y-%m-%d %H:%M:%S")
        self.expires_time = datetime.datetime(year=self.now_datetime.year, month=self.now_datetime.month,
                                              day=self.now_datetime.day)
        self.config = global_yaml_config.get('TapdTask')
        self.execute()

    def execute(self):
        # 是否工作日
        if is_workday(self.now_datetime.date()):
            for x in self.config:
                self._feishu_user_open_ids = x["user_open_ids"]
                self._cookies = x["tapd_cookie"]
                self._robot_url = x["feishu_robot_url"]
                self._not_task_users_dict = {}
                for project in x["tapd_projects"]:
                    self._project_id = project
                    resp = requests.get(f'https://www.tapd.cn/{self._project_id}/prong/tasks',
                                        headers=self._get_headers(),
                                        cookies=self._get_cookies(),
                                        proxies=self._get_proxies())
                    task_list = self._get_task_list(resp.text)
                    if len(task_list) != 0:
                        card_msg = self._get_normal_message(task_list)
                        if card_msg != None:
                            # print(card_msg)
                            self._send(card_msg)

                    logger.info(f'执行【{self._project_name}】项目结束！')

                card_msg = self._get_not_task_message()
                if card_msg != None:
                    # print(card_msg)
                    self._send(card_msg)

    def _get_task_list(self, resp_text):
        task_list = []
        soup = BeautifulSoup(resp_text, "lxml")
        self._project_name = soup.select_one(".project-name").text
        rows = soup.select("#task_table tbody tr")
        # wf(f"{self._project_name} - TAPD.html").create(resp_text)
        for row in rows[1:]:
            title = row.select('td')[3].find('a').text
            title_href = row.select('td')[3].find('a').get('href')
            iteration = row.select('td')[5].find('a').text
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

    def _get_normal_template(self, href, title, iteration, iteration_href, status, hour, open_id, from_time, to_time):
        return {"extra": {"tag": "button", "text": {"content": "👉 去处理", "tag": "plain_text"}, "type": "primary",
                          "url": href}, "tag": "div",
                "text": {
                    "content": f"**{title}** \n🔹 迭代：[{iteration}]({iteration_href})\n🔔 状态：{status}\n⌚ 工时：{hour} 天\n🙊 处理人：<at id={open_id}></at>\n📅 预计时间：{from_time} 至 {to_time}",
                    "tag": "lark_md"}}

    def _get_normal_message(self, task_list):
        _init_msg = {"msg_type": "interactive", "card": {"config": {"enable_forward": True}, "elements": [],
                                                         "header": {"template": "orange",
                                                                    "title": {"content": f"🏷️ {self._project_name}",
                                                                              "tag": "plain_text"}}}}
        card_msg = {"msg_type": "interactive", "card": {"config": {"enable_forward": True}, "elements": [],
                                                        "header": {"template": "orange",
                                                                   "title": {"content": f"🏷️ {self._project_name}",
                                                                             "tag": "plain_text"}}}}
        # 查找当天任务 9,10
        if self.now_datetime.hour >= 9 and self.now_datetime.hour <= 10:
            for u in self._feishu_user_open_ids:
                if not self._not_task_users_dict.get(u):
                    self._not_task_users_dict.update({u: False})
                if not self._not_task_users_dict[u]:
                    for x in task_list:
                        to_date_time = datetime.datetime.strptime(x["to_time"], "%Y-%m-%d")
                        if u == x["user"] and to_date_time >= self.expires_time:
                            self._not_task_users_dict.update({u: True})
                            break

        # 正常任务提醒 设置时段 18,19,20
        for x in task_list:
            to_date_time = datetime.datetime.strptime(x["to_time"], "%Y-%m-%d")
            from_date_time = datetime.datetime.strptime(x["from_time"], "%Y-%m-%d")
            if (self.now_datetime.hour >= 18 and self.now_datetime.hour <= 20 and to_date_time == self.expires_time and
                x["status"] != "已完成") or (
                    self.now_datetime.hour >= 9 and self.now_datetime.hour <= 10 and from_date_time == self.expires_time and
                    x["status"] == "未开始"):
                _extra = self._get_normal_template(x["title_href"], x["title"], x["iteration"], x["iteration_href"],
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

    def _get_not_task_users_template(self):
        at_users = ""
        for u in self._not_task_users_dict:
            if not self._not_task_users_dict[u]:
                at_users += f"<at id={self._feishu_user_open_ids[u]}>{u}</at>"
        if at_users=="":
            return None
        return {"i18n_elements":{"zh_cn":[{"tag":"div","text":{"content":f"发现你今日任务未创建。{at_users}","tag":"lark_md"}},{"actions":[{"tag":"button","text":{"content":"👉 去创建","tag":"plain_text"},"type":"danger","url":"https://www.tapd.cn/company/participant_projects"}],"tag":"action"}]}}

    def _get_not_task_message(self):
        _init_msg = {"msg_type": "interactive", "card": {"config": {"enable_forward": True},
                                                         "header": {"template": "red",
                                                                    "title": {"content": f"👻️ 我的任务",
                                                                              "tag": "plain_text"}}}}
        card_msg = {"msg_type": "interactive", "card": {"config": {"enable_forward": True},
                                                        "header": {"template": "red",
                                                                   "title": {"content": f"👻️ 我的任务",
                                                                             "tag": "plain_text"}}}}
        _i18n_elements=self._get_not_task_users_template()
        if _i18n_elements != None:
            card_msg["card"].update(_i18n_elements)

        if _init_msg == card_msg:
            return None

        return card_msg

    def _send(self, data):
        resp = requests.post(self._robot_url, json=data, proxies=self._get_proxies())
        if resp.status_code == 200:
            return True
        return False

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


ListeningTapdTask()
