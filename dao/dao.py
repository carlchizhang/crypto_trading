import sqlite3
import logging

from .consts import DB_NAME
from utils import get_data_path

class DAO(object):
    """ DAO is the database access object for sqlite3 """

    def __init__(self, database=DB_NAME):
        self._conn = sqlite3.connect(get_data_path(DB_NAME))

    def bulk_insert_raw_orderbook(self, columns):
        cursor = self._conn.cursor()
        cursor.executemany("INSERT INTO raw_orderbook (pair, price, volume, is_ask, order_epoch, snapshot_epoch) VALUES (?, ?, ?, ?, ?, ?)", columns)
        self._conn.commit()