from flask import jsonify, request
from datetime import datetime
from flask_mysqldb import MySQL
import MySQLdb.cursors
def register_order_process_routes(app, mysql):
    @app.route('/process_order', methods=['POST'])
    def process_order():
        conn = mysql.connection
        cursor = conn.cursor()

        try:
            data = request.get_json()
            customerId = data['customerId']
            items = data['items']  # List of {productId, quantity}

            # Step 1: Calculate total
            totalAmount = 0
            for item in items:
                cursor.execute("SELECT price, quantityInStock FROM product WHERE productId = %s", (item['productId'],))
                product = cursor.fetchone()

                if not product:
                    return jsonify({"error": f"Product ID {item['productId']} not found"}), 404

                price, quantityInStock = product
                if item['quantity'] > quantityInStock:
                    return jsonify({"error": f"Not enough stock for product ID {item['productId']}"}), 400

                totalAmount += price * item['quantity']

            # Step 2: Generate new orderId
            cursor.execute("SELECT orderId FROM orders ORDER BY orderId DESC LIMIT 1")
            last_order = cursor.fetchone()
            if last_order:
                last_num = int(last_order[0][3:])  # Skip 'ORD'
                new_order_id = f"ORD{last_num + 1:04d}"
            else:
                new_order_id = "ORD1001"

            # Step 3: Insert into orders table
            cursor.execute("""
                INSERT INTO orders (orderId, orderDate, totalAmount)
                VALUES (%s, %s, %s)
            """, (new_order_id, datetime.now(), totalAmount))

            # Step 4: Process each item
            for item in items:
                productId = item['productId']
                quantity = item['quantity']

                # Get current price
                cursor.execute("SELECT price FROM product WHERE productId = %s", (productId,))
                price = cursor.fetchone()[0]

                # Insert into orderItems
                cursor.execute("""
                    INSERT INTO orderItems (orderId, productId, quantity, price, customerId)
                    VALUES (%s, %s, %s, %s, %s)
                """, (new_order_id, productId, quantity, price, customerId))

                # Update product stock
                cursor.execute("""
                    UPDATE product SET quantityInStock = quantityInStock - %s
                    WHERE productId = %s
                """, (quantity, productId))

                # Check if stock is now below minimum level
                cursor.execute("""
                    SELECT quantityInStock, minimumStockLevel FROM product WHERE productId = %s
                """, (productId,))
                stock, minimum = cursor.fetchone()
                if stock < minimum:
                    cursor.execute("""
                        INSERT INTO lowStockAlerts (productId, alertDate)
                        VALUES (%s, %s)
                    """, (productId, datetime.now()))

            conn.commit()
            return jsonify({"message": "Order placed successfully", "orderId": new_order_id}), 200

        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            cursor.close()
