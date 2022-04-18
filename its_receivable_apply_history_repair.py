# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022-04-01 18:29:27
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : its_receivable_apply_history_repair.py
# @Software: PyCharm

import datetime
from libs.conn_mysql import ConnMySql
from libs.yaml_config import global_yaml_config
from libs.write_file import WriteFile as wf


class ItsReceivableApplyHistoryRepair(object):
    """
    修复历史收款申请单

    生成update sql 语句
    """

    def __init__(self):
        self.now_datetime = datetime.datetime.now()
        db = ConnMySql(global_yaml_config.get('DataBase'))
        data_list = db.query(
            "select ira.*,ipa.submit_code as payable_submit_code from its_receivable_apply ira,its_payable_apply ipa where ira.payable_apply_code=ipa.apply_code;")
        update_sql = ""
        for data in data_list:
            payment_status = int(data.get('payment_status'))
            pay_status = 4 if payment_status == 2 else 5
            id = data.get('id')
            payable_submit_code = data.get('payable_submit_code')
            update_sql += "update its_receivable_apply set pay_type=1, update_time='{0}', pay_status={1}, pay_postscript='{2}' where id={3};\n".format(
                self.now_datetime, pay_status, payable_submit_code, id)
            wf('V3.8.0-修复历史收款申请.sql').create(update_sql)
