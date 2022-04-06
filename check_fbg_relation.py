# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022/4/6 11:08
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : check_its_bill_detail.py
# @Software: PyCharm

import prettytable
import requests
from decimal import Decimal
from libs.yaml_config import global_yaml_config
from libs.conn_mysql import ConnMySql
from libs.thread_pool_manage import ThreadPoolManage

_RECEIVABLE_ESTIMATED_RELATION_ = 'fin_fbg_receivable_estimated_relation'
_PAYABLE_ESTIMATED_RELATION_ = 'fin_fbg_payable_estimated_relation'
_RECEIVABLE_CONFIRM_RELATION_ = 'fin_fbg_receivable_confirm_relation'
_PAYABLE_CONFIRM_RELATION_ = 'fin_fbg_payable_confirm_relation'
_INCOME_CONFIRM_RELATION_ = 'fin_fbg_income_confirm_relation'
_COST_CONFIRM_RELATION_ = 'fin_fbg_cost_confirm_relation'

_ES_COST_CONFIRM_RELATION_ = 'fbg_prod_es_cost_confirm_relation'
_ES_INCOME_CONFIRM_RELATION_ = "fbg_prod_es_income_confirm_relation"
_ES_PAYABLE_CONFIRM_RELATION_ = "fbg_prod_es_payable_confirm_relation"
_ES_PAYABLE_ESTIMATED_RELATION_ = "fbg_prod_es_payable_estimated_relation"
_ES_RECEIVABLE_CONFIRM_RELATION_ = "fbg_prod_es_receivable_confirm_relation"
_ES_RECEIVABLE_ESTIMATED_RELATION_ = "fbg_prod_es_receivable_estimated_relation"


def call_action(conn, sql):
    db = ConnMySql(conn)
    return db.first(sql).get('row_count')


pt = prettytable.PrettyTable()
pt.field_names = ["来 源", "交易流水", "数据量"]


class CheckFbgRelation(object):
    """
    校验6大交易流水数据
    """

    def __init__(self):
        self.config = global_yaml_config.get('FbgRelation')

    def exec(self):
        for x in range(1, 7):
            if x == 1:
                self._table_prefix = _PAYABLE_ESTIMATED_RELATION_
                self._es_index = _ES_PAYABLE_ESTIMATED_RELATION_
            elif x == 2:
                self._table_prefix = _PAYABLE_CONFIRM_RELATION_
                self._es_index = _ES_PAYABLE_CONFIRM_RELATION_
            elif x == 3:
                self._table_prefix = _RECEIVABLE_ESTIMATED_RELATION_
                self._es_index = _ES_RECEIVABLE_ESTIMATED_RELATION_
            elif x == 4:
                self._table_prefix = _RECEIVABLE_CONFIRM_RELATION_
                self._es_index = _ES_RECEIVABLE_CONFIRM_RELATION_
            elif x == 5:
                self._table_prefix = _INCOME_CONFIRM_RELATION_
                self._es_index = _ES_INCOME_CONFIRM_RELATION_
            elif x == 6:
                self._table_prefix = _COST_CONFIRM_RELATION_
                self._es_index = _ES_COST_CONFIRM_RELATION_
            else:
                break;

            self.__do_threads()
            pt.add_row(["数据库", self._table_prefix, self._total_count])
            self.__get_es_alias_count()
        print(pt)

    def __do_threads(self):
        self._total_count = 0
        databases = self.config.get('DataBases')
        threads = []
        for x in range(0, 3):
            db = databases[x]
            thread = ThreadPoolManage(call_action, db, self.__get_select_sql())
            thread.start()
            threads.append(thread)

        for t in threads:
            t.join()
            self._total_count += Decimal(t.get_result())

    def __get_select_sql(self):
        sql_list = []
        for i in range(0, 65):
            sql_list.append(f"select count(*) row_count from {self._table_prefix}_{i}")

        union_all_sql = " union all \n".join(sql_list)
        select_sql = f"""select sum(t.row_count) row_count from (
                {union_all_sql}
                )t"""

        return select_sql

    def __get_s(self,table_prefix):
        sql_list = []
        for i in range(0, 65):
            sql_list.append(f"select count(*) row_count from {table_prefix}_{i} where origin_data_type=2")

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
            pt.add_row(["Elasticsearch", self._es_index, count])
            return count
        return 0
