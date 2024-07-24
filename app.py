from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import bcrypt
import re

app = Flask(__name__)
# Seguridad
app.secret_key = 'your_secret_key'  # Cambia esto a una clave secreta más segura

# Configuración de la base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'dataflas'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Inicializar MySQL
mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ""
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            sql = 'SELECT * FROM cuenta WHERE nombreUsuario = %s'
            cursor.execute(sql, (username,))
            account = cursor.fetchone()
            
            if account:
                hash_almacenado = account['contraseña'].encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), hash_almacenado):
                    session['loggedin'] = True
                    session['id'] = account['id']
                    session['username'] = account['nombreUsuario']
                    msg = 'Logged in successfully!'
                    return render_template('home.html', msg=msg)
                else:
                    msg = 'Incorrect username/password!'
            else:
                msg = 'Incorrect username/password!'
        except Exception as e:
            msg = f'Error connecting to the database: {e}'
    
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM cuenta WHERE nombreUsuario = %s', (username,))
        account = cursor.fetchone()
        
        if account:
            msg = 'ESTA CUENTA YA EXISTE'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'EMAIL INCORRECTO !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'CARACTERES INVALIDOS'
        elif not username or not password or not email:
            msg = 'DIGITE INFORMACION EN EL CAMPO REQUERIDO'
        else:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('INSERT INTO cuenta ( nombreUsuario, contraseña, email) VALUES (%s, %s, %s)', (username, hashed_password.decode('utf-8'), email))
            mysql.connection.commit()
            msg = 'SE HA REGISTRADO CORRECTAMENTE'
    elif request.method == 'POST':
        msg = 'DIGITE INFORMACION EN EL CAMPO REQUERIDO'
    
    return render_template('register.html', msg=msg)

if __name__ == "__main__":
    app.run(debug=True)
