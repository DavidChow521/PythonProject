# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022/5/13 9:45
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : tapd_spider_requests.py
# @Software: PyCharm
import copy
import random
import datetime
import time
import requests
from bs4 import BeautifulSoup
from chinese_calendar import is_workday
from libs.logger import logger
from libs.yaml_config import global_yaml_config


class TapdSpider():
    def __init__(self):
        self.now_datetime = datetime.datetime.now()
        # self.now_datetime = datetime.datetime.strptime('2022-05-26 18:00:00', "%Y-%m-%d %H:%M:%S")
        self.expires_time = datetime.datetime(year=self.now_datetime.year, month=self.now_datetime.month,
                                              day=self.now_datetime.day)
        self.config = global_yaml_config.get('TapdTask')
        self.am_range = [9, 10]
        self.pm_range = [18, 19, 20]

        # 是否在通知时间范围内 且 是工作日
        if (self.now_datetime.hour in self.am_range or self.now_datetime.hour in self.pm_range) and is_workday(
                self.now_datetime.date()):
            self.exec()
        pass

    def exec(self):
        for x in self.config:
            self.current_feishu_user_open_ids = x["user_open_ids"]
            self.current_cookies = x["tapd_cookie"]
            self.current_robot_token = x["feishu_robot_token"]
            self.current_not_task_users_dict = {}
            for id in x["tapd_projects"]:
                self.process_project(id)
                # 等待1s
                time.sleep(1)

            card_msg = self.get_not_task_message()
            if card_msg != None:
                # print(card_msg)
                self.send_copy(self.current_robot_token, card_msg)
        pass

    def process_project(self, project_id):
        task_list = []
        www_root = "https://www.tapd.cn/"
        # 获取第一页
        resp_html = self.get_prong_task_html(f"{www_root}/{project_id}/prong/tasks")
        task_list.extend(self.get_task_list(resp_html))
        # 获取第二页
        if self.current_project_page_next_url != None:
            resp_html = self.get_prong_task_html(f"{www_root}/{self.current_project_page_next_url}")
            task_list.extend(self.get_task_list(resp_html))
        if len(task_list) != 0:
            card_msg = self.get_project_message(task_list)
            if card_msg != None:
                # print(card_msg)
                self.send_copy(self.current_robot_token, card_msg)

        logger.info(f'执行【{self.current_project_name}】项目结束！')

    def get_project_message_template(self, href, title, iteration, iteration_href, status, hour, open_id, from_time,
                                     to_time):
        return {"extra": {"tag": "button", "text": {"content": "👉 去处理", "tag": "plain_text"}, "type": "primary",
                          "url": href}, "tag": "div",
                "text": {
                    "content": f"**{title}** \n🔹 迭代：[{iteration}]({iteration_href})\n🔔 状态：{status}\n⌚ 工时：{hour} 天\n🙊 处理人：<at id={open_id}></at>\n📅 预计时间：{from_time} 至 {to_time}",
                    "tag": "lark_md"}}

    def get_project_message(self, task_list):
        init_msg = {"msg_type": "interactive", "card": {"config": {"enable_forward": True}, "elements": [],
                                                        "header": {"template": "orange",
                                                                   "title": {
                                                                       "content": f"🏷️ {self.current_project_name}",
                                                                       "tag": "plain_text"}}}}
        card_msg = copy.deepcopy(init_msg)

        # 查找当天任务
        if self.now_datetime.hour in self.am_range:
            for u in self.current_feishu_user_open_ids:
                if not self.current_not_task_users_dict.get(u):
                    self.current_not_task_users_dict.update({u: False})
                if not self.current_not_task_users_dict[u]:
                    for x in task_list:
                        to_date_time = datetime.datetime.strptime(x["to_time"], "%Y-%m-%d")
                        if u == x["user"] and to_date_time >= self.expires_time:
                            self.current_not_task_users_dict.update({u: True})
                            break

        # 正常任务提醒
        for x in task_list:
            to_date_time = datetime.datetime.strptime(x["to_time"], "%Y-%m-%d")
            from_date_time = datetime.datetime.strptime(x["from_time"], "%Y-%m-%d")
            if (self.now_datetime.hour in self.pm_range and to_date_time == self.expires_time and
                x["status"] != "已完成") or (
                    self.now_datetime.hour in self.am_range and from_date_time == self.expires_time and
                    x["status"] == "未开始"):
                _extra = self.get_project_message_template(x["title_href"], x["title"], x["iteration"],
                                                           x["iteration_href"],
                                                           x["status"], x["working_hour"],
                                                           self.current_feishu_user_open_ids[x["user"]], x["from_time"],
                                                           x["to_time"])
                card_msg["card"]["elements"].append(_extra)
                if len(task_list) != task_list.index(x):
                    card_msg["card"]["elements"].append({"tag": "hr"})
        if init_msg == card_msg:
            return None

        card_msg["card"]["elements"].append(
            {"elements": [{"content": self.now_datetime.strftime('%Y-%m-%d %H:%M:%S'), "tag": "lark_md"}],
             "tag": "note"})

        return card_msg

    def get_not_task_message(self):
        not_task_users = ""
        for u in self.current_not_task_users_dict:
            not_task_users += "" if self.current_not_task_users_dict[
                                        u] == True else f"<at id={self.current_feishu_user_open_ids[u]}>{u}</at>"
        if not_task_users == "":
            return None

        card_msg = {"msg_type": "interactive", "card": {"config": {"enable_forward": True},
                                                        "header": {"template": "red",
                                                                   "title": {"content": f"👻️ 我的任务",
                                                                             "tag": "plain_text"}}}}
        card_msg["card"].update({"i18n_elements": {
            "zh_cn": [{"tag": "div", "text": {"content": f"发现你今日任务未创建。{not_task_users}", "tag": "lark_md"}},
                      {"actions": [
                          {"tag": "button", "text": {"content": "👉 去创建", "tag": "plain_text"}, "type": "danger",
                           "url": "https://www.tapd.cn/company/participant_projects"}], "tag": "action"}]}})

        return card_msg

    def get_task_list(self, resp_html):
        task_list = []
        soup = BeautifulSoup(resp_html, "lxml")
        self.current_project_name = soup.select_one(".project-name").text
        self.current_project_page_next_url = soup.select_one(".page-next").find('a').get('href')
        rows = soup.select("#task_table tbody tr")
        # wf(f"{self.current_project_name} - TAPD.html").create(resp_text)
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

            if self.current_feishu_user_open_ids.__contains__(user) and status != "已完成":
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

    def get_cookies(self):
        cookies = {}
        for line in self.current_cookies.split(';'):
            k, v = line.split('=', 1)
            cookies[k] = v
        return cookies;

    def get_random_ueragent(self):
        user_agents = [
            "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.14 (KHTML, like Gecko) Chrome/24.0.1292.0 Safari/537.14",
            "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36"
        ]
        return random.choice(user_agents)

    def send_feishu(self, token, data):
        resp = requests.post(f"https://open.feishu.cn/open-apis/bot/v2/hook/{token}", json=data,
                             proxies=self.get_proxies())
        return self.response_status(resp)

    # 抄送一份
    def send_copy(self, token, data):
        self.send_feishu(token, data)
        self.send_feishu(global_yaml_config.get('RobotToken'), data)

    def get_proxies(self):
        return {"http": None, "https": None}

    def response_status(self, resp):
        if resp.status_code != requests.codes.OK:
            logger.info(f'Status: {resp.status_code}, Url: {resp.url}')
            return False
        return True

    def get_prong_task_html(self, url):
        headers = {
            'User-Agent': self.get_random_ueragent()
        }
        resp = requests.get(url, headers=headers, cookies=self.get_cookies(), proxies=self.get_proxies())
        if self.response_status(resp):
            return resp.text
        return None


TapdSpider()
