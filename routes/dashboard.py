from flask import Flask, render_template, jsonify, session, redirect, url_for, send_file
from flask_mysqldb import MySQL
import csv
import io
from datetime import datetime
def register_dashboard_routes(app, mysql):
    @app.route('/dashboard')
    def dashboard():
        if 'loggedin' not in session:
            return redirect(url_for('login'))
        return render_template('dashboard.html')

    @app.route('/api/inventory-data')
    def inventory_data():
        if 'loggedin' not in session:
            return redirect(url_for('login'))

        cursor = mysql.connection.cursor()

        # Total Inventory Value
        cursor.execute("SELECT SUM(price * quantityInStock) FROM product")
        total_value = cursor.fetchone()[0] or 0

        # Total Items
        cursor.execute("SELECT COUNT(*) FROM product")
        total_items = cursor.fetchone()[0]

        cursor.close()

        return jsonify({
            'TotalValue': total_value,
            'TotalItems': total_items
        })

    @app.route('/api/products-per-category')
    def products_per_category():
        if 'loggedin' not in session:
            return redirect(url_for('login'))

        cursor = mysql.connection.cursor()
        query = '''
            SELECT c.categoryName, COUNT(p.productId)
            FROM categories c
            LEFT JOIN product p ON p.categoryId = c.categoryId
            GROUP BY c.categoryName
        '''
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()

        labels = [row[0] for row in results]
        values = [row[1] for row in results]

        return jsonify({'labels': labels, 'values': values})

    @app.route('/api/stock-status')
    def stock_status():
        if 'loggedin' not in session:
            return redirect(url_for('login'))

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM product WHERE quantityInStock = 0")
        out_of_stock = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM product WHERE quantityInStock < minimumStockLevel AND quantityInStock > 0")
        low_stock = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM product WHERE quantityInStock >= minimumStockLevel")
        normal_stock = cursor.fetchone()[0]

        cursor.close()

        return jsonify({
            'labels': ['Out of Stock', 'Low Stock', 'Normal Stock'],
            'values': [out_of_stock, low_stock, normal_stock]
        })

    @app.route('/export/inventory-csv')
    def export_inventory_csv():
        if 'loggedin' not in session:
            return redirect(url_for('login'))

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT productId, name, price, quantityInStock, categoryId, brandId FROM product')
        rows = cursor.fetchall()
        cursor.close()

        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(['Product ID', 'Name', 'Price', 'Quantity', 'Category ID', 'Brand ID'])

        for row in rows:
            writer.writerow(row)

        output = io.BytesIO()
        output.write(si.getvalue().encode('utf-8'))
        output.seek(0)

        filename = f"inventory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return send_file(output, mimetype='text/csv', download_name=filename, as_attachment=True)

