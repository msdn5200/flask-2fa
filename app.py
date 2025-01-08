import pyotp
import sqlite3
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet

app = Flask(__name__)
app.secret_key = "your_secret_key"

# 固定加密密钥
encryption_key = b'bxspYn9Y8PCnxoJrs_1wX4JW0SkhS1aVv4ByOz1AOUk='
cipher = Fernet(encryption_key)


# 初始化数据库
def init_db():
    conn = sqlite3.connect('2fa.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, username TEXT UNIQUE, secret BLOB
    )''')
    conn.commit()
    conn.close()


# 用户页面
@app.route('/')
def index():
    return render_template('index.html')


# 获取 TOTP 验证码
@app.route('/get_totp/<username>', methods=['GET'])
def get_totp(username):
    conn = sqlite3.connect('2fa.db')
    c = conn.cursor()
    c.execute('SELECT secret FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()

    if not result:
        return jsonify({'error': 'User not found'}), 404

    encrypted_secret = result[0]
    try:
        decrypted_secret = cipher.decrypt(encrypted_secret).decode()
        totp = pyotp.TOTP(decrypted_secret)
        return jsonify({'username': username, 'totp_code': totp.now()})
    except Exception as e:
        return jsonify({'error': f'Decryption failed: {str(e)}'}), 500


# 管理员登录
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = sqlite3.connect('2fa.db')
        c = conn.cursor()
        c.execute('SELECT password FROM admins WHERE username = ?', (username,))
        result = c.fetchone()
        conn.close()

        if result and check_password_hash(result[0], password):
            session['admin'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')


# 管理员仪表盘
@app.route('/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect('2fa.db')
    c = conn.cursor()

    # 添加用户
    if request.method == 'POST' and 'username' in request.form:
        username = request.form.get('username')
        secret = request.form.get('secret') or pyotp.random_base32()
        encrypted_secret = cipher.encrypt(secret.encode())
        try:
            c.execute('INSERT INTO users (username, secret) VALUES (?, ?)', (username, encrypted_secret))
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template('dashboard.html', error="User already exists")

    # 删除用户
    if request.method == 'POST' and 'delete_users' in request.form:
        delete_ids = request.form.getlist('delete_users')
        c.executemany('DELETE FROM users WHERE id = ?', [(user_id,) for user_id in delete_ids])
        conn.commit()

    # 获取用户列表
    c.execute('SELECT id, username, secret FROM users')
    users = [
        {
            "id": row[0],
            "username": row[1],
            "secret": cipher.decrypt(row[2]).decode()
        }
        for row in c.fetchall()
    ]
    conn.close()
    return render_template('dashboard.html', users=users)


# 批量导入用户
@app.route('/import', methods=['POST'])
def import_txt():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    file = request.files['file']
    if not file:
        return "No file uploaded", 400

    conn = sqlite3.connect('2fa.db')
    c = conn.cursor()
    for line in file.readlines():
        username, secret = line.decode('utf-8').strip().split(',')
        encrypted_secret = cipher.encrypt(secret.encode())
        try:
            c.execute('INSERT INTO users (username, secret) VALUES (?, ?)', (username, encrypted_secret))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))


# 管理员登出
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


if __name__ == '__main__':
    init_db()
    conn = sqlite3.connect('2fa.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)',
              ('admin', generate_password_hash('Aass1122')))
    conn.commit()
    conn.close()
    app.run(host='0.0.0.0', port=5000, debug=True)
