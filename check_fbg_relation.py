# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022/4/6 11:08
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : check_its_bill_detail.py
# @Software: PyCharm

import requests
from decimal import Decimal
from libs.yaml_config import global_yaml_config
from libs.conn_mysql import ConnMySql
from libs.thread_pool_manage import ThreadPoolManage
from libs.feishu_robot_notify import FeiShuRobotNotify as notify

RECEIVABLE_ESTIMATED_RELATION = 'fin_fbg_receivable_estimated_relation'
PAYABLE_ESTIMATED_RELATION = 'fin_fbg_payable_estimated_relation'
RECEIVABLE_CONFIRM_RELATION = 'fin_fbg_receivable_confirm_relation'
PAYABLE_CONFIRM_RELATION = 'fin_fbg_payable_confirm_relation'
INCOME_CONFIRM_RELATION = 'fin_fbg_income_confirm_relation'
COST_CONFIRM_RELATION = 'fin_fbg_cost_confirm_relation'

ES_COST_CONFIRM_RELATION = 'fbg_prod_es_cost_confirm_relation'
ES_INCOME_CONFIRM_RELATION = "fbg_prod_es_income_confirm_relation"
ES_PAYABLE_CONFIRM_RELATION = "fbg_prod_es_payable_confirm_relation"
ES_PAYABLE_ESTIMATED_RELATION = "fbg_prod_es_payable_estimated_relation"
ES_RECEIVABLE_CONFIRM_RELATION = "fbg_prod_es_receivable_confirm_relation"
ES_RECEIVABLE_ESTIMATED_RELATION = "fbg_prod_es_receivable_estimated_relation"


def call_action(conn, sql):
    db = ConnMySql(conn)
    return db.first(sql).get('row_count')


class CheckFbgRelation(object):
    """
    校验6大交易流水数据
    """

    def __init__(self):
        self.notify_content = ""
        self.config = global_yaml_config.get('FbgRelation')

    def exec(self):
        for x in range(1, 7):
            total_count = 0
            if x == 1:
                # 先统计确认冲销数据
                self._table_prefix = PAYABLE_CONFIRM_RELATION
                total_count = self.__do_threads_return_count(True)

                self._table_prefix = PAYABLE_ESTIMATED_RELATION
                self._es_index = ES_PAYABLE_ESTIMATED_RELATION
            elif x == 2:
                self._table_prefix = PAYABLE_CONFIRM_RELATION
                self._es_index = ES_PAYABLE_CONFIRM_RELATION
            elif x == 3:
                # 先统计确认冲销数据
                self._table_prefix = RECEIVABLE_CONFIRM_RELATION
                total_count = self.__do_threads_return_count(True)

                self._table_prefix = RECEIVABLE_ESTIMATED_RELATION
                self._es_index = ES_RECEIVABLE_ESTIMATED_RELATION
            elif x == 4:
                self._table_prefix = RECEIVABLE_CONFIRM_RELATION
                self._es_index = ES_RECEIVABLE_CONFIRM_RELATION
            elif x == 5:
                self._table_prefix = INCOME_CONFIRM_RELATION
                self._es_index = ES_INCOME_CONFIRM_RELATION
            elif x == 6:
                self._table_prefix = COST_CONFIRM_RELATION
                self._es_index = ES_COST_CONFIRM_RELATION
            else:
                break;

            total_count += self.__do_threads_return_count()
            self.notify_content += f"**MySql** (*{self._table_prefix}*)：{format(total_count, ',')}\n"
            self.__get_es_alias_count()
            self.notify_content += "\n"

        self._send()

    def __do_threads_return_count(self, write_off=False):
        total_count = 0
        threads = []
        databases = self.config.get('DataBases')
        for db in databases:
            thread = ThreadPoolManage(call_action, db, self.__get_select_sql(write_off))
            thread.start()
            threads.append(thread)

        for t in threads:
            t.join()
            total_count += Decimal(t.get_result())

        return total_count

    def __get_select_sql(self, write_off=False):
        sql_list = []
        for i in range(0, 65):
            sql = f"select count(*) row_count from {self._table_prefix}_{i}"
            # 是否销账
            if write_off:
                sql += " where origin_data_type=2"
            sql_list.append(sql)

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
        notify(global_yaml_config.get('Webhook')).card('【内部关联方】FBG交易流水', self.notify_content)
