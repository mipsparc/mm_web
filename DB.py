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
    
    #
    # データベーススキーマバージョン確認
    #
    @classmethod
    def getSchemeVersion(self):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            SELECT version
            FROM scheme_version
        ''', ())
        version = int(cur.fetchone()[0])
        con.close()
        
        return version

    #
    # マスコン割付設定画面
    #

    @classmethod
    def getAllMasconPos(self):
        con = sqlite3.connect(self.dbfile)
        con.row_factory = self.dict_factory
        cur = con.cursor()
        cur.execute('''
            SELECT id, loco_id, nickname, mascon_pos
            FROM mascon_assign
            LEFT JOIN loco USING (loco_id)
            ORDER BY loco_id ASC
        ''', ())
        mascon_assigns = cur.fetchall()
        con.close()
        
        return mascon_assigns
    
    @classmethod
    def getAllNicknames(self):
        con = sqlite3.connect(self.dbfile)
        con.row_factory = self.dict_factory
        cur = con.cursor()
        cur.execute('''
            SELECT loco_id, nickname
            FROM loco
            ORDER BY loco_id ASC
        ''', ())
        nicknames = cur.fetchall()
        con.close()
        
        return nicknames
    
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
    
    #
    # 車両設定画面
    #
    
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
            nickname = excluded.nickname,
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

    #
    # 加速曲線編集画面
    #

    # {1: [{curve_group_id: 1, speed: ...の形式
    @classmethod
    def getAllSpeedAccelCurve(self):
        con = sqlite3.connect(self.dbfile)
        con.row_factory = self.dict_factory
        cur = con.cursor()
        cur.execute('''
            SELECT curve_id, curve_group_id, speed, accel
            FROM speed_accel_curve
            ORDER BY curve_group_id ASC, speed ASC
        ''', ())
    
        results = cur.fetchall()
        con.close()

        curve_groups = {}
        for result in results:
            if result['curve_group_id'] in curve_groups:
                curve_groups[result['curve_group_id']].append(result)
            else:
                curve_groups[result['curve_group_id']] = [result, ]

        return curve_groups
    
    @classmethod
    def upsertAccelSpeed(self, curve_group_id, speed, accel):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            INSERT INTO speed_accel_curve
            (curve_group_id, speed, accel)
            VALUES (?, ?, ?)
            ON CONFLICT (curve_group_id, speed)
            DO UPDATE
            SET accel = excluded.accel
        ''', (curve_group_id, speed, accel))
        con.commit()
        con.close()
    
    @classmethod
    def updateAccelSpeed(self, curve_id, speed, accel):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            UPDATE OR IGNORE speed_accel_curve
            SET speed = ?, accel = ?
            WHERE curve_id = ?
        ''', (speed, accel, curve_id))
        con.commit()
        con.close()
    
    @classmethod
    def deleteAccelSpeed(self, curve_id):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            DELETE FROM speed_accel_curve
            WHERE curve_id = ?
        ''', (curve_id, ))
        con.commit()
        con.close()

    @classmethod
    def deleteAccelSpeedGroup(self, curve_group_id):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            DELETE FROM speed_accel_curve
            WHERE curve_group_id = ?
        ''', (curve_group_id, ))
        con.commit()
        con.close()

    @classmethod
    def createAccelSpeedGroup(self, new_curve_group_id):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            INSERT INTO speed_accel_curve
            (curve_group_id, speed, accel)
            VALUES
            (?, 0, 0.3),
            (?, 100, 0.0)
        ''', (new_curve_group_id, new_curve_group_id))
        con.commit()
        con.close()
        
    #
    # 出力曲線編集画面
    #
    @classmethod
    def getAllSpeedOutputCurve(self):
        con = sqlite3.connect(self.dbfile)
        con.row_factory = self.dict_factory
        cur = con.cursor()
        cur.execute('''
            SELECT curve_id, curve_group_id, speed, output
            FROM speed_output_curve
            ORDER BY curve_group_id ASC, speed ASC
        ''', ())
    
        results = cur.fetchall()
        con.close()
        
        curve_groups = {}
        for result in results:
            if result['curve_group_id'] in curve_groups:
                curve_groups[result['curve_group_id']].append(result)
            else:
                curve_groups[result['curve_group_id']] = [result, ]

        return curve_groups
    
    @classmethod
    def upsertOutputSpeed(self, curve_group_id, speed, output):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            INSERT INTO speed_output_curve
            (curve_group_id, speed, output)
            VALUES (?, ?, ?)
            ON CONFLICT (curve_group_id, speed)
            DO UPDATE
            SET output = excluded.output
        ''', (curve_group_id, speed, output))
        con.commit()
        con.close()
    
    @classmethod
    def updateOutputSpeed(self, curve_id, speed, output):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            UPDATE OR IGNORE speed_output_curve
            SET speed = ?, output = ?
            WHERE curve_id = ?
        ''', (speed, output, curve_id))
        con.commit()
        con.close()
    
    @classmethod
    def deleteOutputSpeed(self, curve_id):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            DELETE FROM speed_output_curve
            WHERE curve_id = ?
        ''', (curve_id, ))
        con.commit()
        con.close()

    @classmethod
    def deleteOutputSpeedGroup(self, curve_group_id):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            DELETE FROM speed_output_curve
            WHERE curve_group_id = ?
        ''', (curve_group_id, ))
        con.commit()
        con.close()

    @classmethod
    def createOutputSpeedGroup(self, new_curve_group_id):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            INSERT INTO speed_output_curve
            (curve_group_id, speed, output)
            VALUES
            (?, 0, 0),
            (?, 100, 500)
        ''', (new_curve_group_id, new_curve_group_id))
        con.commit()
        con.close()
        
        
    #
    # ボタン編集画面
    #
    @classmethod
    def getAllButtons(self):
        con = sqlite3.connect(self.dbfile)
        con.row_factory = self.dict_factory
        cur = con.cursor()
        cur.execute('''
            SELECT button_assign_id, mascon_pos, button_id, assign_type, send_key
            FROM button_assign
        ''', ())
        button_profile = cur.fetchall()
        con.close()
        
        return button_profile
    
    @classmethod
    def deleteButton(self, button_assign_id):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            DELETE FROM button_assign
            WHERE button_assign_id = ?
        ''', (button_assign_id, ))
        con.commit()
        con.close()

    @classmethod
    def upsertButton(self, mascon_pos, button_id, assign_type, send_key):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            INSERT INTO button_assign
            (mascon_pos, button_id, assign_type, send_key)
            VALUES (?, ?, ?, ?)
        ''', (mascon_pos, button_id, assign_type, send_key))
        con.commit()
        con.close()
    
    @classmethod
    def updateButton(self, assign_id, mascon_pos, button_id, assign_type, send_key):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            UPDATE OR IGNORE button_assign
            SET mascon_pos = ?, button_id = ?, assign_type = ?, send_key = ?
            WHERE button_assign_id = ?
        ''', (mascon_pos, button_id, assign_type, send_key, assign_id))
        con.commit()
        con.close()

    #
    # キーボード編集画面
    #
    @classmethod
    def getKeyboards(self, assign_type1, assign_type2):
        con = sqlite3.connect(self.dbfile)
        con.row_factory = self.dict_factory
        cur = con.cursor()
        cur.execute('''
            SELECT keyboard_assign_id, assign_type, key_code, num
            FROM keyboard_assign
            WHERE assign_type = ?
            OR assign_type = ?
        ''', (assign_type1, assign_type2))
        keyboards = cur.fetchall()
        con.close()
        
        # key_codeをキーにする
        output = {}
        for keyboard in keyboards:
            output[int(keyboard['key_code'])] = keyboard
        
        return output
    
    @classmethod
    def deleteKeyboard(self, assign_id):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            DELETE FROM keyboard_assign
            WHERE keyboard_assign_id = ?
        ''', (assign_id, ))
        con.commit()
        con.close()
        
    @classmethod
    def upsertKeyboard(self, assign_type, key_code, num):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            INSERT INTO keyboard_assign
            (assign_type, key_code, num)
            VALUES (?, ?, ?)
            ON CONFLICT (key_code)
            DO UPDATE
            SET num = excluded.num
        ''', (assign_type, key_code, num))
        con.commit()
        con.close()
        
    @classmethod
    def updateKeyboard(self, assign_id, assign_type, key_code, num):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        cur.execute('''
            UPDATE OR IGNORE keyboard_assign
            SET assign_type = ?, key_code = ?, num = ?
            WHERE keyboard_assign_id = ?
        ''', (assign_type, key_code, num, assign_id))
        con.commit()
        con.close()

