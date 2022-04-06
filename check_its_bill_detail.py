# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022/4/2 11:08
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : check_its_bill_detail.py
# @Software: PyCharm

import datetime
import prettytable
import requests
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from libs.thread_pool_manage import ThreadPoolManage
from libs.conn_mysql import ConnMySql
from libs.yaml_config import global_yaml_config

_DB_PREFIX_ = 'its_settlement'
_PAYABLE_BILL_DETAIL_PREFIX_ = 'its_payable_bill_detail'
_RECEIVABLE_BILL_DETAIL_PREFIX_ = 'its_receivable_bill_detail'

_ES_PAYABLE_BILL_DETAIL_INDEX_ = 'its_prod_es_payable_bill'
_ES_RECEIVABLE_BILL_DETAIL_INDEX_ = 'its_prod_es_receivable_bill'


def call_action(conn, sql):
    db = ConnMySql(conn)
    return db.first(sql).get('row_count')


pt = prettytable.PrettyTable()
pt.field_names = ["来 源", "交易流水", "数据量"]


class CheckItsBillDetail(object):
    """
    校验应付账单、应收账单明细数据量

    """

    def __init__(self):
        self.config = global_yaml_config.get("ItsRelation")
        self.now_datetime = datetime.datetime.now()
        self.end_time = datetime.datetime(year=self.now_datetime.year, month=self.now_datetime.month, day=1)

    def exec(self):
        for x in range(1, 3):
            if x == 1:
                self._table_prefix = _PAYABLE_BILL_DETAIL_PREFIX_
                self._es_index = _ES_PAYABLE_BILL_DETAIL_INDEX_
            else:
                self._table_prefix = _RECEIVABLE_BILL_DETAIL_PREFIX_
                self._es_index = _ES_RECEIVABLE_BILL_DETAIL_INDEX_

            self.__do_instance()

        print(pt)

    def __do_instance(self):
        self._total_count = 0
        databases = self.config.get('DataBases')
        for db in databases:
            self.__do_threads(db)

        pt.add_row(["数据库", self._table_prefix, self._total_count])
        self.__get_es_alias_count()

    def __do_threads(self, db):
        threads = []
        self._start_time = datetime.datetime.strptime('2021-07-01', "%Y-%m-%d")
        while (self._start_time <= self.end_time):
            self._account_time = self._start_time.strftime("%Y%m")

            thread = ThreadPoolManage(call_action, db, self.__get_select_sql())
            thread.start()
            threads.append(thread)
            self._start_time = self._start_time + relativedelta(months=+1)

        for t in threads:
            t.join()
            self._total_count += Decimal(t.get_result())

    def __get_select_sql(self):
        sql_list = []
        for i in range(0, 32):
            sql_list.append(
                f"select count(*) row_count from {_DB_PREFIX_}_{self._account_time}.{self._table_prefix}_{i}")

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
