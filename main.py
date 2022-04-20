# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022/4/6 14:02
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : main.py
# @Software: PyCharm

from its_receivable_apply_history_repair import ItsReceivableApplyHistoryRepair
from check_its_bill_detail import CheckItsBillDetail
from check_fbg_relation import CheckFbgRelation
from check_lbg_relation import CheckLbgRelation

if __name__ == '__main__':
    ItsReceivableApplyHistoryRepair()
    # CheckFbgRelation().exec()
    # CheckItsBillDetail().exec()
    # CheckLbgRelation().exec()
