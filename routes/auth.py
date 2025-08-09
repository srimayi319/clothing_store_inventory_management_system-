from flask import request, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
import MySQLdb.cursors
def register_auth_routes(app, mysql):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            account = cursor.fetchone()

            if account and check_password_hash(account['hashedPassword'], password):
                session['loggedin'] = True
                session['userId'] = account['id']
                session['username'] = account['username']
                session['role'] = account['role']

                cursor.execute('UPDATE users SET lastLogin = NOW() WHERE id = %s', (account['id'],))
                mysql.connection.commit()
                cursor.close()

                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect username or password!', 'danger')
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            if 'loggedin' not in session:
                username = request.form['username']
                password = request.form['password']
                hashedPassword = generate_password_hash(password)
                role = 'user'  # default role

                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
                existing_user = cursor.fetchone()

                if existing_user:
                    flash('Username already exists.', 'warning')
                else:
                    cursor.execute(
                        'INSERT INTO users (username, hashedPassword, role) VALUES (%s, %s, %s)',
                        (username, hashedPassword, role)
                    )
                    mysql.connection.commit()
                    cursor.close()

                    session['loggedin'] = True
                    session['username'] = username
                    session['role'] = role

                    flash('Registration successful!', 'success')
                    return redirect(url_for('dashboard'))
        return render_template('register.html')