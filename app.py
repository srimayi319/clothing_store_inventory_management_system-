from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import my_secrets
app = Flask(__name__)

# Configure MySQL using camelCase keys from secrets.py
app.config['MYSQL_HOST'] = my_secrets.MYSQL_HOST
app.config['MYSQL_PORT'] = my_secrets.MYSQL_PORT
app.config['MYSQL_USER'] = my_secrets.MYSQL_USER
app.config['MYSQL_PASSWORD'] = my_secrets.MYSQL_PASSWORD
app.config['MYSQL_DB'] = my_secrets.MYSQL_DB
app.secret_key = my_secrets.SECRET_KEY

mysql = MySQL(app)
from routes.product import register_product_routes
from routes.dashboard import register_dashboard_routes
from routes.auth import register_auth_routes  
from routes.order_process import register_order_process_routes  
register_product_routes(app, mysql)
register_dashboard_routes(app, mysql)
register_auth_routes(app, mysql)
register_order_process_routes(app, mysql)
@app.route('/')
def home():
    return redirect('/dashboard')
@app.route('/test')
def testConnection():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        cursor.close()
        return f"Connection successful. Result: {result[0]}"
    except Exception as e:
        return f"Connection failed. Error: {e}"

if __name__ == '__main__':
    app.run(debug=True)