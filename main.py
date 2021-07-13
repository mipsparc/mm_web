from flask import Flask, render_template, request, redirect, url_for, Response, flash, Markup
import version
import os
import israspi
import pathlib
import datetime
from subprocess import Popen
import DB
import re
import time

app = Flask(__name__)
# アプライアンスのため固定鍵とする。セキュリティは必要とされない。
# 同様に、CSRFなども自由だが、現実的な攻撃を受けづらいので対策しない。
app.secret_key = b'\xda\x90\x89lh\xdb\x80\xee"$\xa1#\xc4\'\xcc\xc6\xde|\x18~\xdc\x86\x14\xa6'

if israspi.is_raspi:
    FIRMWARE_FILENAME = '/mnt/rescue/new_firmware.tar.bz2'
    DATABASE_FILENAME = '/mnt/database/multimascon.sqlite3'
    LOG_DIR = '/mnt/database/log/'
else:
    FIRMWARE_FILENAME = '/tmp/new_firmware.tar.bz2'
    # ホームディレクトリにsymlinkを置く
    from pathlib import Path
    DATABASE_FILENAME = str(Path.home()) + '/multimascon.sqlite3'
    LOG_DIR = './MultiMascon/log/'

@app.route("/")
def menu():
    return render_template('menu.html', version=version.VERSION, menu=True)

@app.route("/upgrade", methods=['GET', 'POST'])
def upgrade():
    if request.method == 'GET':
        return render_template('upgrade.html', version=version.VERSION)
    elif request.method == 'POST':
        f = request.files['file']
        blob = f.read()
        if len(blob) < 100:
            return redirect(url_for('upgrade'))
        
        open(FIRMWARE_FILENAME, mode='wb').write(blob)
        Popen('sleep 5; reboot', shell=True)
        flash('再起動を開始しました。起動完了するまでケーブルを抜かないでください')
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
        
        open(DATABASE_FILENAME, mode='wb').write(blob)
        flash('設定情報復元が完了しました')
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
            Popen('sleep 5; shutdown -h now', shell=True)
        elif request.form['power'] == 'reboot':
            Popen('sleep 5; reboot', shell=True)
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
            Popen(f'sed -i -e "s/^wpa_passphrase=.*/wpa_passphrase={new_psk}/" /mnt/database/hostapd.conf', shell=True)
            flash('変更が完了しました。再起動(設定画面からも可能)後に反映されます。')

        return redirect(url_for('psk'))
    
@app.route("/softreset", methods=['GET', 'POST'])
def softreset():
    if request.method == 'GET':
        return render_template('softreset.html', version=version.VERSION)
    elif request.method == 'POST':
        #with open('/tmp/webui_namedpipe', 'w') as fifo:
            #fifo.write('softreset\n')
        Popen('pkill -9 -f "/mnt/multimascon/MultiMascon/main.py"', shell=True)
        time.sleep(0.5)
        Popen('python3 /mnt/multimascon/MultiMascon/main.py', shell=True)
        flash('ソフトリセットが完了しました')

        return redirect(url_for('softreset'))
