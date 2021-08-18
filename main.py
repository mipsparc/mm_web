from flask import Flask, render_template, request, redirect, url_for, Response, flash, Markup
import version
import os
import israspi
import pathlib
import datetime
from subprocess import Popen, run
from DB import DB
import re
import time
import pyudev
from Chart import Chart
import sys
# MultiMasconからもimportする
sys.path.append(os.path.join(os.path.dirname(__file__), '../MultiMascon/'))
from Button import Button
from DSAir2 import DSAir2
from Keyboard import Keyboard

app = Flask(__name__)
# アプライアンスのため固定鍵とする。セキュリティは必要とされない。
# 同様に、CSRFなども自由だが、現実的な攻撃を受けづらいので対策しない。
app.secret_key = b'\xda\x90\x89lh\xdb\x80\xee"$\xa1#\xc4\'\xcc\xc6\xde|\x18~\xdc\x86\x14\xa6'

if israspi.is_raspi:
    FIRMWARE_FILENAME = '/mnt/rescue/MultiMasconUpdate.img'
    DATABASE_FILENAME = '/mnt/database/multimascon.sqlite3'
    LOG_DIR = '/mnt/database/log/'

@app.route("/")
def menu():
    # データベーススキーマのバージョン
    current_version = DB.getSchemeVersion()
    if version.SCHEME_VERSION != current_version:
        flash('設定ファイルバージョンとファームウェアバージョンに差異があります。両方とも最新にしてください')

    return render_template('menu.html', version=version.VERSION)

@app.route("/loco", methods=['GET', 'POST'])
def loco():
    if request.method == 'GET':
        locos = DB.getAllLocos()
        # 新規登録用
        locos.append({'loco_id': -1, 'isnew': True})
        return render_template('loco.html', version=version.VERSION, locos=locos)
    
    elif request.method == 'POST':
        if request.form['mode'] == 'del':
            loco_id = int(request.form['loco_id'])
            if loco_id >= 0:
                DB.deleteLoco(str(loco_id))
        elif request.form['mode'] == 'save':
            loco_id = request.form['loco_id']
            if not loco_id.isdecimal():
                loco_id = -1
            else:
                loco_id = int(loco_id)
            address = int(request.form['address'])
            accel_curve_group_id = int(request.form['accel_curve_group_id'])
            speed_curve_group_id = int(request.form['speed_curve_group_id'])
            base_level = int(request.form['base_level'])
            light_func_id = int(request.form['light_func_id'])
            nickname = request.form['nickname']
            brake_ratio = float(request.form['brake_ratio'])
            
            # 条件はしっかり
            if address > 0 and accel_curve_group_id > 0 and speed_curve_group_id > 0 \
                and base_level >= 0 and light_func_id >= 0 and brake_ratio > 0 and len(nickname) > 0:
                if loco_id < 0:
                    DB.insertLoco(str(address), str(accel_curve_group_id), str(speed_curve_group_id), str(base_level), str(light_func_id), nickname, str(brake_ratio))
                else:
                    DB.updateLoco(str(loco_id), str(address), str(accel_curve_group_id), str(speed_curve_group_id), str(base_level), str(light_func_id), nickname, str(brake_ratio))
                
        return redirect(url_for('loco'))

@app.route("/mascon", methods=['GET', 'POST'])
def mascon():
    if request.method == 'GET':
        # 現在接続されているポートの一覧
        ports = []
        context = pyudev.Context()
        for device in context.list_devices():
            if '/usb' in device.sys_path:
                # 物理接続位置を取得する
                # 例: 
                # - 1(1番ポートに接続)
                # - 2/1(2番ポートに接続されたハブの1番ポートに接続)
                path = device.sys_path.split("/usb")[1]
                path = path.split(":")[0]
                path = path.split("/")[-1]
                path = path.replace("-", "/")
                path = path.replace(".", "/")
                path = path[4:]
                if path == '':
                    continue
                ports.append(path)
    
        mascon_assigns = DB.getAllMasconPos()
        # 新規登録用
        mascon_assigns.append({'id': -1, 'isnew': True})
        
        nicknames = DB.getAllNicknames()
        return render_template('mascon.html', version=version.VERSION, mascons=mascon_assigns, nicknames=nicknames, ports=list(set(ports)))
    
    elif request.method == 'POST':
        if request.form['mode'] == 'del':
            mascon_assign_id = int(request.form['mascon_assign_id'])
            if mascon_assign_id > 0:
                DB.deleteMasconPos(str(mascon_assign_id))
        elif request.form['mode'] == 'save':
            mascon_assign_id = int(request.form['mascon_assign_id'])
            loco_id = int(request.form['loco_id'])
            mascon_pos = request.form['mascon_pos']
            p = re.compile('([0-9]+/?){1,8}')
            if loco_id > 0 and p.fullmatch(mascon_pos) is not None:
                if mascon_assign_id < 0:
                    DB.upsertMasconPos(str(loco_id), mascon_pos)
                # すでにレコードがある場合は、それを上書きする
                # TODO このコードいるのか?
                elif DB.isMasconAssignIdExist(str(mascon_assign_id)) is not None:
                    DB.updateMasconPos(str(mascon_assign_id), str(loco_id), mascon_pos)
                
        return redirect(url_for('mascon'))

@app.route("/button", methods=['GET', 'POST'])
def button():
    if request.method == 'GET':
        buttons = DB.getAllButtons()
        
        # 新規登録用
        buttons.append({'button_assign_id': -1, 'isnew': True, 'assign_types':{-1: '選択してください'}})
        return render_template('button.html', version=version.VERSION, buttons=buttons, button_types=Button.BUTTONS, assign_types=Button.ASSIGN_TYPES)
    
    elif request.method == 'POST':
        if request.form['mode'] == 'del':
            assign_id = int(request.form['button_assign_id'])
            if assign_id >= 0:
                DB.deleteButton(str(assign_id))
        elif request.form['mode'] == 'save':
            assign_id = int(request.form['button_assign_id'])
            mascon_pos = request.form['mascon_pos']
            button_id = int(request.form['button_id'])
            assign_type = int(request.form['assign_type'])
            send_key = int(request.form['send_key'])
            
            p = re.compile('([0-9]+/?){1,8}')
            if p.fullmatch(mascon_pos) is not None and button_id in Button.BUTTONS.keys() \
                and assign_type in Button.ASSIGN_TYPES.keys() and send_key >= 0:
                if assign_id < 0:
                    DB.upsertButton(str(mascon_pos), str(button_id), str(assign_type), str(send_key))
                else:
                    DB.updateButton(str(assign_id), str(mascon_pos), str(button_id), str(assign_type), str(send_key))
                
        return redirect(url_for('button'))

@app.route("/keyboard", methods=['GET', 'POST'])
def keyboard():
    if request.method == 'GET':
        # デフォルト値を設定
        loco_keyboards = {}
        for scan_key in Keyboard.SCAN_CODES_LOCO:
            loco_keyboards[scan_key] = {'keyboard_assign_id': -1, 'key_code': scan_key, 'num': ''}
        loco_keyboards.update(DB.getKeyboards(str(Keyboard.ASSIGN_TYPE_LOCO), ''))
        loco_keyboards = list(loco_keyboards.values())
        
        normal_keyboards = DB.getKeyboards(str(Keyboard.ASSIGN_TYPE_FUNC), str(Keyboard.ASSIGN_TYPE_ACCESSORY))
        normal_keyboards[999] = {'keyboard_assign_id': -1, 'isnew': True}

        return render_template('keyboard.html', version=version.VERSION, loco_keyboards=loco_keyboards, normal_keyboards=normal_keyboards, loco_key=Keyboard.SCAN_CODES_LOCO, normal_key=Keyboard.SCAN_CODES_NORMAL)
    
    elif request.method == 'POST':
        if request.form['mode'] == 'del':
            assign_id = int(request.form['keyboard_assign_id'])
            DB.deleteKeyboard(str(assign_id))
        elif request.form['mode'] == 'save':
            assign_id = int(request.form['keyboard_assign_id'])
            key_code = int(request.form['key_code'])
            assign_type = ''
            if request.form['type'] == 'loco_key':
                assign_type = Keyboard.ASSIGN_TYPE_LOCO
                # DCCアドレス
                num = int(request.form['loco_addr'])
            else:
                # ファンクションID / アクセサリアドレス
                num = int(request.form['num'])
                
                if request.form['type'] == 'func':
                    assign_type = Keyboard.ASSIGN_TYPE_FUNC
                elif request.form['type'] == 'accessory':
                    assign_type = Keyboard.ASSIGN_TYPE_ACCESSORY
            
            if assign_type != '' and num >= 0 \
                and (key_code in Keyboard.SCAN_CODES_LOCO or key_code in Keyboard.SCAN_CODES_NORMAL):
                if assign_id < 0:
                    DB.upsertKeyboard(str(assign_type), str(key_code), str(num))
                else:
                    DB.updateKeyboard(str(assign_id), str(assign_type), str(key_code), str(num))
                
        return redirect(url_for('keyboard'))

@app.route("/accel_speed", methods=['GET', 'POST'])
def accel_speed():
    if request.method == 'GET':
        curve_groups = DB.getAllSpeedAccelCurve()
        svg = ''
        if curve_groups != {}:
            profiles = Chart.genAccelProfileFromCurveGroups(curve_groups)
            svg = Chart.createSpeedAccel(profiles)
            
            # 新規登録用
            for k in curve_groups.keys():
                curve_groups[k].append({'curve_group_id': curve_groups[k][0]['curve_group_id'], 'curve_id': -1, 'isnew': True})
        return render_template('accel_speed.html', version=version.VERSION, chart_img=svg, curve_groups=curve_groups)
    elif request.method == 'POST':
        if request.form['mode'] == 'del':
            curve_id = int(request.form['curve_id'])
            if curve_id > 0:
                DB.deleteAccelSpeed(str(curve_id))
        elif request.form['mode'] == 'save':
            curve_group_id = int(request.form['curve_group_id'])
            curve_id = int(request.form['curve_id'])
            speed = int(request.form['speed'])
            accel = float(request.form['accel'])
            if curve_group_id > 0 and speed >= 0 and accel >= 0:
                # 新規追加
                if curve_id < 0:
                    DB.upsertAccelSpeed(str(curve_group_id), str(speed), str(accel))
                # すでにレコードがある場合は、それを上書きする
                else:
                    DB.updateAccelSpeed(str(curve_id), str(speed), str(accel))
        elif request.form['mode'] == 'delGroup':
            curve_group_id = int(request.form['curve_group_id'])
            if curve_group_id > 0:
                DB.deleteAccelSpeedGroup(str(curve_group_id))
                
        elif request.form['mode'] == 'new':
            curve_groups = DB.getAllSpeedAccelCurve()
            if curve_groups == {}:
                new_curve_group_id = 1
            else:
                new_curve_group_id = max(curve_groups.keys()) + 1
            DB.createAccelSpeedGroup(new_curve_group_id)

        return redirect(url_for('accel_speed'))
    
@app.route("/output_speed", methods=['GET', 'POST'])
def output_speed():
    if request.method == 'GET':
        curve_groups = DB.getAllSpeedOutputCurve()
        svg = ''
        if curve_groups != {}:
            profiles = Chart.genOutputProfileFromCurveGroups(curve_groups)
            svg = Chart.createSpeedOutput(profiles)
        
            # 新規登録用
            for k in curve_groups.keys():
                curve_groups[k].append({'curve_group_id': curve_groups[k][0]['curve_group_id'], 'curve_id': -1, 'isnew': True})
        return render_template('output_speed.html', version=version.VERSION, chart_img=svg, curve_groups=curve_groups)
    elif request.method == 'POST':
        if request.form['mode'] == 'del':
            curve_id = int(request.form['curve_id'])
            if curve_id > 0:
                DB.deleteOutputSpeed(str(curve_id))
        elif request.form['mode'] == 'save':
            curve_group_id = int(request.form['curve_group_id'])
            curve_id = int(request.form['curve_id'])
            speed = int(request.form['speed'])
            output = float(request.form['output'])
            if curve_group_id > 0 and speed >= 0 and output >= 0:
                # 新規追加
                if curve_id < 0:
                    DB.upsertOutputSpeed(str(curve_group_id), str(speed), str(output))
                # すでにレコードがある場合は、それを上書きする
                else:
                    DB.updateOutputSpeed(str(curve_id), str(speed), str(output))
        elif request.form['mode'] == 'delGroup':
            curve_group_id = int(request.form['curve_group_id'])
            if curve_group_id > 0:
                DB.deleteOutputSpeedGroup(str(curve_group_id))
                
        elif request.form['mode'] == 'new':
            curve_groups = DB.getAllSpeedOutputCurve()
            if curve_groups == {}:
                new_curve_group_id = 1
            else:
                new_curve_group_id = max(curve_groups.keys()) + 1
            DB.createOutputSpeedGroup(new_curve_group_id)

        return redirect(url_for('output_speed'))

@app.route("/upgrade", methods=['GET', 'POST'])
def upgrade():
    if request.method == 'GET':
        return render_template('upgrade.html', version=version.VERSION)
    elif request.method == 'POST':
        f = request.files['file']
        blob = f.read()
        if len(blob) < 100:
            return redirect(url_for('upgrade'))
        
        run('mount -t vfat -o rw /dev/mmcblk0p6 /mnt/rescue', shell=True)
        open(FIRMWARE_FILENAME, mode='wb').write(blob)
        run('umount /mnt/rescue', shell=True)
        Popen('sleep 3; reboot', shell=True)
        flash('再起動を開始しました。起動完了するまで電源ケーブルを抜かないでください')
        return redirect(url_for('upgrade_ready'))

@app.route("/upgrade_ready")
def upgrade_ready():
    return render_template('upgrade_ready.html', version=version.VERSION)

@app.route("/database", methods=['GET', 'POST'])
def database():
    if request.method == 'GET':
        return render_template('database.html', version=version.VERSION)
    elif request.method == 'POST':
        f = request.files['file']
        blob = f.read()
        if len(blob) < 100:
            return redirect(url_for('database'))
        
        run('pkill -f "/mnt/multimascon/MultiMascon/main.py"', shell=True)
        Popen('python3 /mnt/multimascon/MultiMascon/main.py', shell=True)
        flash('設定情報を更新しました')
        return redirect(url_for('database'))
    
@app.route("/database/multimascon.sqlite3")
def database_download():
    database_file = open(DATABASE_FILENAME, mode='rb').read()
    return database_file, 200, {'Content-Type': 'application/octet-stream'}

@app.route("/log")
def log():
    log = ''
    
    log_filenums = sorted([int(p.stem) for p in pathlib.Path(LOG_DIR).iterdir()], reverse=True)
    if log_filenums == []:
        log = '見つかりませんでした'
    else:
        for filenum in log_filenums:
            log += f'<br>----------{filenum}----------<br>' + open(LOG_DIR + f'{filenum}.txt').read().replace('\n', '<br>')
        
    return render_template('log.html',  version=version.VERSION, log=Markup(log))

@app.route("/power", methods=['GET', 'POST'])
def power():
    if request.method == 'GET':
        return render_template('power.html', version=version.VERSION)
    elif request.method == 'POST':
        if request.form['power'] == 'shutdown':
            Popen('sleep 3; shutdown -h now', shell=True)
        elif request.form['power'] == 'reboot':
            Popen('sleep 3; reboot', shell=True)
        else:
            return redirect(url_for('power'))
        
        flash('終了手順が開始しました。シャットダウンの場合は、ランプが消灯してから10秒経つまでケーブルを抜かないでください')
        return redirect(url_for('power'))
    
@app.route("/psk", methods=['GET', 'POST'])
def psk():
    if request.method == 'GET':
        return render_template('psk.html', version=version.VERSION)
    elif request.method == 'POST':
        new_psk = request.form['psk']
        p = re.compile('[a-zA-Z0-9]{8,62}')
        if p.fullmatch(new_psk) is None:
            flash('パスワードが不正です。変更が反映されませんでした')
        else:
            run(f'sed -i -e "s/^wpa_passphrase=.*/wpa_passphrase={new_psk}/" /mnt/database/hostapd.conf', shell=True)
            flash('変更が完了しました。再起動後に反映されます。')

        return redirect(url_for('psk'))
    
@app.route("/softreset", methods=['GET', 'POST'])
def softreset():
    if request.method == 'GET':
        return render_template('softreset.html', version=version.VERSION)
    elif request.method == 'POST':
        run('pkill -f "/mnt/multimascon/MultiMascon/main.py"', shell=True)
        Popen('python3 /mnt/multimascon/MultiMascon/main.py', shell=True)
        flash('ソフトリセットが完了しました')

        return redirect(url_for('softreset'))
    
@app.route("/cv", methods=['GET', 'POST'])
def cv():
    if request.method == 'GET':
        cv_number = request.args.get('cv_number') or ''
        result_text = request.args.get('result_text') or ''
        
        try:
            cv_number = int(cv_number)
        except:
            cv_number = ''
        return render_template('cv.html', cv_number=cv_number, result_text=result_text, version=version.VERSION)
    
    elif request.method == 'POST':
        mode = request.form['mode']
        cv_number = request.form['cv_number']
        try:
            cv_number = int(cv_number)
            if cv_number < 0 or 1023 < cv_number:
                raise ValueError
        except:
            flash('CV番号が不正です')
            return redirect(url_for('cv'))
        
        if mode != 'read' and mode != 'write':
            return redirect(url_for('cv'))
        
        if mode == 'write':
            cv_value = request.form['cv_value']
            try:
                cv_value = int(cv_value)
                if cv_value < 0 or 255 < cv_value:
                    raise ValueError
            except:
                flash('CV値が不正です')
                return redirect(url_for('cv', cv_number=cv_number))
        
        run('pkill -f "/mnt/multimascon/MultiMascon/main.py"', shell=True)
        time.sleep(1)

        try:
            dsair = DSAir2('/dev/ttyUSB0', None)
        except:
            flash('DSAir2との接続に失敗しました')
            return redirect(url_for('cv', cv_number=cv_number))
        
        max_wait_time = time.time() + 7
        if mode == 'read':
            dsair.send(f'getLocoConfig(49152,{cv_number})')
            read_value = ''
            while time.time() < max_wait_time:
                read_value = dsair.read().decode('ascii')
                if read_value.startswith('@CV,'):
                    break
            if read_value == '':
                flash('CV値読み込みに失敗しました')
                return redirect(url_for('cv', cv_number=cv_number))
            else:
                read_cv_result = read_value.split(',')
                if len(read_cv_result) <= 3 or (not read_cv_result[3].isdecimal()):
                    flash('CV値読み込みに失敗しました')
                    return redirect(url_for('cv', cv_number=cv_number))
                read_cv_value = read_cv_result[3]
                return redirect(url_for('cv', cv_number=cv_number, result_text=f'読み出し成功 CV{cv_number}: {read_cv_value}'))

        else:
            dsair.send(f'setLocoConfig(49152,{cv_number},{cv_value})')
            time.sleep(3)
            return redirect(url_for('cv', cv_number=cv_number, result_text=f'CV{cv_number}: {cv_value} を書き込みました(検証はしていません)'))
