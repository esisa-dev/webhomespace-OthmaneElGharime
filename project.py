import os
import zipfile
import tempfile
from flask import(  
    Flask,
    request,
    render_template,
    redirect,
    session,
    url_for,

)
from werkzeug.utils import secure_filename
import spwd
import crypt

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('browse'))
    return render_template(('login.html'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if authenticate(username, password):
            session['username'] = username
            return redirect(url_for('browse'))
        else:
            error = 'Invalid credentials'
    return render_template('login.html', error=error)

def authenticate(username, password):
    try:
        user = spwd.getspnam(username)
        if user:
            return crypt.crypt(password, user.sp_pwd) == user.sp_pwd
    except KeyError:
        return False
    return False

@app.route('/logout')
def logout():
    session.pop('username', None)
    print('Logged out')
    return redirect(url_for('index'))

@app.route('/browse', defaults={'path': ''})
@app.route('/browse/<path:path>')
def browse(path):
    if 'username' not in session:
        return redirect(url_for('login'))
    base_dir = os.path.expanduser(f'~{session["username"]}')
    full_path = os.path.join(base_dir, path)
    return render_template('browse.html', path=path, content=list_directory(full_path))

def list_directory(path):
    items = []
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        items.append({
            'name': item,
            'is_file': os.path.isfile(item_path),
            'size': os.path.getsize(item_path),
            'path': item_path
        })
    return items

@app.route('/download')
def download():
    if 'username' not in session:
        return redirect(url_for('login'))

    base_dir = os.path.expanduser(f'~{session["username"]}')
    zip_filename = f'{session["username"]}_home.zip'

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_zip_path = os.path.join(temp_dir, zip_filename)
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, base_dir)
                    zipf.write(file_path, arcname)
        return send_file(temp_zip_path, as_attachment=True, attachment_filename=zip_filename)

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)