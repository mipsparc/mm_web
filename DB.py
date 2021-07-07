#coding: utf-8

import sqlite3
import israspi

class DB:
    if israspi.is_raspi:
        dbfile = '/mnt/database/multimascon.sqlite3'
    else:
        dbfile = 'multimascon.sqlite3'
    
