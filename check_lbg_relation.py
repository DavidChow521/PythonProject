# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022/4/20 14:14
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : check_lbg_relation.py
# @Software: PyCharm

import requests
from libs.yaml_config import global_yaml_config
from libs.feishu_robot_notify import FeiShuRobotNotify as notify
from libs.thread_pool_manage import ThreadPoolManage
from libs.conn_mysql import ConnMySql
from decimal import Decimal

PAYABLE_CONFIRM = "fin_payable_confirm_lbg"
PAYABLE_ESTIMATED = "fin_payable_estimated_lbg"
RECEIVABLE_CONFIRM = "fin_receivables_confirm_lbg"
RECEIVABLE_ESTIMATED = "fin_receivables_estimated_lbg"

ES_PAYABLE_CONFIRM = "lbg_prod_es_payable_confirm_v2"
ES_PAYABLE_ESTIMATED = "lbg_prod_es_payable_estimated_v2"
ES_RECEIVABLE_CONFIRM = "lbg_prod_es_receivables_confirm_v2"
ES_RECEIVABLE_ESTIMATED = "lbg_prod_es_receivables_estimated_v2"


def call_action(conn, sql):
    db = ConnMySql(conn)
    return db.first(sql).get('row_count')


class CheckLbgRelation(object):
    """
    校验4大交易流水数据
    """

    def __init__(self):
        self.notify_content = ""
        self.config = global_yaml_config.get('LbgRelation')

    def exec(self):
        for x in range(1, 5):
            if x == 1:
                self._table_prefix = PAYABLE_CONFIRM
                self._es_index = ES_PAYABLE_CONFIRM
            elif x == 2:
                self._table_prefix = PAYABLE_ESTIMATED
                self._es_index = ES_PAYABLE_ESTIMATED
            elif x == 3:
                self._table_prefix = RECEIVABLE_CONFIRM
                self._es_index = ES_RECEIVABLE_CONFIRM
            elif x == 4:
                self._table_prefix = RECEIVABLE_ESTIMATED
                self._es_index = ES_RECEIVABLE_ESTIMATED
            else:
                break;
            self.__do_instance()
        self._send()

    def __do_instance(self):
        self._total_count = 0
        databases = self.config.get('DataBases')
        for database in databases:
            self.__do_threads(database)

        self.notify_content += f"**MySql** (*{self._table_prefix}*)：{format(self._total_count, ',')}\n"
        self.__get_es_alias_count()
        self.notify_content += "\n"

    def __do_threads(self, database):
        threads = []
        for db in database.get('databases'):
            thread = ThreadPoolManage(call_action, {
                'host': database.get('host'),
                'port': database.get('port'),
                'user': database.get('user'),
                'password': database.get('password'),
                'database': db

            }, self.__get_select_sql())
            thread.start()
            threads.append(thread)

        for t in threads:
            t.join()
            self._total_count += Decimal(t.get_result())

    def __get_select_sql(self):
        sql_list = []
        for i in range(0, 271):
            sql_list.append(f"select count(*) row_count from {self._table_prefix}_{i}")

        union_all_sql = " union all \n".join(sql_list)
        select_sql = f"""select sum(t.row_count) row_count from (
                {union_all_sql}
                )t"""

        return select_sql

    def __get_es_alias_count(self):
        resp = requests.api.get(
            '{0}/{1}/_count'.format(global_yaml_config.get("EsBaseUrl"), self._es_index))
        if resp.status_code == 200:
            count = resp.json().get('count')
            self.notify_content += f"**Elasticsearch** (*{self._es_index}*) ：{format(count, ',')}\n"
            return count
        return 0

    def _send(self):
        notify(global_yaml_config.get('Webhook')).card('【内部关联方】LBG交易流水', self.notify_content)
