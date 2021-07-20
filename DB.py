#coding: utf-8

import sqlite3
import israspi

class DB:
    if israspi.is_raspi:
        dbfile = '/mnt/database/multimascon.sqlite3'
    else:
        dbfile = 'multimascon.sqlite3'
        
    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    @classmethod
    def getAllMasconPos(self):
        con = sqlite3.connect(self.dbfile)
        con.row_factory = self.dict_factory
        cur = con.cursor()
        cur.execute('''
            SELECT id, loco_id, mascon_pos
            FROM mascon_assign
            ORDER BY loco_id ASC
        ''', ())
        mascon_assigns = cur.fetchall()
        con.close()
        
        return mascon_assigns
    
    # 単に削除する
    @classmethod
    def deleteMasconPos(self, mascon_assign_id):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            DELETE FROM mascon_assign
            WHERE id = ?
        ''', (mascon_assign_id,))
        con.commit()
        con.close()
    
    # 新規追加としてレコードを追加する。mascon_posが重複する場合はloco_idで上書きする
    @classmethod
    def upsertMasconPos(self, loco_id, mascon_pos):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            INSERT INTO mascon_assign
            (loco_id, mascon_pos)
            VALUES (?, ?)
            ON CONFLICT (mascon_pos)
            DO UPDATE
            SET loco_id = excluded.loco_id
        ''', (loco_id, mascon_pos))
        con.commit()
        con.close()
    
    # すでにあるレコードを編集する場合。mascon_posが重複する場合は受け付けない
    @classmethod
    def updateMasconPos(self, mascon_assign_id, loco_id, mascon_pos):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            UPDATE OR IGNORE mascon_assign
            SET loco_id = ?, mascon_pos = ?
            WHERE id = ?
        ''', (loco_id, mascon_pos, mascon_assign_id))
        con.commit()
        con.close()
        
    # あらかじめmascon_assign_idをみて新規かどうかを判定する
    @classmethod
    def isMasconAssignIdExist(self, mascon_assign_id):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            SELECT id
            FROM mascon_assign
            WHERE id = ?
        ''', (mascon_assign_id, ))
        existence = bool(cur.fetchone())
        con.close()
        
        return existence
    
    @classmethod
    def getAllLocos(self):
        con = sqlite3.connect(self.dbfile)
        con.row_factory = self.dict_factory
        cur = con.cursor()
        cur.execute('''
            SELECT loco_id, address, accel_curve_group_id, speed_curve_group_id, base_level, light_func_id, nickname, brake_ratio
            FROM loco
            ORDER BY address ASC
        ''', ())
        locos = cur.fetchall()
        con.close()
        
        return locos
    
    @classmethod
    def deleteLoco(self, loco_id):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            DELETE FROM loco
            WHERE loco_id = ?
        ''', (loco_id, ))
        con.commit()
        con.close()
    
    @classmethod
    def insertLoco(self, address, accel_curve_group_id, speed_curve_group_id, base_level, light_func_id, nickname, brake_ratio):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            INSERT INTO loco
            (address, accel_curve_group_id, speed_curve_group_id, base_level, light_func_id, nickname, brake_ratio)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (address)
            DO UPDATE
            SET accel_curve_group_id = excluded.accel_curve_group_id,
            speed_curve_group_id = excluded.speed_curve_group_id,
            base_level = excluded.base_level,
            light_func_id = excluded.light_func_id,
            nickname = excluded.nickname
            brake_ratio = excluded.brake_ratio
        ''', (address, accel_curve_group_id, speed_curve_group_id, base_level, light_func_id, nickname, brake_ratio))
        con.commit()
        con.close()
        
    @classmethod
    def updateLoco(self, loco_id, address, accel_curve_group_id, speed_curve_group_id, base_level, light_func_id, nickname, brake_ratio):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            UPDATE loco
            SET address = ?,
            accel_curve_group_id = ?,
            speed_curve_group_id = ?,
            base_level = ?,
            light_func_id = ?,
            nickname = ?,
            brake_ratio = ?
            WHERE loco_id = ?
        ''', (address, accel_curve_group_id, speed_curve_group_id, base_level, light_func_id, nickname, brake_ratio, loco_id))
        con.commit()
        con.close()
        
    # {1: [{curve_group_id: 1, speed: ...の形式
    @classmethod
    def getAllSpeedAccelCurve(self):
        con = sqlite3.connect(self.dbfile)
        con.row_factory = self.dict_factory
        cur = con.cursor()
        cur.execute('''
            SELECT curve_group_id, speed, accel
            FROM speed_accel_curve
            ORDER BY speed ASC
        ''', ())
    
        results = cur.fetchall()
        curve_groups = {}
        for result in results:
            if result['curve_group_id'] in curve_groups:
                curve_groups[result['curve_group_id']].append(result)
            else:
                curve_groups[result['curve_group_id']] = [result, ]
                
        con.close()
        return curve_groups
    
    
    
