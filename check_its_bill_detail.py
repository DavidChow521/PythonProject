# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022/4/2 11:08
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : check_its_bill_detail.py
# @Software: PyCharm

import datetime
import requests
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from libs.thread_pool_manage import ThreadPoolManage
from libs.conn_mysql import ConnMySql
from libs.yaml_config import global_yaml_config
from libs.feishu_robot_notify import FeiShuRobotNotify as notify

DB_PREFIX = 'its_settlement'
PAYABLE_BILL_DETAIL_PREFIX = 'its_payable_bill_detail'
RECEIVABLE_BILL_DETAIL_PREFIX = 'its_receivable_bill_detail'

ES_PAYABLE_BILL_DETAIL_INDEX = 'its_prod_es_payable_bill'
ES_RECEIVABLE_BILL_DETAIL_INDEX = 'its_prod_es_receivable_bill'


def call_action(conn, sql):
    db = ConnMySql(conn)
    return db.first(sql).get('row_count')


class CheckItsBillDetail(object):
    """
    校验应付账单、应收账单明细数据量
    """

    def __init__(self):
        self.notify_content = ""
        self.config = global_yaml_config.get("ItsRelation")
        self.now_datetime = datetime.datetime.now()
        self.end_time = datetime.datetime(year=self.now_datetime.year, month=self.now_datetime.month, day=1)

    def exec(self):
        for x in range(1, 3):
            if x == 1:
                self._table_prefix = PAYABLE_BILL_DETAIL_PREFIX
                self._es_index = ES_PAYABLE_BILL_DETAIL_INDEX
            else:
                self._table_prefix = RECEIVABLE_BILL_DETAIL_PREFIX
                self._es_index = ES_RECEIVABLE_BILL_DETAIL_INDEX

            self.__do_instance()

        self._send()

    def __do_instance(self):
        self._total_count = 0
        databases = self.config.get('DataBases')
        for db in databases:
            self.__do_threads(db)

        self.notify_content += f"**MySql** (*{self._table_prefix}*)：{format(self._total_count, ',')}\n"
        self.__get_es_alias_count()
        self.notify_content += "\n"

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
                f"select count(*) row_count from {DB_PREFIX}_{self._account_time}.{self._table_prefix}_{i}")

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
        notify(global_yaml_config.get('Webhook')).card('【内部关联方】结算账单明细', self.notify_content)
