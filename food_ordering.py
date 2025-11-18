from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    orders = db.relationship('Order', backref='user', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    menu_items = db.relationship('MenuItem', backref='category', lazy=True)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    image_url = db.Column(db.String(255))
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    delivery_address = db.Column(db.Text, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(15), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order_items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    menu_item = db.relationship('MenuItem', backref='order_items')

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        if Category.query.count() == 0:
            # Add sample data
            categories = [
                Category(name="Pizza", description="Delicious pizzas"),
                Category(name="Burgers", description="Juicy burgers"),
                Category(name="Drinks", description="Refreshing beverages"),
                Category(name="Desserts", description="Sweet treats")
            ]
            
            for category in categories:
                db.session.add(category)
            
            menu_items = [
                MenuItem(name="Margherita Pizza", description="Classic pizza with tomato and cheese", 
                        price=12.99, category_id=1),
                MenuItem(name="Pepperoni Pizza", description="Pizza with pepperoni", 
                        price=14.99, category_id=1),
                MenuItem(name="Cheeseburger", description="Beef patty with cheese", 
                        price=8.99, category_id=2),
                MenuItem(name="Chicken Burger", description="Grilled chicken burger", 
                        price=9.99, category_id=2),
                MenuItem(name="Coca Cola", description="500ml bottle", 
                        price=2.99, category_id=3),
                MenuItem(name="Chocolate Cake", description="Rich chocolate cake", 
                        price=5.99, category_id=4)
            ]
            
            for item in menu_items:
                db.session.add(item)
            
            admin_user = User(
                username="admin",
                email="admin@restaurant.com",
                password=generate_password_hash("admin123"),
                phone="1234567890",
                address="123 Restaurant St",
                is_admin=True
            )
            db.session.add(admin_user)
            
            db.session.commit()

# Helper functions
def get_user_nav():
    if 'user_id' in session:
        cart_count = len(session.get('cart', {}))
        admin_link = '<a href="/admin">Admin</a>' if session.get('is_admin') else ''
        return f'''
        <a href="/cart">Cart ({cart_count})</a>
        <a href="/orders">My Orders</a>
        {admin_link}
        <a href="/logout">Logout ({session.get("username", "User")})</a>
        '''
    else:
        return '<a href="/login">Login</a><a href="/register">Register</a>'

def get_alerts():
    alerts = ""
    if '_flashes' in session:
        for category, message in session['_flashes']:
            alert_class = 'alert-success' if category == 'success' else 'alert-error'
            alerts += f'<div class="{alert_class}">{message}</div>'
        session.pop('_flashes', None)
    return alerts

def flash(message, category='success'):
    if '_flashes' not in session:
        session['_flashes'] = []
    session['_flashes'].append((category, message))

# Routes
@app.route('/')
def index():
    featured_items = MenuItem.query.filter_by(is_available=True).limit(4).all()
    
    featured_html = ""
    for item in featured_items:
        order_btn = '<a href="/login" class="btn">Login to Order</a>'
        if 'user_id' in session:
            order_btn = f'<button class="btn" onclick="addToCart({item.id})">Add to Cart</button>'
        
        featured_html += f'''
        <div class="menu-item">
            <h3>{item.name}</h3>
            <p>{item.description}</p>
            <div class="price">${item.price:.2f}</div>
            {order_btn}
        </div>
        '''
    
    content = f'''
    <div class="hero">
        <h2>Welcome to Food Ordering System</h2>
        <p>Order your favorite food online!</p>
        <a href="/menu" class="btn">View Full Menu</a>
    </div>
    <h2>Featured Items</h2>
    <div class="menu-grid">
        {featured_html}
    </div>
    '''
    
    # Base template with proper CSS escaping
    base_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>%(title)s</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #f4f4f4; }
            .header { background: #ff6b6b; color: white; padding: 1rem; text-align: center; }
            .nav { background: #333; padding: 1rem; display: flex; gap: 1rem; flex-wrap: wrap; }
            .nav a { color: white; text-decoration: none; padding: 0.5rem 1rem; border-radius: 4px; }
            .nav a:hover { background: #555; }
            .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
            .menu-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; }
            .menu-item { background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .menu-item img { width: 100%%; height: 150px; object-fit: cover; border-radius: 5px; }
            .price { color: #ff6b6b; font-size: 1.2rem; font-weight: bold; margin: 0.5rem 0; }
            .btn { background: #ff6b6b; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
            .btn:hover { background: #ff5252; }
            .form-group { margin-bottom: 1rem; }
            .form-group label { display: block; margin-bottom: 0.3rem; font-weight: bold; }
            .form-group input, .form-group textarea { width: 100%%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; }
            .alert { padding: 0.8rem; margin-bottom: 1rem; border-radius: 4px; }
            .alert-success { background: #d4edda; color: #155724; }
            .alert-error { background: #f8d7da; color: #721c24; }
            .cart-item { display: flex; justify-content: space-between; align-items: center; padding: 0.8rem 0; border-bottom: 1px solid #eee; }
            .order-card { background: white; padding: 1rem; border-radius: 6px; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            .hero { text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 8px; margin-bottom: 2rem; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🍕 Food Ordering System</h1>
        </div>
        <div class="nav">
            <a href="/">Home</a>
            <a href="/menu">Menu</a>
            %(user_nav)s
        </div>
        <div class="container">
            %(alerts)s
            %(content)s
        </div>
        <script>
            setTimeout(function() { 
                var alerts = document.querySelectorAll('.alert');
                alerts.forEach(function(alert) { 
                    alert.style.display = 'none';
                });
            }, 4000);
            
            %(scripts)s
        </script>
    </body>
    </html>
    '''
    
    scripts = '''
    function addToCart(itemId) {
        fetch('/add_to_cart', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({item_id: itemId})
        }).then(function(r) { return r.json(); }).then(function(data) {
            alert(data.message);
            if(data.success) location.reload();
        });
    }
    '''
    
    return render_template_string(base_template % {
        'title': 'Home',
        'user_nav': get_user_nav(),
        'alerts': get_alerts(),
        'content': content,
        'scripts': scripts
    })

@app.route('/menu')
def menu():
    category_id = request.args.get('category_id')
    if category_id:
        items = MenuItem.query.filter_by(category_id=category_id, is_available=True).all()
    else:
        items = MenuItem.query.filter_by(is_available=True).all()
    
    categories = Category.query.all()
    
    cats_html = '<div style="margin-bottom: 1rem;"><a href="/menu" class="btn">All</a> '
    for cat in categories:
        cats_html += f'<a href="/menu?category_id={cat.id}" class="btn">{cat.name}</a> '
    cats_html += '</div>'
    
    menu_html = cats_html + '<div class="menu-grid">'
    for item in items:
        order_btn = '<a href="/login" class="btn">Login to Order</a>'
        if 'user_id' in session:
            order_btn = f'<button class="btn" onclick="addToCart({item.id})">Add to Cart</button>'
        
        menu_html += f'''
        <div class="menu-item">
            <h3>{item.name}</h3>
            <p>{item.description}</p>
            <div class="price">${item.price:.2f}</div>
            {order_btn}
        </div>
        '''
    menu_html += '</div>'
    
    base_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>%(title)s</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #f4f4f4; }
            .header { background: #ff6b6b; color: white; padding: 1rem; text-align: center; }
            .nav { background: #333; padding: 1rem; display: flex; gap: 1rem; flex-wrap: wrap; }
            .nav a { color: white; text-decoration: none; padding: 0.5rem 1rem; border-radius: 4px; }
            .nav a:hover { background: #555; }
            .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
            .menu-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; }
            .menu-item { background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .price { color: #ff6b6b; font-size: 1.2rem; font-weight: bold; margin: 0.5rem 0; }
            .btn { background: #ff6b6b; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
            .btn:hover { background: #ff5252; }
            .alert { padding: 0.8rem; margin-bottom: 1rem; border-radius: 4px; }
            .alert-success { background: #d4edda; color: #155724; }
            .alert-error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🍕 Food Ordering System</h1>
        </div>
        <div class="nav">
            <a href="/">Home</a>
            <a href="/menu">Menu</a>
            %(user_nav)s
        </div>
        <div class="container">
            %(alerts)s
            %(content)s
        </div>
        <script>
            %(scripts)s
        </script>
    </body>
    </html>
    '''
    
    scripts = '''
    function addToCart(itemId) {
        fetch('/add_to_cart', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({item_id: itemId})
        }).then(function(r) { return r.json(); }).then(function(data) {
            alert(data.message);
            if(data.success) location.reload();
        });
    }
    '''
    
    return render_template_string(base_template % {
        'title': 'Menu',
        'user_nav': get_user_nav(),
        'alerts': get_alerts(),
        'content': menu_html,
        'scripts': scripts
    })

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username exists!', 'error')
            return redirect('/register')
        
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            phone=request.form.get('phone', ''),
            address=request.form.get('address', '')
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registered! Please login.', 'success')
        return redirect('/login')
    
    content = '''
    <h2>Register</h2>
    <form method="POST" style="max-width: 400px;">
        <div class="form-group">
            <label>Username:</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Email:</label>
            <input type="email" name="email" required>
        </div>
        <div class="form-group">
            <label>Password:</label>
            <input type="password" name="password" required>
        </div>
        <div class="form-group">
            <label>Phone:</label>
            <input type="tel" name="phone">
        </div>
        <div class="form-group">
            <label>Address:</label>
            <textarea name="address"></textarea>
        </div>
        <button type="submit" class="btn">Register</button>
    </form>
    <p>Have an account? <a href="/login">Login</a></p>
    '''
    
    base_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>%(title)s</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #f4f4f4; }
            .header { background: #ff6b6b; color: white; padding: 1rem; text-align: center; }
            .nav { background: #333; padding: 1rem; display: flex; gap: 1rem; flex-wrap: wrap; }
            .nav a { color: white; text-decoration: none; padding: 0.5rem 1rem; border-radius: 4px; }
            .nav a:hover { background: #555; }
            .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
            .form-group { margin-bottom: 1rem; }
            .form-group label { display: block; margin-bottom: 0.3rem; font-weight: bold; }
            .form-group input, .form-group textarea { width: 100%%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; }
            .btn { background: #ff6b6b; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
            .btn:hover { background: #ff5252; }
            .alert { padding: 0.8rem; margin-bottom: 1rem; border-radius: 4px; }
            .alert-success { background: #d4edda; color: #155724; }
            .alert-error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🍕 Food Ordering System</h1>
        </div>
        <div class="nav">
            <a href="/">Home</a>
            <a href="/menu">Menu</a>
            %(user_nav)s
        </div>
        <div class="container">
            %(alerts)s
            %(content)s
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(base_template % {
        'title': 'Register',
        'user_nav': get_user_nav(),
        'alerts': get_alerts(),
        'content': content
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash('Login successful!', 'success')
            return redirect('/')
        else:
            flash('Invalid login!', 'error')
    
    content = '''
    <h2>Login</h2>
    <form method="POST" style="max-width: 400px;">
        <div class="form-group">
            <label>Username:</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Password:</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit" class="btn">Login</button>
    </form>
    <p>No account? <a href="/register">Register</a></p>
    '''
    
    base_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>%(title)s</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #f4f4f4; }
            .header { background: #ff6b6b; color: white; padding: 1rem; text-align: center; }
            .nav { background: #333; padding: 1rem; display: flex; gap: 1rem; flex-wrap: wrap; }
            .nav a { color: white; text-decoration: none; padding: 0.5rem 1rem; border-radius: 4px; }
            .nav a:hover { background: #555; }
            .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
            .form-group { margin-bottom: 1rem; }
            .form-group label { display: block; margin-bottom: 0.3rem; font-weight: bold; }
            .form-group input { width: 100%%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; }
            .btn { background: #ff6b6b; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; }
            .alert { padding: 0.8rem; margin-bottom: 1rem; border-radius: 4px; }
            .alert-success { background: #d4edda; color: #155724; }
            .alert-error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🍕 Food Ordering System</h1>
        </div>
        <div class="nav">
            <a href="/">Home</a>
            <a href="/menu">Menu</a>
            %(user_nav)s
        </div>
        <div class="container">
            %(alerts)s
            %(content)s
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(base_template % {
        'title': 'Login',
        'user_nav': get_user_nav(),
        'alerts': get_alerts(),
        'content': content
    })

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out!', 'success')
    return redirect('/')

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login!'})
    
    data = request.get_json()
    item_id = str(data['item_id'])
    
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    cart[item_id] = cart.get(item_id, 0) + 1
    session['cart'] = cart
    
    return jsonify({'success': True, 'message': 'Added to cart!'})

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Please login!', 'error')
        return redirect('/login')
    
    cart = session.get('cart', {})
    items = []
    total = 0
    
    for item_id, qty in cart.items():
        item = MenuItem.query.get(int(item_id))
        if item:
            item_total = item.price * qty
            total += item_total
            items.append({
                'item': item,
                'quantity': qty,
                'total': item_total
            })
    
    items_html = ""
    for cart_item in items:
        items_html += f'''
        <div class="cart-item">
            <div>
                <h4>{cart_item['item'].name}</h4>
                <p>${cart_item['item'].price} x {cart_item['quantity']}</p>
            </div>
            <div>
                <button onclick="updateCart({cart_item['item'].id}, {cart_item['quantity'] - 1})">-</button>
                <span>{cart_item['quantity']}</span>
                <button onclick="updateCart({cart_item['item'].id}, {cart_item['quantity'] + 1})">+</button>
            </div>
            <div>${cart_item['total']:.2f}</div>
        </div>
        '''
    
    summary = ""
    if items:
        summary = f'''
        <div style="text-align: center; margin-top: 1rem;">
            <h3>Total: ${total:.2f}</h3>
            <a href="/checkout" class="btn">Checkout</a>
        </div>
        '''
    else:
        items_html = "<p>Cart is empty!</p>"
    
    content = f'''
    <h2>Your Cart</h2>
    <div class="cart-items">
        {items_html}
    </div>
    {summary}
    '''
    
    base_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>%(title)s</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #f4f4f4; }
            .header { background: #ff6b6b; color: white; padding: 1rem; text-align: center; }
            .nav { background: #333; padding: 1rem; display: flex; gap: 1rem; flex-wrap: wrap; }
            .nav a { color: white; text-decoration: none; padding: 0.5rem 1rem; border-radius: 4px; }
            .nav a:hover { background: #555; }
            .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
            .cart-item { display: flex; justify-content: space-between; align-items: center; padding: 0.8rem 0; border-bottom: 1px solid #eee; }
            .btn { background: #ff6b6b; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
            .btn:hover { background: #ff5252; }
            .alert { padding: 0.8rem; margin-bottom: 1rem; border-radius: 4px; }
            .alert-success { background: #d4edda; color: #155724; }
            .alert-error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🍕 Food Ordering System</h1>
        </div>
        <div class="nav">
            <a href="/">Home</a>
            <a href="/menu">Menu</a>
            %(user_nav)s
        </div>
        <div class="container">
            %(alerts)s
            %(content)s
        </div>
        <script>
            %(scripts)s
        </script>
    </body>
    </html>
    '''
    
    scripts = '''
    function updateCart(itemId, newQty) {
        fetch('/update_cart', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({item_id: itemId, quantity: newQty})
        }).then(function(r) { return r.json(); }).then(function(data) {
            if(data.success) location.reload();
        });
    }
    '''
    
    return render_template_string(base_template % {
        'title': 'Cart',
        'user_nav': get_user_nav(),
        'alerts': get_alerts(),
        'content': content,
        'scripts': scripts
    })

@app.route('/update_cart', methods=['POST'])
def update_cart():
    data = request.get_json()
    item_id = str(data['item_id'])
    quantity = data['quantity']
    
    cart = session.get('cart', {})
    if quantity <= 0:
        cart.pop(item_id, None)
    else:
        cart[item_id] = quantity
    session['cart'] = cart
    
    return jsonify({'success': True})

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('Please login!', 'error')
        return redirect('/login')
    
    if request.method == 'POST':
        cart = session.get('cart', {})
        if not cart:
            flash('Cart is empty!', 'error')
            return redirect('/cart')
        
        total = 0
        for item_id, qty in cart.items():
            item = MenuItem.query.get(int(item_id))
            if item:
                total += item.price * qty
        
        user = User.query.get(session['user_id'])
        order = Order(
            user_id=user.id,
            total_amount=total,
            delivery_address=request.form['address'],
            customer_name=request.form['name'],
            customer_phone=request.form['phone'],
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        
        for item_id, qty in cart.items():
            item = MenuItem.query.get(int(item_id))
            if item:
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=item.id,
                    quantity=qty,
                    price=item.price
                )
                db.session.add(order_item)
        
        db.session.commit()
        session.pop('cart', None)
        flash(f'Order #{order.id} placed!', 'success')
        return redirect('/orders')
    
    user = User.query.get(session['user_id'])
    content = f'''
    <h2>Checkout</h2>
    <form method="POST" style="max-width: 500px;">
        <div class="form-group">
            <label>Name:</label>
            <input type="text" name="name" value="{user.username}" required>
        </div>
        <div class="form-group">
            <label>Phone:</label>
            <input type="tel" name="phone" value="{user.phone or ''}" required>
        </div>
        <div class="form-group">
            <label>Address:</label>
            <textarea name="address" required>{user.address or ''}</textarea>
        </div>
        <button type="submit" class="btn">Place Order</button>
    </form>
    '''
    
    base_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>%(title)s</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #f4f4f4; }
            .header { background: #ff6b6b; color: white; padding: 1rem; text-align: center; }
            .nav { background: #333; padding: 1rem; display: flex; gap: 1rem; flex-wrap: wrap; }
            .nav a { color: white; text-decoration: none; padding: 0.5rem 1rem; border-radius: 4px; }
            .nav a:hover { background: #555; }
            .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
            .form-group { margin-bottom: 1rem; }
            .form-group label { display: block; margin-bottom: 0.3rem; font-weight: bold; }
            .form-group input, .form-group textarea { width: 100%%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; }
            .btn { background: #ff6b6b; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; }
            .alert { padding: 0.8rem; margin-bottom: 1rem; border-radius: 4px; }
            .alert-success { background: #d4edda; color: #155724; }
            .alert-error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🍕 Food Ordering System</h1>
        </div>
        <div class="nav">
            <a href="/">Home</a>
            <a href="/menu">Menu</a>
            %(user_nav)s
        </div>
        <div class="container">
            %(alerts)s
            %(content)s
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(base_template % {
        'title': 'Checkout',
        'user_nav': get_user_nav(),
        'alerts': get_alerts(),
        'content': content
    })

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash('Please login!', 'error')
        return redirect('/login')
    
    if session.get('is_admin'):
        orders = Order.query.order_by(Order.created_at.desc()).all()
        title = "All Orders"
    else:
        orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.created_at.desc()).all()
        title = "My Orders"
    
    orders_html = ""
    for order in orders:
        items_html = ""
        for item in order.order_items:
            items_html += f"<li>{item.menu_item.name} x {item.quantity} - ${item.price:.2f}</li>"
        
        status_control = ""
        if session.get('is_admin'):
            status_control = f'''
            <div class="form-group">
                <label>Status:</label>
                <select onchange="updateStatus({order.id}, this.value)">
                    <option value="pending" {"selected" if order.status=="pending" else ""}>Pending</option>
                    <option value="preparing" {"selected" if order.status=="preparing" else ""}>Preparing</option>
                    <option value="ready" {"selected" if order.status=="ready" else ""}>Ready</option>
                    <option value="delivered" {"selected" if order.status=="delivered" else ""}>Delivered</option>
                </select>
            </div>
            '''
        
        orders_html += f'''
        <div class="order-card">
            <h3>Order #{order.id}</h3>
            <p><strong>Status:</strong> {order.status.title()}</p>
            <p><strong>Total:</strong> ${order.total_amount:.2f}</p>
            <p><strong>Date:</strong> {order.created_at.strftime('%Y-%m-%d %H:%M')}</p>
            <p><strong>Address:</strong> {order.delivery_address}</p>
            <ul>{items_html}</ul>
            {status_control}
        </div>
        '''
    
    if not orders_html:
        orders_html = "<p>No orders found.</p>"
    
    base_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>%(title)s</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #f4f4f4; }
            .header { background: #ff6b6b; color: white; padding: 1rem; text-align: center; }
            .nav { background: #333; padding: 1rem; display: flex; gap: 1rem; flex-wrap: wrap; }
            .nav a { color: white; text-decoration: none; padding: 0.5rem 1rem; border-radius: 4px; }
            .nav a:hover { background: #555; }
            .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
            .order-card { background: white; padding: 1rem; border-radius: 6px; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 1rem; }
            .form-group label { display: block; margin-bottom: 0.3rem; font-weight: bold; }
            .form-group select { padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; }
            .alert { padding: 0.8rem; margin-bottom: 1rem; border-radius: 4px; }
            .alert-success { background: #d4edda; color: #155724; }
            .alert-error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🍕 Food Ordering System</h1>
        </div>
        <div class="nav">
            <a href="/">Home</a>
            <a href="/menu">Menu</a>
            %(user_nav)s
        </div>
        <div class="container">
            %(alerts)s
            %(content)s
        </div>
        <script>
            %(scripts)s
        </script>
    </body>
    </html>
    '''
    
    scripts = '''
    function updateStatus(orderId, status) {
        fetch('/update_order_status', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({order_id: orderId, status: status})
        }).then(function(r) { return r.json(); }).then(function(data) {
            if(data.success) location.reload();
        });
    }
    '''
    
    return render_template_string(base_template % {
        'title': 'Orders',
        'user_nav': get_user_nav(),
        'alerts': get_alerts(),
        'content': f"<h2>{title}</h2>{orders_html}",
        'scripts': scripts
    })

@app.route('/update_order_status', methods=['POST'])
def update_order_status():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    order = Order.query.get(data['order_id'])
    if order:
        order.status = data['status']
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        flash('Access denied!', 'error')
        return redirect('/')
    
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    
    content = f'''
    <h2>Admin Dashboard</h2>
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1rem 0;">
        <div class="order-card">
            <h3>Total Orders</h3>
            <p style="font-size: 2rem;">{total_orders}</p>
        </div>
        <div class="order-card">
            <h3>Pending Orders</h3>
            <p style="font-size: 2rem;">{pending_orders}</p>
        </div>
        <div class="order-card">
            <h3>Total Revenue</h3>
            <p style="font-size: 2rem;">${total_revenue:.2f}</p>
        </div>
    </div>
    '''
    
    base_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>%(title)s</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #f4f4f4; }
            .header { background: #ff6b6b; color: white; padding: 1rem; text-align: center; }
            .nav { background: #333; padding: 1rem; display: flex; gap: 1rem; flex-wrap: wrap; }
            .nav a { color: white; text-decoration: none; padding: 0.5rem 1rem; border-radius: 4px; }
            .nav a:hover { background: #555; }
            .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
            .order-card { background: white; padding: 1rem; border-radius: 6px; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }
            .alert { padding: 0.8rem; margin-bottom: 1rem; border-radius: 4px; }
            .alert-success { background: #d4edda; color: #155724; }
            .alert-error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🍕 Food Ordering System</h1>
        </div>
        <div class="nav">
            <a href="/">Home</a>
            <a href="/menu">Menu</a>
            %(user_nav)s
        </div>
        <div class="container">
            %(alerts)s
            %(content)s
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(base_template % {
        'title': 'Admin',
        'user_nav': get_user_nav(),
        'alerts': get_alerts(),
        'content': content
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)