from flask import Flask, render_template, request, redirect, url_for, Response, flash, Markup
import version
import os
import israspi
import glob
import datetime
from subprocess import Popen

app = Flask(__name__)
# アプライアンスのため固定鍵とする。セキュリティは必要とされない。
# 同様に、CSRFなども自由だが、現実的な攻撃を受けづらいので対策しない。
app.secret_key = b'\xda\x90\x89lh\xdb\x80\xee"$\xa1#\xc4\'\xcc\xc6\xde|\x18~\xdc\x86\x14\xa6'

if israspi.is_raspi:
    FIRMWARE_FILENAME = '/mnt/rescue/new_firmware.tar.bz2'
    DATABASE_FILENAME = '/mnt/database/multimascon.sqlite3'
    LOGS = '/mnt/database/log/*.txt'
else:
    FIRMWARE_FILENAME = '/tmp/new_firmware.tar.bz2'
    # ホームディレクトリにsymlinkを置く
    from pathlib import Path
    DATABASE_FILENAME = str(Path.home()) + '/multimascon.sqlite3'
    LOGS = './MultiMascon/log/*.txt'

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
        flash('再起動を開始しました。起動完了するまで絶対にケーブルを抜かないでください')
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
        return redirect(url_for('database'))
    
@app.route("/database/multimascon.sqlite3")
def database_download():
    database_file = open(DATABASE_FILENAME, mode='rb').read()
    return database_file, 200, {'Content-Type': 'application/octet-stream'}

@app.route("/log")
def log():
    log = ''
    
    log_files = glob.glob(LOGS)
    if len(log_files) == 0:
        log = '見つかりませんでした'
    else:
        log_files.sort(reverse=True)
        for filename in log_files:
            log += open(filename).read().replace('\n', '<br>') + '<br>------------------------------------<br>'
        
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
        flash('終了手順が開始しました。シャットダウンの場合は、電源が完全に切れる(ランプが消灯する)まで絶対にケーブルを抜かないでください')
        return redirect(url_for('power'))
