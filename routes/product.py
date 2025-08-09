from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors

def register_product_routes(app, mysql):

    # Add product
    @app.route('/addProduct', methods=['POST'])
    def addProduct():
        if 'loggedin' in session and session.get('role') == 'admin':
            name = request.form['name']
            quantityInStock = int(request.form['quantityInStock'])
            price = float(request.form['price'])
            categoryId = request.form['categoryId']
            brandId = request.form['brandId']
            size = request.form['size']
            color = request.form['color']
            material = request.form['material']
            description = request.form['description']
            maximumStockLevel = request.form['maximumStockLevel']
            minimumStockLevel = request.form['minimumStockLevel']

            cursor = mysql.connection.cursor()
            cursor.execute('''
                INSERT INTO product 
                (name, quantityInStock, price, categoryId, brandId, size, color, material, description, maximumStockLevel, minimumStockLevel)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (name, quantityInStock, price, categoryId, brandId, size, color, material, description, maximumStockLevel, minimumStockLevel))

            mysql.connection.commit()
            cursor.close()

            flash('Product added successfully!', 'success')
            return redirect(url_for('viewItems'))
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('viewItems'))

    # View products (with filters)
    @app.route('/viewItems', methods=['GET'])
    def viewItems():
        if 'loggedin' in session:
            search = request.args.get('search', '')
            category = request.args.get('categories', '')
            stock = request.args.get('stock', '')

            query = "SELECT * FROM product WHERE 1=1"
            values = []

            if search:
                query += " AND name LIKE %s"
                values.append(f"%{search}%")

            if category:
                query += " AND categoryId = %s"
                values.append(category)

            if stock == 'low':
                query += " AND quantityInStock < minimumStockLevel"
            elif stock == 'out':
                query += " AND quantityInStock = 0"

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(query, tuple(values))
            products = cursor.fetchall()
            cursor.close()
            return render_template('view_items.html', products=products)
        return redirect(url_for('login'))
            

    # Update stock
    @app.route('/updateStock', methods=['POST'])
    def updateStock():
        if 'loggedin' in session and session.get('role') == 'admin':
            productId = request.form['productId']
            restockQuantity = int(request.form['restockQuantity'])

            cursor = mysql.connection.cursor()
            cursor.execute('''
                UPDATE product SET quantityInStock = quantityInStock + %s
                WHERE productId = %s
            ''', (restockQuantity, productId))

            # Remove alert if stock is now above minimum
            cursor.execute('DELETE FROM low_stock_alerts WHERE productId = %s', (productId,))

            mysql.connection.commit()
            cursor.close()

            flash('Stock updated successfully!', 'success')
            return redirect(url_for('viewItems'))
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('viewItems'))

    # Low stock alert page
    @app.route('/lowStockAlerts')
    def lowStockAlerts():
        if 'loggedin' in session:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('''
                SELECT p.productId, p.name, p.quantityInStock, l.alertDate
                FROM low_stock_alerts l
                JOIN product p ON l.productId = p.productId
                ORDER BY l.alertDate DESC
            ''')
            alerts = cursor.fetchall()
            cursor.close()
            return render_template('low_stock_alerts.html', alerts=alerts)
        return redirect(url_for('login'))

    # Delete product
    @app.route('/deleteProduct/<int:productId>', methods=['POST'])
    def deleteProduct(productId):
        if 'loggedin' in session and session.get('role') == 'admin':
            cursor = mysql.connection.cursor()
            cursor.execute('DELETE FROM product WHERE productId = %s', (productId,))
            mysql.connection.commit()
            cursor.close()
            flash('Product deleted.', 'success')
            return redirect(url_for('viewItems'))
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('viewItems'))
