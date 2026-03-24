from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "keto_store_secret_2026"
DB_PATH = 'database.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        # User Table
        conn.execute('''CREATE TABLE IF NOT EXISTS users 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         username TEXT UNIQUE, password TEXT, role TEXT)''')
        # Product Table
        conn.execute('''CREATE TABLE IF NOT EXISTS products 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         name TEXT, price REAL)''')
        # Orders Table
        conn.execute('''CREATE TABLE IF NOT EXISTS orders 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         buyer_name TEXT, place TEXT, product_name TEXT, 
                         quantity INTEGER, total_price REAL, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Default Admin
        conn.execute("INSERT OR IGNORE INTO users (id, username, password, role) VALUES (1, 'admin', 'admin123', 'admin')")
        conn.commit()

init_db()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = sqlite3.connect(DB_PATH)
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", 
                            (request.form['username'], request.form['password'])).fetchone()
        conn.close()
        if user:
            session['user'], session['role'] = user[1], user[3]
            return redirect('/admin' if user[3] == 'admin' else '/')
        return "Invalid Credentials. Please try again."
    return render_template('login.html')

@app.route('/admin')
def admin():
    if session.get('role') != 'admin': return redirect('/login')
    conn = sqlite3.connect(DB_PATH)
    products = conn.execute("SELECT * FROM products").fetchall()
    orders = conn.execute("SELECT * FROM orders ORDER BY date DESC").fetchall()
    conn.close()
    return render_template('admin.html', products=products, orders=orders)

@app.route('/add_product', methods=['POST'])
def add_product():
    if session.get('role') == 'admin':
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO products (name, price) VALUES (?, ?)", 
                         (request.form['name'], request.form['price']))
    return redirect('/admin')

@app.route('/delete/<int:id>')
def delete_product(id):
    if session.get('role') == 'admin':
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM products WHERE id=?", (id,))
    return redirect('/admin')

@app.route('/checkout', methods=['POST'])
def checkout():
    p_id = request.form.get('product_id')
    qty = int(request.form.get('quantity'))
    conn = sqlite3.connect(DB_PATH)
    product = conn.execute("SELECT name, price FROM products WHERE id=?", (p_id,)).fetchone()
    
    if product:
        total = product[1] * qty
        conn.execute("INSERT INTO orders (buyer_name, place, product_name, quantity, total_price) VALUES (?, ?, ?, ?, ?)", 
                     (request.form.get('buyer_name'), request.form.get('place'), product[0], qty, total))
        conn.commit()
    conn.close()
    return render_template('cart.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)