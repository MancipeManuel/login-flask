from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import bcrypt
import re
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Cambia esto a una clave secreta más segura

# Configuración de la base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'dataflas'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Carpeta para subir fotos de perfil

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
                    return redirect(url_for('home'))
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
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form and 'foto' in request.files:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        foto = request.files['foto']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM cuenta WHERE nombreUsuario = %s', (username,))
        account = cursor.fetchone()
        
        if account:
            msg = 'ESTA CUENTA YA EXISTE'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'EMAIL INCORRECTO !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'CARACTERES INVALIDOS'
        elif not username or not password or not email or not foto:
            msg = 'DIGITE INFORMACION EN EL CAMPO REQUERIDO'
        else:
            try:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                foto_filename = os.path.join(app.config['UPLOAD_FOLDER'], foto.filename)
                foto.save(foto_filename)
                cursor.execute('INSERT INTO cuenta (nombreUsuario, contraseña, email, foto) VALUES (%s, %s, %s, %s)', (username, hashed_password.decode('utf-8'), email, foto_filename))
                mysql.connection.commit()
                msg = 'SE HA REGISTRADO CORRECTAMENTE'
            except Exception as e:
                msg = f'Error al registrar la cuenta: {e}'
    elif request.method == 'POST':
        msg = 'DIGITE INFORMACION EN EL CAMPO REQUERIDO'
    
    return render_template('register.html', msg=msg)

@app.route('/home')
def home():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM cuenta WHERE id = %s', (session['id'],))
        account = cursor.fetchone()

        foto_url = url_for('static', filename='uploads/' + account['foto']) if account['foto'] else url_for('static', filename='default.png')
        
        return render_template('home.html', account=account, foto_url=foto_url)
    return redirect(url_for('login'))

@app.route('/update', methods=['GET', 'POST'])
def update():
    if 'loggedin' in session:
        msg = ''
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM cuenta WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        
        if request.method == 'POST' and 'username' in request.form and 'email' in request.form:
            username = request.form['username']
            email = request.form['email']
            foto = request.files['foto'] if 'foto' in request.files else None
            
            try:
                if foto:
                    foto_filename = os.path.join(app.config['UPLOAD_FOLDER'], foto.filename)
                    foto.save(foto_filename)
                    cursor.execute('UPDATE cuenta SET nombreUsuario = %s, email = %s, foto = %s WHERE id = %s', (username, email, foto.filename, session['id']))
                else:
                    cursor.execute('UPDATE cuenta SET nombreUsuario = %s, email = %s WHERE id = %s', (username, email, session['id']))
                
                mysql.connection.commit()
                msg = 'Cuenta actualizada correctamente'
                return redirect(url_for('home'))
            except Exception as e:
                msg = f'Error al actualizar la cuenta: {e}'
        
        # Pasar la URL de la foto al template
        foto_url = url_for('static', filename='uploads/' + account['foto']) if account['foto'] else url_for('static', filename='/default.png')
        
        return render_template('update.html', account=account, msg=msg, foto_url=foto_url)
    return redirect(url_for('login'))

@app.route('/delete', methods=['POST'])
def delete():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cursor.execute('DELETE FROM cuenta WHERE id = %s', (session['id'],))
            mysql.connection.commit()
            session.pop('loggedin', None)
            session.pop('id', None)
            session.pop('username', None)
            flash('Cuenta eliminada correctamente')
        except Exception as e:
            flash(f'Error al eliminar la cuenta: {e}')
        return redirect(url_for('register'))
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
