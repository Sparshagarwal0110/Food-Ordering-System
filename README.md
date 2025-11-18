# 🍕 Food Ordering System
Food Ordering System College Minor Project.

A complete web-based food ordering system built with Python Flask. Perfect for college projects and learning full-stack development.

# ✨ Features

*User Registration & Login - Secure authentication system

*Menu Browsing - View food items by categories (Pizza, Burgers, Drinks, Desserts)

*Shopping Cart - Add/remove items with quantity management

*Order Management - Place orders and track status

*Admin Panel - Manage orders and view analytics

*Responsive Design - Works on desktop and mobile

**🚀 Quick Start**

*Prerequisites
Python 3.7 or higher

pip package manager

*Installation & Run
*Install dependencies:

bash
pip install flask flask-sqlalchemy werkzeug

*Run the application:

bash
python app.py
Access the system:

Open: http://localhost:5000

Admin Login: username admin, password admin123

**📁 Project Structure**

The entire system is contained in a single Python file:

app.py - Complete Flask application with database models, routes, and templates

**👥 User Roles**

*Customer Features:
Register new account

Browse menu by categories

Add items to shopping cart

Place orders with delivery information

Track order status

*Admin Features:
View all orders

Update order status (Pending → Preparing → Ready → Delivered)

View system statistics (total orders, revenue, users)

Monitor customer activities

**🗃️ Database**

SQLite database created automatically on first run

Includes sample data: categories, menu items, and admin user

No additional setup required

**🛠️ Technology Stack**

Backend: Python Flask

Database: SQLAlchemy with SQLite

Authentication: Flask sessions with password hashing

Frontend: HTML, CSS, JavaScript (embedded in Python)

Styling: Custom CSS with responsive design

**📞 Support**

For issues or questions:

Check that all dependencies are installed

Ensure port 5000 is available

Delete restaurant.db to reset the database
