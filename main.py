from flask import Flask, render_template, request
import version

app = Flask(__name__)

UPLOAD_FILENAME = '/tmp/new_firmware.tar.gz2'

@app.route("/")
def menu():
    return render_template('menu.html', version=version.VERSION, menu=True)

@app.route("/upgrade", methods=['GET', 'POST'])
def upgrade():
    if request.method == 'GET':
        return render_template('upgrade.html', version=version.VERSION)
    elif request.method == 'POST':
        f = request.files['file']
        f.save('/var/www/uploads/uploaded_file.txt')
