# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2022-04-01 18:29:27
# @Author : zhoutao
# @Email : zt13415@ztn.com
# @File : conn_mysql.py
# @Software: PyCharm
import pymysql


class ConnMySql(object):
    def __init__(self, options):
        # 建立连接
        self.__conn = pymysql.connect(
            host=options.get('host'),  # 主机地址，若是自己的主机也可以用'localhost'
            port=options.get('port'),  # 端口
            user=options.get('user'),  # 用户
            password=options.get('password'),  # 密码
            database=options.get('database'),  # 数据库
            charset='utf8',  # 设置编码
        )
        # 创建一个游标
        self.__cur = self.__conn.cursor(pymysql.cursors.DictCursor)

    def close(self):
        if self.__conn and self.__cur:
            # 关闭游标
            self.__conn.commit()
            self.__cur.close()
            # 断开连接
            self.__conn.close()

    def query(self, sql, *args):
        self.__cur.execute(sql, args)
        return self.__cur.fetchall()

    def first(self, sql, *args):
        self.__cur.execute(sql, args)
        return self.__cur.fetchone()

    def delete(self, sql, *args):
        try:
            num = self.__cur.execute(sql, args)
            self.__conn.commit()
            return num
        except pymysql.Error as e:
            self.__conn.rollback()
            raise pymysql.Error(e)
        finally:
            self.close()

    def insert(self, sql, *args):
        try:
            self.__cur.execute(sql, args)
            Id = self.__cur.lastrowid
            self.__conn.commit()
            return Id
        except pymysql.Error as e:
            self.__conn.rollback()
            raise pymysql.Error(e)
        finally:
            self.close()

    def update(self, sql, *args):
        try:
            self.__cur.execute(sql, args)
            self.__conn.commit()
        except pymysql.Error as e:
            self.__conn.rollback()
            raise pymysql.Error(e)
        finally:
            self.close()
