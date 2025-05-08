from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import my_secrets
app = Flask(__name__)

# Configure MySQL
# Use values from secrets.py
app.config['MYSQL_HOST'] = my_secrets.MYSQL_HOST
app.config['MYSQL_PORT'] = my_secrets.MYSQL_PORT
app.config['MYSQL_USER'] = my_secrets.MYSQL_USER
app.config['MYSQL_PASSWORD'] = my_secrets.MYSQL_PASSWORD
app.config['MYSQL_DB'] = my_secrets.MYSQL_DB
app.secret_key = my_secrets.SECRET_KEY
 

mysql = MySQL(app)

# Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the account exists in the database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['role'] = account['role']
            
            # Update last_login timestamp
            cursor.execute('UPDATE users SET last_login = NOW() WHERE id = %s', (account['id'],))
            mysql.connection.commit()
            cursor.close()
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        
        else:
            flash('Incorrect username or password!', 'danger')
    return render_template('login.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if 'loggedin' not in session:
            username = request.form['username']
            password = request.form['password']
            role = 'user'  # Set a default role for new users

            # Check if the username already exists in the database
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('Username already exists. Please choose a different username.', 'warning')
            else:
                # Insert the new user into the database
                cursor.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, %s)', (username, password, role))
                mysql.connection.commit()
                cursor.close()

                # Optionally, you can log in the user automatically after registration
                session['loggedin'] = True
                session['username'] = username
                session['role'] = role

                flash('Registration successful!', 'success')
                return redirect(url_for('dashboard'))
        else:
            flash('You are already logged in.', 'info')

    return render_template('register.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        # User is logged in
        return render_template('dashboard.html')
    elif 'registered' in session:
        # User is registered but not logged in
        return render_template('registered_dashboard.html')
    else:
        # User is not logged in or registered, redirect to login
        return redirect(url_for('login'))

@app.route('/api/inventory-data')
def inventory_data():
    # This route uses jsonify to send data to the client for dynamic updates
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT SUM(QuantityInStock) AS TotalItems FROM product')
        TotalItems = cursor.fetchone()['TotalItems']
        
        cursor.execute('SELECT SUM(Price * QuantityInStock) AS TotalValue FROM product')
        TotalValue = cursor.fetchone()['TotalValue']
        
        return jsonify(TotalItems=TotalItems, TotalValue=TotalValue)
    else:
        return jsonify(error='User not logged in'), 401

@app.route('/api/stock_level_data', methods=['POST'])
def stock_level_data():
    if 'loggedin' in session:
        # Fetch all items from the database
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT ProductID, Name, Price, QuantityInStock FROM product WHERE QuantityInStock < MinimumStockLevel')
        products = cursor.fetchall()

        # Close the cursor after fetching
        cursor.close()

        # Convert the products to JSON format and return as a response
        return render_template('view_items.html', products=products)
     
    else:
        return redirect(url_for('login'))

@app.route('/product_data', methods=['GET', 'POST'])
def product():
    if request.method == 'POST':
        action = request.form['action']

        if action == 'add':
            return add_item()
        elif action == 'delete':
            return delete_item()
        elif action == 'view':
            return view_items()
        else:
            flash('Invalid action requested.', 'danger')

    # Default behavior for GET request or invalid action
    return 'Please make a POST request with a valid action'

def add_item():
    if 'loggedin' in session:
        # Get item details from the form
        item_name = request.form['item_name']
        item_quantity = request.form['item_quantity']
        item_price = request.form['item_price']
        item_category = request.form['item_category']
        item_brand = request.form['item_brand']
        item_size = request.form['item_size']
        item_color = request.form['item_color']
        item_material = request.form['item_material']
        item_description = request.form['item_description']
        item_maxstocklevel = request.form['item_maxstocklevel']
        item_minstocklevel = request.form['item_minstocklevel']

        # Insert the new item into the database
        cursor = mysql.connection.cursor()
        cursor.execute('''
            INSERT INTO product 
            (Name, QuantityInStock, Price, CategoryID, BrandID, Size, Color, Material, Description, MaximumStockLevel, MinimumStockLevel) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        ''', (item_name, item_quantity, item_price, item_category, item_brand, item_size, item_color, item_material, item_description, 
              item_maxstocklevel, item_minstocklevel))
        mysql.connection.commit()

        # Close the cursor after inserting
        cursor.close()

        flash('Item added successfully!', 'success')
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

def delete_item():
    if 'loggedin' in session:
        # Get the item ID from the form
        item_id = request.form['item_id']

        # Delete the item from the database
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM product WHERE ProductID = %s', (item_id,))
        mysql.connection.commit()

        # Close the cursor after deleting
        cursor.close()

        flash('Item deleted successfully!', 'success')
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

def view_items():
    if 'loggedin' in session:
        # Fetch all items from the database
        cursor = mysql.connection.cursor()
        
        cursor.execute('SELECT * FROM product_view')
        products = cursor.fetchall()

        # Close the cursor after fetching
        cursor.close()

        return render_template('view_items.html', products=products)
    else:
        return redirect(url_for('login'))

# Add Order
@app.route('/add_order', methods=['POST'])
def add_order():
    if 'loggedin' in session:
        try:
            # Start a transaction
            cursor = mysql.connection.cursor()
            cursor.execute('START TRANSACTION')

            # Get order details from the form
            order_id = request.form['order_id']
            customer_id = request.form['customer_id']
            product_id = request.form['product_id']
            quantity = request.form['quantity']
            price = request.form['price']

            # Calculate total amount
            quantity = int(quantity)  # if quantity is an integer
            price = float(price)  # if price is a decimal value
            total_amount = quantity * price

            cursor.execute('INSERT INTO orders(orderId, total_amount) VALUES (%s, %s)', (order_id, total_amount))
            
            # Insert into orders
            cursor.execute('''
                INSERT INTO order_items (orderId, productId, quantity, price, customerId) 
                VALUES (%s, %s, %s, %s, %s)
            ''', (order_id, product_id, quantity, price, customer_id))
            
            # Update product stock
            cursor.execute('UPDATE product SET QuantityInStock = QuantityInStock - %s WHERE ProductID = %s', (quantity, product_id))

            # Commit the transaction
            mysql.connection.commit()

            cursor.close()

            flash('Order added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            # Rollback in case of error
            mysql.connection.rollback()
            cursor.close()

            flash(f"Error: {e}", 'danger')
            return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/low_stock_alerts', methods=['GET'])
def low_stock_alerts():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Execute the query to get the alert data
        cursor.execute('''
            SELECT p.ProductID,p.QuantityinStock, l.AlertDate
            FROM low_stock_alerts l
            JOIN product p ON l.ProductID = p.ProductID
            ORDER BY l.AlertDate DESC
        ''')
        
        # Fetch all results
        alerts = cursor.fetchall()
        cursor.close()
        
        print(alerts)
        return jsonify(alerts)
    else:
        return redirect(url_for('login'))
@app.route('/update_stock', methods=['POST'])
def update_stock():
    if 'loggedin' in session:
        # Get the item ID and restock quantity from the form
        item_id = request.form['item_id']
        restock_quantity = request.form['RestockQuantity']

        # Ensure the restock quantity is a valid number
        try:
            restock_quantity = int(restock_quantity)
        except ValueError:
            return "Invalid restock quantity", 400

        # Update the item in the product table
        cursor = mysql.connection.cursor()
        cursor.execute('''
            UPDATE product
            SET QuantityInStock = QuantityInStock + %s
            WHERE ProductID = %s
        ''', (restock_quantity, item_id))
        
        # Delete the corresponding low stock alert
        cursor.execute('''
            DELETE FROM low_stock_alerts
            WHERE ProductID = %s
        ''', (item_id,))
        
        # Commit the changes
        mysql.connection.commit()
        
        # Close the cursor
        cursor.close()
        flash('Item updated successfully!', 'success')
        # Redirect back to the dashboard or display a success message
        return redirect(url_for('dashboard'))
    else:
        # User is not logged in, redirect to login
        return redirect(url_for('login'))

@app.route('/test')
def test_connection():
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

