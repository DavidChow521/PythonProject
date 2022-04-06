# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022-04-01 18:29:27
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : check_its_bill_detail.py
# @Software: PyCharm

import datetime
from libs.conn_mysql import ConnMySql
from libs.yaml_config import global_yaml_config


class RepairItsReceivableApply(object):
    """
    修复历史收款申请单

    生成update sql 语句
    """

    def __init__(self):
        self.now_datetime = datetime.datetime.now()
        db = ConnMySql(global_yaml_config.get('DataBase'))
        data_list = db.query("select * from its_receivable_apply where create_time<='2022-04-10'")
        for data in data_list:
            payment_status = int(data.get('payment_status'))
            pay_status = 4 if payment_status == 2 else 5
            id = data.get('id')
            update_sql = "update its_receivable_apply set pay_type=1, update_time='{0}', pay_status={1} where id={2};".format(
                self.now_datetime, pay_status, id)
            print(update_sql)
